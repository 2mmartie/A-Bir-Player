import os
import sys
import json
import subprocess
import time
from pathlib import Path
from core.metadata import TrackMetadata

# Proje kök dizinini ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    with open("batch_log.txt", "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")

def get_config_data():
    config_path = os.path.join(BASE_DIR, "config.json")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def get_all_music_files(folders):
    extensions = (".flac", ".mp3", ".wav", ".ogg", ".m4a")
    files = []
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for root, _, filenames in os.walk(folder):
            for f in filenames:
                if f.lower().endswith(extensions):
                    path = os.path.join(root, f)
                    # Metadata kontrolü
                    meta = TrackMetadata.from_file(path)
                    if meta.title.lower() == "unknown title" and meta.artist.lower() == "unknown artist":
                        continue
                    files.append(path)
    return files

def draw_progress(current, total, song_name, detail=""):
    """Tek satırda progress bar çizer."""
    length = 30
    filled = int(length * current // total)
    bar = '█' * filled + '░' * (length - filled)
    percent = (100 * current // total)
    
    # Konsol genişliğini aşmamak için şarkı ismini kısalt
    if len(song_name) > 25:
        song_name = song_name[:22] + "..."
        
    status = f"\r[Batch: {current}/{total}] |{bar}| {percent}% | {song_name} {detail}"
    sys.stdout.write(status)
    sys.stdout.flush()

def separate_song(file_path, idx, total):
    # Demucs fixer path
    fixer_path = os.path.join(BASE_DIR, "demucs_fixer.py")
    base_dir = os.path.dirname(file_path)
    file_name = os.path.basename(file_path).rsplit('.', 1)[0]
    output_dir = os.path.join(base_dir, f"{file_name}_stems")

    # Zaten ayrıştırılmışsa atla
    if os.path.exists(output_dir):
        return "ALREADY_DONE"

    song_display = os.path.basename(file_path)
    draw_progress(idx, total, song_display, "Başlatılıyor...")
    
    # FFmpeg kontrolü ve PATH ekleme
    local_bin = os.path.join(BASE_DIR, "bin")
    env = os.environ.copy()
    if os.path.exists(local_bin):
        env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")

    # Demucs komutu (htdemucs modeli)
    cmd = [sys.executable, fixer_path, "-n", "htdemucs", "--out", base_dir, file_path]
    
    try:
        # Demucs çıktısını anlık okumak için Popen kullanıyoruz
        process = subprocess.Popen(
            cmd, 
            env=env,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            encoding="utf-8",
            bufsize=1,
            universal_newlines=True
        )
        
        # Demucs'un % ilerlemesini yakalamaya çalış
        for line in process.stdout:
            if "%" in line:
                # Satırdaki son % değerini bulmaya çalış
                parts = line.strip().split()
                percent_part = next((p for p in parts if "%" in p), "")
                if percent_part:
                    draw_progress(idx, total, song_display, percent_part)
        
        process.wait()
        
        if process.returncode == 0:
            return "SUCCESS"
        else:
            log(f"Hata (Kod {process.returncode}): {song_display}")
            return "FAILED"
    except Exception as e:
        log(f"Sistem Hatası ({song_display}): {str(e)}")
        return "ERROR"

def main():
    print("\n=== GECE BOYU AYRIŞTIRMA MODU AKTİF ===")
    log("=== YENİ OTURUM BAŞLADI ===")
    
    data = get_config_data()
    folders = data.get("library_folders", [])
    library_paths = data.get("library_paths", [])

    all_files = []
    if folders:
        all_files = get_all_music_files(folders)
    
    # Klasörlerden dosya çıkmazsa veya klasör yoksa doğrudan library_paths kullan
    if not all_files and library_paths:
        for path in library_paths:
            if not os.path.exists(path): continue
            meta = TrackMetadata.from_file(path)
            if meta.title.lower() == "unknown title" and meta.artist.lower() == "unknown artist":
                continue
            all_files.append(path)

    if not all_files:
        print("Hata: Kütüphane boş. Önce uygulama üzerinden klasör ekleyin.")
        return

    total = len(all_files)
    done_count = 0
    fail_count = 0
    skip_count = 0

    for i, file_path in enumerate(all_files, 1):
        status = separate_song(file_path, i, total)
        
        if status == "SUCCESS":
            done_count += 1
            log(f"Başarılı: {os.path.basename(file_path)}")
        elif status == "ALREADY_DONE":
            skip_count += 1
        else:
            fail_count += 1
            log(f"BAŞARISIZ: {os.path.basename(file_path)}")

    # İşlem bitince progress bar'ı tamamla ve özeti göster
    draw_progress(total, total, "TAMAMLANDI", "")
    print(f"\n\n=== İŞLEM BİTTİ ===")
    print(f"Başarılı: {done_count} | Zaten Ayrılmış: {skip_count} | Hata: {fail_count}")
    log(f"Özet: {done_count} yeni, {skip_count} skip, {fail_count} hata.")

if __name__ == "__main__":
    main()
