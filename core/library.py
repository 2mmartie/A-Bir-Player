"""
library.py — Kütüphane ve parça yönetimi.
Track nesneleri lazy metadata yükleme yapar (ilk erişimde).
"""
import os
import random
import re
from pathlib import Path
from .metadata import TrackMetadata


class Track:
    """Tek bir FLAC dosyasını temsil eder."""

    def __init__(self, path: str):
        self.path = path
        self._metadata: TrackMetadata | None = None

    @property
    def metadata(self) -> TrackMetadata:
        if self._metadata is None:
            self._metadata = TrackMetadata.from_file(self.path)
        return self._metadata

    @property
    def display_title(self) -> str:
        if self._metadata:
            return self._metadata.title
        return Path(self.path).stem

    def __repr__(self):
        return f"<Track {Path(self.path).name}>"


class Library:
    """Kütüphanedeki tüm parçaları yönetir."""

    def __init__(self):
        self.tracks: list[Track] = []
        self._shuffle_order: list[int] = []
        self._shuffled = False

    # ------------------------------------------------------------------ #
    # Ekleme / Çıkarma
    # ------------------------------------------------------------------ #
    def _natural_sort_key(self, s: str):
        return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

    def add_folder(self, folder_path: str) -> list[Track]:
        """Bir klasördeki tüm .flac/.mp3 dosyalarını ekler. (Unknown/Unknown olanları eler)"""
        new_tracks: list[Track] = []
        existing_paths = {t.path for t in self.tracks}

        for root, dirs, files in os.walk(folder_path):
            dirs.sort(key=self._natural_sort_key)
            for fname in sorted(files, key=self._natural_sort_key):
                if fname.lower().endswith((".flac", ".mp3", ".wav", ".ogg", ".m4a")):
                    full = os.path.join(root, fname)
                    if full not in existing_paths:
                        track = Track(full)
                        # Unknown + Unknown filtreleme
                        m = track.metadata
                        if m.title.lower() == "unknown title" and m.artist.lower() == "unknown artist":
                            continue
                        new_tracks.append(track)
                        existing_paths.add(full)

        self.tracks.extend(new_tracks)
        self._rebuild_shuffle()
        return new_tracks

    def add_files(self, file_paths: list[str]) -> list[Track]:
        """Seçilen dosyaları ekler. (Unknown/Unknown olanları eler)"""
        existing_paths = {t.path for t in self.tracks}
        new_tracks: list[Track] = []
        
        file_paths_sorted = sorted(file_paths, key=lambda x: self._natural_sort_key(Path(x).name))
        
        for fp in file_paths_sorted:
            if fp.lower().endswith((".flac", ".mp3", ".wav", ".ogg", ".m4a")) and fp not in existing_paths:
                track = Track(fp)
                m = track.metadata
                if m.title.lower() == "unknown title" and m.artist.lower() == "unknown artist":
                    continue
                new_tracks.append(track)
                existing_paths.add(fp)
        self.tracks.extend(new_tracks)
        self._rebuild_shuffle()
        return new_tracks

    def remove_track(self, track: Track):
        if track in self.tracks:
            self.tracks.remove(track)
            self._rebuild_shuffle()

    def clear(self):
        self.tracks.clear()
        self._shuffle_order.clear()

    # ------------------------------------------------------------------ #
    # Navigasyon
    # ------------------------------------------------------------------ #
    def index_of(self, track: Track | None) -> int:
        if track is None or track not in self.tracks:
            return 0
        return self.tracks.index(track)

    def next_track(self, current: Track | None, shuffle: bool = False) -> Track | None:
        if not self.tracks:
            return None
        if shuffle:
            return self._shuffle_next(current)
        if current is None or current not in self.tracks:
            return self.tracks[0]
        idx = self.index_of(current)
        next_idx = (idx + 1) % len(self.tracks)
        return self.tracks[next_idx]

    def prev_track(self, current: Track | None, shuffle: bool = False) -> Track | None:
        if not self.tracks:
            return None
        if current is None or current not in self.tracks:
            return self.tracks[0]
        idx = self.index_of(current)
        prev_idx = (idx - 1) % len(self.tracks)
        return self.tracks[prev_idx]

    # ------------------------------------------------------------------ #
    # Shuffle
    # ------------------------------------------------------------------ #
    def _rebuild_shuffle(self):
        self._shuffle_order = list(range(len(self.tracks)))
        random.shuffle(self._shuffle_order)

    def _shuffle_next(self, current: Track | None) -> Track | None:
        if not self._shuffle_order or not self.tracks:
            return None
        if current is None or current not in self.tracks:
            return self.tracks[self._shuffle_order[0]]
        cur_idx = self.index_of(current)
        try:
            pos = self._shuffle_order.index(cur_idx)
            next_pos = (pos + 1) % len(self._shuffle_order)
        except ValueError:
            next_pos = 0
        return self.tracks[self._shuffle_order[next_pos]]

    def reshuffle(self):
        self._rebuild_shuffle()

    def search(self, query: str) -> list[Track]:
        """Başlık, sanatçı veya albüme göre arama yapar."""
        if not query:
            return []
        q = query.lower()
        results = []
        for track in self.tracks:
            m = track.metadata
            if (q in m.title.lower()) or (q in m.artist.lower()) or (m.album and q in m.album.lower()):
                results.append(track)
        return results
