"""
Demucs Fixer - torchaudio 2.9+ torchcodec sorununu çözer.

Torchaudio 2.9+ sürümlerinde save() fonksiyonu tamamen torchcodec'e
yönlendirildi. Ancak torchcodec Windows'ta FFmpeg shared DLL'leri
gerektirir. Bu script, torchaudio.save()'i soundfile kütüphanesi ile
değiştirerek sorunu tamamen bypass eder.
"""
import sys
import os
import numpy as np

# ── 1. torchaudio.save'i soundfile tabanlı implementasyonla değiştir ──
import torch
import torchaudio

try:
    import soundfile as sf
except ImportError:
    print("[demucs_fixer] HATA: soundfile kütüphanesi bulunamadı!")
    print("[demucs_fixer] Lütfen çalıştırın: pip install soundfile")
    sys.exit(1)


def _soundfile_save(
    uri,
    src,
    sample_rate,
    channels_first=True,
    format=None,
    encoding=None,
    bits_per_sample=None,
    buffer_size=4096,
    backend=None,
    compression=None,
):
    """torchaudio.save yerine soundfile kullanan drop-in replacement."""
    # Tensor → numpy
    if isinstance(src, torch.Tensor):
        wav = src.detach().cpu()
        if channels_first and wav.dim() == 2:
            wav = wav.t()  # [C, T] → [T, C]
        wav = wav.numpy()
    else:
        wav = np.array(src)

    path = str(uri)
    ext = os.path.splitext(path)[1].lower()

    # Format ve subtype belirleme
    if ext == ".wav":
        sf_format = "WAV"
        if encoding and "FLOAT" in encoding.upper() or encoding == "PCM_F":
            subtype = "FLOAT"
        elif bits_per_sample == 24:
            subtype = "PCM_24"
        elif bits_per_sample == 32:
            if encoding and "PCM_F" in encoding:
                subtype = "FLOAT"
            else:
                subtype = "PCM_32"
        else:
            subtype = "PCM_16"
    elif ext == ".flac":
        sf_format = "FLAC"
        if bits_per_sample == 24:
            subtype = "PCM_24"
        else:
            subtype = "PCM_16"
    elif ext == ".ogg":
        sf_format = "OGG"
        subtype = "VORBIS"
    else:
        # Fallback: WAV olarak kaydet
        sf_format = "WAV"
        subtype = "PCM_16"

    sf.write(path, wav, sample_rate, subtype=subtype, format=sf_format)


# Monkey-patch: torchaudio.save'i tamamen değiştir
torchaudio.save = _soundfile_save

# Ayrıca demucs.audio modülündeki ta referansını da yakala
# (import edildikten sonra da çalışsın diye)
import importlib
try:
    # Eğer demucs.audio zaten import edildiyse, oradaki ta.save'i de değiştir
    demucs_audio = importlib.import_module("demucs.audio")
    if hasattr(demucs_audio, "ta"):
        demucs_audio.ta.save = _soundfile_save
except Exception:
    pass

print("[demucs_fixer] torchaudio.save -> soundfile backend aktif.")

# ── 2. Demucs'u başlat ──
from demucs.separate import main

if __name__ == "__main__":
    main()
