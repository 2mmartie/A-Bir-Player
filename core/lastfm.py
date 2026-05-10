"""
lastfm.py — Last.fm Now Playing + Scrobble servisi.

Kural (Last.fm standartları):
  - Parça başladığında → update_now_playing()
  - Parçanın %50'si dinlendiyse VEYA 4 dakika geçtiyse → scrobble()
  - Scrobble için parça en az 30 saniye olmalı
"""
import json
import os
import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal

try:
    import pylast
    PYLAST_AVAILABLE = True
except ImportError:
    PYLAST_AVAILABLE = False

import sys

def _get_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

CONFIG_PATH = _get_config_path()


class LastFmService(QObject):
    scrobbled     = pyqtSignal(str, str)   # (artist, title) — başarılı scrobble
    error_signal  = pyqtSignal(str)        # hata mesajı
    status_signal = pyqtSignal(str)        # bilgi mesajı

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = None
        self._lock = threading.Lock()

        # Mevcut parça bilgisi
        self._artist = ""
        self._title  = ""
        self._album  = ""
        self._duration     = 0.0
        self._track_number = 0
        self._start_time   = 0.0
        self._scrobbled    = False
        self._scrobble_timer: threading.Timer | None = None

    # ------------------------------------------------------------------ #
    # Bağlantı
    # ------------------------------------------------------------------ #
    @property
    def is_connected(self) -> bool:
        return self._network is not None

    def connect(self, api_key: str, api_secret: str,
                username: str, password: str) -> bool:
        if not PYLAST_AVAILABLE:
            self.error_signal.emit("pylast yüklü değil: pip install pylast")
            return False
        try:
            pw_hash = pylast.md5(password)
            net = pylast.LastFMNetwork(
                api_key=api_key,
                api_secret=api_secret,
                username=username,
                password_hash=pw_hash,
            )
            # Bağlantıyı doğrula: session_key çağırmak ağ üzerinden API'ye istek atar.
            # Şifre veya API key hatalıysa burada exception fırlatır.
            _ = net.session_key
            
            with self._lock:
                self._network = net
            self.status_signal.emit(f"Last.fm: {username} olarak bağlandı ✓")
            return True
        except Exception as e:
            with self._lock:
                self._network = None
            self.error_signal.emit(f"Last.fm bağlantı hatası: {e}")
            return False

    def disconnect(self):
        with self._lock:
            self._network = None
        self._cancel_timer()

    # ------------------------------------------------------------------ #
    # Now Playing + Scrobble
    # ------------------------------------------------------------------ #
    def track_started(self, artist: str, title: str, album: str,
                      duration: float, track_number: int = 0):
        """Yeni parça başladığında çağrılır."""
        self._cancel_timer()

        with self._lock:
            self._artist       = artist
            self._title        = title
            self._album        = album
            self._duration     = duration
            self._track_number = track_number
            self._start_time   = time.time()
            self._scrobbled    = False
            net = self._network

        if not net:
            return

        # Now Playing — arka planda
        threading.Thread(
            target=self._do_now_playing,
            args=(net, artist, title, album, int(duration), track_number),
            daemon=True,
        ).start()

        # Scrobble zamanlayıcısı: min(%50, 4 dk), min 30 sn kural
        if duration >= 30:
            delay = min(duration * 0.5, 240.0)
            self._scrobble_timer = threading.Timer(delay, self._do_scrobble)
            self._scrobble_timer.daemon = True
            self._scrobble_timer.start()

    def track_stopped(self):
        """Parça durdurulduğunda / atlandığında çağrılır."""
        self._cancel_timer()

    # ------------------------------------------------------------------ #
    # İç metodlar
    # ------------------------------------------------------------------ #
    def _cancel_timer(self):
        if self._scrobble_timer:
            self._scrobble_timer.cancel()
            self._scrobble_timer = None

    def _do_now_playing(self, net, artist, title, album, duration, track_number):
        try:
            net.update_now_playing(
                artist=artist,
                title=title,
                album=album or None,
                duration=duration,
                track_number=track_number or None,
            )
        except Exception as e:
            self.error_signal.emit(f"Now Playing hatası: {e}")

    def _do_scrobble(self):
        with self._lock:
            if self._scrobbled or not self._network:
                return
            net          = self._network
            artist       = self._artist
            title        = self._title
            album        = self._album
            timestamp    = int(self._start_time)
            track_number = self._track_number
            duration     = int(self._duration)
            self._scrobbled = True

        try:
            net.scrobble(
                artist=artist,
                title=title,
                timestamp=timestamp,
                album=album or None,
                track_number=track_number or None,
                duration=duration,
            )
            self.scrobbled.emit(artist, title)
            self.status_signal.emit(f"Scrobble: {artist} — {title}")
        except Exception as e:
            self.error_signal.emit(f"Scrobble hatası: {e}")

    # ------------------------------------------------------------------ #
    # Config (JSON dosyası)
    # ------------------------------------------------------------------ #
    @staticmethod
    def load_config() -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save_config(data: dict):
        existing = LastFmService.load_config()
        existing.update(data)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
