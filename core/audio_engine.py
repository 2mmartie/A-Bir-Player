"""
audio_engine.py — Kayıpsız FLAC oynatma motoru.

Akış:
  1. load(path)  → soundfile ile tüm dosyayı float32 PCM array'e yükler
  2. play()      → QThread başlatır
  3. QThread     → sounddevice OutputStream callback ile ses kartına gönderir
  4. Seek        → callback içinde _seek_frame flag'i kontrol edilir

Neden tam dosya yükleme?
  - Tipik FLAC parçaları 20-60 MB, i3 5005u için problem değil
  - Seek çok daha basit ve güvenilir (sadece frame pointer güncelle)
  - Chunk-based'den kaynaklanan buffer sync sorunları yok
"""

import os
import threading
import time

import numpy as np
# import sounddevice as sd (Lazy loaded below)
import soundfile as sf
from PyQt5.QtCore import QThread, pyqtSignal


class AudioEngine(QThread):
    # Sinyal: mevcut pozisyon (saniye)
    position_changed = pyqtSignal(float)
    # Sinyal: parça bitti
    track_finished = pyqtSignal()
    # Sinyal: hata mesajı
    error_occurred = pyqtSignal(str)
    # Sinyal: durum değişimi ('playing' | 'paused' | 'stopped')
    state_changed = pyqtSignal(str)

    BLOCKSIZE = 2048   # PortAudio blok boyutu (düşük gecikme için)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lock = threading.Lock()

        # --- Audio data ---
        self._data: np.ndarray | None = None   # shape: (frames, channels)
        self._samplerate: int = 44100
        self._channels: int = 2
        self._total_frames: int = 0

        # --- Playback state ---
        self._frame: int = 0          # mevcut frame (callback tarafından güncellenir)
        self._volume: float = 0.85
        self._paused: bool = False
        self._stop_flag: bool = False
        self._seek_frame: int | None = None
        
        # --- Stem Separation ---
        self._stem_mode: bool = False
        self._stems: dict[str, np.ndarray] = {} # {vocals, drums, bass, other}
        self._stem_volumes: dict[str, float] = {"vocals": 1.0, "drums": 1.0, "bass": 1.0, "other": 1.0}
        self._stems_loading: bool = False
        
        # --- Gapless / Next Track ---
        self._next_data: np.ndarray | None = None
        self._next_samplerate: int = 44100
        self._next_total_frames: int = 0
        self._next_ready: bool = False
        self._next_path: str | None = None
        
        # --- Visualizer ---
        self._viz_levels: np.ndarray = np.zeros(32, dtype="float32")  # 32 frequency bands

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def load(self, path: str, is_preload: bool = False) -> bool:
        """Dosyayı yükle. is_preload=True ise sadece belleğe hazırlar, hemen çalmaz."""
        if not is_preload:
            self._request_stop()
        
        try:
            data, sr = sf.read(path, dtype="float32", always_2d=True)
        except Exception as e:
            if not is_preload:
                self.error_occurred.emit(f"Dosya yüklenemedi: {e}")
            return False

        with self._lock:
            if is_preload:
                self._next_data = data
                self._next_samplerate = sr
                self._next_total_frames = len(data)
                self._next_path = path
                self._next_ready = True
            else:
                self._data = data
                self._samplerate = sr
                self._channels = data.shape[1]
                self._total_frames = len(data)
                self._frame = 0
                self._seek_frame = None
                self._stop_flag = False
                self._paused = False
                self._next_ready = False # Reset preload
                
                # Look for stems
                threading.Thread(target=self._load_associated_stems, args=(path,), daemon=True).start()

        return True

    def play(self):
        """Yüklü dosyayı oynat (ya da duraklatılmışsa devam et)."""
        with self._lock:
            if self._data is None:
                return
            self._paused = False
            self._stop_flag = False

        if not self.isRunning():
            self.start()
        self.state_changed.emit("playing")

    def pause(self):
        with self._lock:
            self._paused = True
        self.state_changed.emit("paused")

    def resume(self):
        with self._lock:
            self._paused = False
        self.state_changed.emit("playing")

    def toggle_pause(self):
        with self._lock:
            self._paused = not self._paused
            state = "paused" if self._paused else "playing"
        self.state_changed.emit(state)

    def stop(self):
        self._request_stop()
        self.state_changed.emit("stopped")

    def seek(self, seconds: float):
        with self._lock:
            if self._samplerate > 0:
                frame = int(seconds * self._samplerate)
                self._seek_frame = max(0, min(frame, self._total_frames - 1))

    def set_volume(self, volume: float):
        """0.0 – 1.0 arası ses seviyesi (soft gain, bit-perfect çıkışı değiştirmez)."""
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))

    def set_stem_volumes(self, volumes: dict[str, float]):
        """Update individual volumes for each stem (0.0 - 1.0)."""
        with self._lock:
            for name, vol in volumes.items():
                if name in self._stem_volumes:
                    self._stem_volumes[name] = max(0.0, min(1.0, vol))
            self._stem_mode = len(self._stems) > 0

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def duration(self) -> float:
        with self._lock:
            if self._samplerate > 0 and self._total_frames > 0:
                return self._total_frames / self._samplerate
        return 0.0

    @property
    def position(self) -> float:
        with self._lock:
            return self._frame / self._samplerate if self._samplerate > 0 else 0.0

    @property
    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return not self._paused and not self._stop_flag

    # ------------------------------------------------------------------ #
    # QThread.run — audio loop
    # ------------------------------------------------------------------ #
    def run(self):
        import sounddevice as sd
        # sounddevice callback — audio thread'de çağrılır (GIL dışında)
        def callback(outdata: np.ndarray, frames: int, time_info, status):
            with self._lock:
                # Seek isteği var mı?
                if self._seek_frame is not None:
                    self._frame = self._seek_frame
                    self._seek_frame = None

                stop   = self._stop_flag
                paused = self._paused
                frame  = self._frame
                data   = self._data
                vol    = self._volume

            if stop or data is None:
                outdata[:] = 0
                raise sd.CallbackStop()

            if paused:
                outdata[:] = 0
                return

            remaining = len(data) - frame
            if remaining <= 0:
                # GAPLESS TRANSITION LOGIC
                with self._lock:
                    if self._next_ready and self._next_data is not None:
                        # Switch to pre-loaded track instantly
                        self._data = self._next_data
                        self._samplerate = self._next_samplerate
                        self._total_frames = self._next_total_frames
                        self._frame = 0
                        self._next_ready = False
                        
                        data = self._data
                        frame = 0
                        remaining = len(data)
                        
                        # Trigger stems load for the new track
                        if self._next_path:
                            threading.Thread(target=self._load_associated_stems, args=(self._next_path,), daemon=True).start()
                    else:
                        outdata[:] = 0
                        raise sd.CallbackStop()

            n = min(frames, remaining)
            
            use_stems = self._stem_mode and self._stems and not self._stems_loading
            
            if use_stems:
                mixed = np.zeros((n, self._channels), dtype="float32")
                for name, sdata in self._stems.items():
                    s_vol = self._stem_volumes.get(name, 1.0)
                    if s_vol > 0:
                        mixed += sdata[frame : frame + n] * s_vol
                outdata[:n] = mixed * vol
            else:
                outdata[:n] = data[frame : frame + n] * vol

            if n < frames:
                outdata[n:] = 0

            with self._lock:
                self._frame = frame + n
                # Update visualizer levels from the rendered block
                try:
                    block = outdata[:n]
                    if block.shape[1] >= 2:
                        mono = (block[:, 0] + block[:, 1]) * 0.5
                    else:
                        mono = block[:, 0]
                    # Simple FFT-based band levels
                    if len(mono) >= 64:
                        fft = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
                        band_count = 32
                        band_size = max(1, len(fft) // band_count)
                        levels = np.zeros(band_count, dtype="float32")
                        for b in range(band_count):
                            start = b * band_size
                            end = min(start + band_size, len(fft))
                            levels[b] = np.mean(fft[start:end]) if end > start else 0.0
                        # Normalize to 0-1 range
                        mx = levels.max()
                        if mx > 0:
                            levels = levels / mx
                        self._viz_levels = levels * vol
                except Exception:
                    pass

        # --- Stream oluştur ---
        with self._lock:
            sr = self._samplerate
            ch = self._channels

        try:
            with sd.OutputStream(
                samplerate=sr,
                channels=ch,
                callback=callback,
                blocksize=self.BLOCKSIZE,
                dtype="float32",
            ) as stream:
                # Pozisyon güncelleme döngüsü
                while stream.active:
                    with self._lock:
                        if self._stop_flag:
                            break
                        pos = self._frame / self._samplerate if self._samplerate else 0.0
                    self.position_changed.emit(pos)
                    time.sleep(0.1)

                # Doğal bitiş mi, yoksa stop_flag mı?
                with self._lock:
                    finished = self._frame >= self._total_frames and not self._stop_flag

            if finished:
                self.track_finished.emit()

        except sd.PortAudioError as e:
            self.error_occurred.emit(f"Ses aygıtı hatası: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Oynatma hatası: {e}")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _request_stop(self):
        with self._lock:
            self._stop_flag = True
        self.wait(2000)   # Thread bitmesini bekle

    def _load_associated_stems(self, path: str):
        """Checks for stems in a folder named '[filename]_stems'."""
        with self._lock:
            self._stems.clear()
            self._stem_mode = False
            self._stems_loading = True
        
        base_dir = os.path.dirname(path)
        file_name = os.path.basename(path).rsplit('.', 1)[0]
        stems_dir = os.path.join(base_dir, f"{file_name}_stems")
        
        if os.path.exists(stems_dir):
            stem_names = ["vocals", "drums", "bass", "other"]
            for name in stem_names:
                # Try .wav or .flac or .mp3
                for ext in [".wav", ".flac", ".mp3"]:
                    s_path = os.path.join(stems_dir, f"{name}{ext}")
                    if os.path.exists(s_path):
                        try:
                            s_data, _ = sf.read(s_path, dtype="float32", always_2d=True)
                            # Ensure length matches original data (roughly)
                            if self._data is not None:
                                if len(s_data) > len(self._data):
                                    s_data = s_data[:len(self._data)]
                                elif len(s_data) < len(self._data):
                                    pad = np.zeros((len(self._data) - len(s_data), self._channels), dtype="float32")
                                    s_data = np.vstack([s_data, pad])
                            
                            self._stems[name] = s_data
                        except Exception: pass
                        break
            
            if self._stems:
                with self._lock:
                    self._stem_mode = True
                    self._stems_loading = False
                print(f"Loaded {len(self._stems)} stems for {file_name}")
            else:
                with self._lock:
                    self._stems_loading = False
