import os
import threading
import subprocess
import sys
import shutil
import re
from PyQt5.QtCore import QThread, pyqtSignal

class AISeparator(QThread):
    """
    Handles AI stem separation in the background using Demucs.
    Purely local for maximum quality and zero-config.
    """
    finished = pyqtSignal(str, bool) # path, success
    progress = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        self._run_local()

    def _run_local(self):
        try:
            self.progress.emit("Lokal AI Modeli Hazırlanıyor...")
            
            base_dir = os.path.dirname(self.file_path)
            file_name = os.path.basename(self.file_path).rsplit('.', 1)[0]
            output_dir = os.path.join(base_dir, f"{file_name}_stems")
            
            if os.path.exists(output_dir):
                self.finished.emit(self.file_path, True)
                return

            # 1. Check for FFmpeg (required by demucs)
            ffmpeg_path = shutil.which("ffmpeg")
            local_bin = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bin")
            local_ffmpeg = os.path.join(local_bin, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
            
            if not ffmpeg_path:
                if os.path.exists(local_ffmpeg):
                    ffmpeg_path = local_ffmpeg
                else:
                    msg = "Hata: 'ffmpeg' bulunamadı! Lütfen FFmpeg'in kurulu olduğundan veya 'bin' klasöründe olduğundan emin olun."
                    print(f"[AI] {msg}")
                    self.progress.emit(msg)
                    self.finished.emit(self.file_path, False)
                    return

            # Add local bin and models to environment
            env = os.environ.copy()
            if os.path.exists(local_bin):
                env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
            
            # Point Torch to our local models
            local_models = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
            if os.path.exists(local_models):
                env["TORCH_HOME"] = local_models

            try:
                import demucs
                import soundfile
            except ImportError:
                if getattr(sys, 'frozen', False):
                    msg = "Hata: AI bileşenleri pakete dahil edilememiş. Lütfen teknik destek ile iletişime geçin."
                else:
                    msg = "Gerekli AI bileşenleri (demucs, soundfile) eksik. Kuruluyor..."
                    print(f"[AI] {msg}")
                    self.progress.emit(msg)
                    
                    try:
                        # Uninstall torchcodec if it was installed (it's causing issues on Win/Py3.14)
                        subprocess.call([sys.executable, "-m", "pip", "uninstall", "-y", "torchcodec"], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        # Install demucs and stable soundfile backend
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "demucs", "soundfile"], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                        msg = "Kütüphaneler optimize edildi! İşlem devam ediyor..."
                    except Exception as e:
                        msg = f"Otomatik kurulum başarısız oldu: {str(e)}"
                
                print(f"[AI] {msg}")
                self.progress.emit(msg)
                if "Hata" in msg:
                    self.finished.emit(self.file_path, False)
                    return

            self.progress.emit("Lokal Ayrıştırma Başladı (Demucs Fixer kullanılıyor)...")
            
            fixer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "demucs_fixer.py")
            
            # Inline fallback: monkey-patch torchaudio.save before running demucs
            inline_fixer = (
                "import torch, torchaudio, soundfile as sf, numpy as np, os; "
                "def _sf_save(uri,src,sample_rate,channels_first=True,**kw):\n"
                "  w=src.detach().cpu(); w=w.t() if channels_first and w.dim()==2 else w; w=w.numpy();\n"
                "  ext=os.path.splitext(str(uri))[1].lower();\n"
                "  fmt,sub=('WAV','PCM_16') if ext=='.wav' else ('FLAC','PCM_16') if ext=='.flac' else ('WAV','PCM_16');\n"
                "  bp=kw.get('bits_per_sample'); enc=kw.get('encoding','');\n"
                "  sub='PCM_24' if bp==24 else 'FLOAT' if enc=='PCM_F' else sub;\n"
                "  sf.write(str(uri),w,sample_rate,subtype=sub,format=fmt)\n"
                "torchaudio.save=_sf_save; "
                "from demucs.separate import main; main()"
            )
            
            cmds = [
                [sys.executable, fixer_path, "-n", "htdemucs", "--flac", "--out", base_dir, self.file_path],
                [sys.executable, "-c", inline_fixer, "-n", "htdemucs", "--flac", "--out", base_dir, self.file_path]
            ]
            
            success_proc = False
            last_err = ""
            
            for cmd in cmds:
                try:
                    process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT, 
                        text=True, 
                        env=env,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            print(f"[AI RAW] {line.strip()}")
                            if "%" in line:
                                match = re.search(r"(\d+)%", line)
                                if match:
                                    percent = match.group(1)
                                    self.progress.emit(f"İşleniyor: %{percent}")
                            elif "[" in line and "/" in line:
                                stage = line[line.find("["):line.find("]")+1]
                                if stage: self.progress.emit(f"Aşama: {stage}")
                    
                    if process.returncode == 0:
                        success_proc = True
                        break
                    else:
                        process.wait()
                        last_err = "İşlem yarıda kesildi veya hata oluştu."
                except Exception as e:
                    last_err = str(e)
                    continue
            
            if success_proc:
                print(f"[AI] Lokal işlem başarılı: {self.file_path}")
                model_name = "htdemucs"
                temp_dir = os.path.join(base_dir, model_name, file_name)
                
                if os.path.exists(temp_dir):
                    if os.path.exists(output_dir):
                        shutil.rmtree(output_dir)
                    os.rename(temp_dir, output_dir)
                self.finished.emit(self.file_path, True)
            else:
                print(f"[AI] Lokal işlem başarısız. Çıktı: {last_err}")
                self.progress.emit("Lokal Hata Detayı:")
                if "ModuleNotFoundError" in last_err:
                    self.progress.emit("Hata: Demucs modülü bulunamadı.")
                else:
                    short_err = last_err.strip().split('\n')[-1]
                    self.progress.emit(f"Hata: {short_err[:100]}")
                self.finished.emit(self.file_path, False)
        except Exception as e:
            msg = f"Sistem Hatası: {str(e)}"
            print(f"[AI] {msg}")
            self.progress.emit(msg)
            self.finished.emit(self.file_path, False)
