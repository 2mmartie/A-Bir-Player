"""
library_manager.py — Kütüphane yönetimi (ekleme, kaldırma, temizleme).
"""
import os
from core.library import Library, Track
from core.lastfm import LastFmService

class LibraryManager:
    @staticmethod
    def remove_track(library: Library, track: Track):
        """Parçayı kütüphaneden kaldırır (dosyayı silmez)."""
        if track in library.tracks:
            library.tracks.remove(track)
            LibraryManager.save_library(library)

    @staticmethod
    def remove_album(library: Library, album_name: str):
        """Belirli bir albüme ait tüm parçaları kaldırır."""
        to_remove = [t for t in library.tracks if (t.metadata.album or "Unknown Album") == album_name]
        for t in to_remove:
            library.tracks.remove(t)
        LibraryManager.save_library(library)

    @staticmethod
    def clear_library(library: Library):
        """Kütüphanedeki tüm parçaları temizler."""
        library.tracks.clear()
        LibraryManager.save_library(library)

    @staticmethod
    def save_library(library: Library):
        """Mevcut kütüphane yollarını config'e kaydeder."""
        paths = [t.path for t in library.tracks]
        LastFmService.save_config({"library_paths": paths})
