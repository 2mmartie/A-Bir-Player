import os
import sys
import urllib.request
import zipfile
import shutil

def download_ffmpeg():
    bin_dir = os.path.join(os.getcwd(), "bin")
    if not os.path.exists(bin_dir):
        os.makedirs(bin_dir)
    
    ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print("FFmpeg zaten mevcut.")
        return

    print("FFmpeg indiriliyor (gyan.dev)...")
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    zip_path = os.path.join(bin_dir, "ffmpeg.zip")
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Zık klasörü açılıyor...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the bin/ffmpeg.exe and bin/ffprobe.exe in the zip
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe") or member.endswith("ffprobe.exe"):
                    filename = os.path.basename(member)
                    source = zip_ref.open(member)
                    target = open(os.path.join(bin_dir, filename), "wb")
                    with source, target:
                        shutil.copyfileobj(source, target)
        
        os.remove(zip_path)
        print("FFmpeg başarıyla kuruldu (bin/ klasörüne).")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    download_ffmpeg()
