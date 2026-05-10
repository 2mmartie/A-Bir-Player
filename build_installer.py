import os
import subprocess
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_command(cmd, msg):
    print(f"\n>>> {msg}...")
    log_file = os.path.join(BASE_DIR, "build_log.txt")
    from datetime import datetime
    with open(log_file, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        f.write(f"\n\n{timestamp} === {msg} ===\n")
        f.flush()
        try:
            # Use subprocess.Popen to stream output to file and console
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                line_ts = datetime.now().strftime("[%H:%M:%S] ")
                f.write(line_ts + line)
                f.flush()
                print(line_ts + line, end="") 
            process.wait()
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
            print(f"DONE: {msg}")
        except Exception as e:
            f.write(f"\nERROR: {e}\n")
            print(f"ERROR during {msg}: {e}")
            sys.exit(1)

def get_version():
    """main.py içindeki versiyonu bulur."""
    main_path = os.path.join(BASE_DIR, "main.py")
    try:
        with open(main_path, "r", encoding="utf-8") as f:
            for line in f:
                if 'setApplicationVersion' in line:
                    # Satırdan "1.0.0" gibi degeri ceker
                    import re
                    match = re.search(r'\"(.*?)\"', line)
                    if match: return match.group(1)
    except: pass
    return "1.0.0"

def main():
    print("=== LOSSLESS PLAYER BUILD MASTER ===")
    version = get_version()
    print(f"Versiyon Algılandı: v{version}")
    
    # 1. FFmpeg Hazır mı?
    bin_dir = os.path.join(BASE_DIR, "bin")
    ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")
    if not os.path.exists(ffmpeg_exe):
        run_command("python setup_ffmpeg.py", "FFmpeg indiriliyor")
    else:
        print("FFmpeg zaten mevcut.")

    # 2. PyInstaller ile Bundle Oluştur
    spec_file = os.path.join(BASE_DIR, "ABirPlayer.spec")
    run_command(f"{sys.executable} -m PyInstaller --noconfirm \"{spec_file}\"", "Uygulama paketleniyor")

    # 3. Arşivleme (Eskisini silmez, yanına yenisini versiyonlu koyar)
    dist_root = os.path.join(BASE_DIR, "dist")
    source_dir = os.path.join(dist_root, "A-Bir Player")
    target_dir = os.path.join(dist_root, f"A-Bir Player_v{version}")

    if os.path.exists(source_dir):
        if os.path.exists(target_dir):
            print(f"\n[UYARI] v{version} zaten mevcut, üzerine yazılıyor...")
            shutil.rmtree(target_dir)
        
        shutil.copytree(source_dir, target_dir)
        print(f"\nBAŞARILI! Yeni sürüm arşivlendi: {target_dir}")
        print(f"Arkadaşınla paylaşacağın klasör: LossLessPlayer_v{version}")
    else:
        print("\nBir sorun oluştu, build klasörü bulunamadı.")

if __name__ == "__main__":
    main()
