"""
metadata.py — FLAC dosyasından tag ve kapak resmi okur.
mutagen kullanır, kayıpsız/audio verisine dokunmaz.
"""
import mutagen
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from pathlib import Path
import re


class TrackMetadata:
    """Bir FLAC parçasının tüm meta verilerini tutar."""

    def __init__(self):
        self.title = "Unknown Title"
        self.artist = "Unknown Artist"
        self.album = "Unknown Album"
        self.year = ""
        self.track_number = 0
        self.duration = 0.0        # saniye (float)
        self.sample_rate = 0      # Hz (ör: 44100, 96000)
        self.bit_depth = 0        # ör: 16, 24
        self.channels = 0         # ör: 2 (stereo)
        self.cover_art: bytes | None = None   # Ham JPEG/PNG baytları

    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path: str) -> "TrackMetadata":
        meta = cls()
        try:
            f = mutagen.File(path)
            if f is None: return meta

            # Tag extraction
            def _get(tags, keys, default=""):
                for k in keys:
                    if k in tags:
                        return str(tags[k][0])
                return default
            
            def _clean_title(title: str) -> str:
                # Remove leading track numbers and separators like "01 - ", "02_ ", "1. ", etc.
                return re.sub(r'^\d+[\s\.\-_]+', '', title).strip()

            ext = Path(path).suffix.lower()
            if ext == ".flac":
                raw_title = _get(f, ["title"], Path(path).stem)
                meta.title = _clean_title(raw_title)
                meta.artist = _get(f, ["artist"], "Unknown Artist")
                meta.album  = _get(f, ["album"], "Unknown Album")
                meta.year   = _get(f, ["date"], "")
                if f.pictures:
                    meta.cover_art = f.pictures[0].data
            elif ext == ".mp3":
                raw_title = _get(f, ["TIT2"], Path(path).stem)
                meta.title = _clean_title(raw_title)
                meta.artist = _get(f, ["TPE1"], "Unknown Artist")
                meta.album  = _get(f, ["TALB"], "Unknown Album")
                meta.year   = _get(f, ["TDRC", "TYER"], "")
                # MP3 cover extraction
                if f.tags:
                    for tag in f.tags.values():
                        if isinstance(tag, APIC):
                            meta.cover_art = tag.data
                            break
            else:
                # Generic handling for other formats (WAV, OGG, M4A)
                raw_title = _get(f, ["title"], Path(path).stem)
                meta.title = _clean_title(raw_title)
                meta.artist = _get(f, ["artist"], "Unknown Artist")
                meta.album  = _get(f, ["album"], "Unknown Album")

            if f.info:
                meta.duration    = f.info.length
                meta.sample_rate = getattr(f.info, "sample_rate", 0)
                meta.bit_depth   = getattr(f.info, "bits_per_sample", 0)
                meta.channels    = getattr(f.info, "channels", 0)

            # Fallback for cover
            if not meta.cover_art:
                p = Path(path).parent
                cover_names = ["cover", "folder", "front", "album", "artwork"]
                exts = [".jpg", ".jpeg", ".png"]
                for name in cover_names:
                    for ext_img in exts:
                        img_path = p / (name + ext_img)
                        if img_path.exists():
                            meta.cover_art = img_path.read_bytes()
                            break
                    if meta.cover_art: break

        except Exception:
            pass
        return meta

    # ------------------------------------------------------------------ #
    @property
    def duration_str(self) -> str:
        """MM:SS biçiminde süre."""
        total = int(self.duration)
        return f"{total // 60:02d}:{total % 60:02d}"

    @property
    def quality_str(self) -> str:
        """Örn: '96 kHz / 24-bit / Stereo'"""
        ch = "Stereo" if self.channels == 2 else f"{self.channels}ch"
        khz = f"{self.sample_rate / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{khz} kHz  ·  {self.bit_depth}-bit  ·  {ch}"
