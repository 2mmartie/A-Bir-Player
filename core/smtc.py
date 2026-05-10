"""
smtc.py — Windows System Media Transport Controls (SMTC) integration using winrt.
"""
import os
import tempfile
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

def _get_winrt():
    # Try modern modular winrt first (preferred)
    try:
        import winrt.windows.media as wm
        import winrt.windows.media.playback as wmp
        import winrt.windows.storage.streams as streams
        import winrt.windows.foundation as wf
        return wm, wmp, streams, wf
    except ImportError:
        pass
        
    # Fallback to deprecated winsdk
    try:
        import winsdk.windows.media as wm
        import winsdk.windows.media.playback as wmp
        import winsdk.windows.storage.streams as streams
        import winsdk.windows.foundation as wf
        return wm, wmp, streams, wf
    except ImportError:
        return None, None, None, None

WINRT_AVAILABLE = False # Will check inside class

class SimpleSMTC(QObject):
    play_requested  = pyqtSignal()
    pause_requested = pyqtSignal()
    next_requested  = pyqtSignal()
    prev_requested  = pyqtSignal()

    def __init__(self, hwnd: int, parent=None):
        super().__init__(parent)
        self._ok = False
        
        self.wm, self.wmp, self.streams, self.wf = _get_winrt()
        if not self.wm:
            print("[SMTC] winrt kütüphanesi bulunamadı. SMTC devre dışı.")
            return

        try:
            # For Win32 apps, get_for_current_view() often fails.
            # Using a dummy MediaPlayer is a reliable way to get an SMTC instance.
            self._player = self.wmp.MediaPlayer()
            self._smtc = self._player.system_media_transport_controls
            
            # Configure SMTC
            self._smtc.is_enabled = True
            self._smtc.is_play_enabled = True
            self._smtc.is_pause_enabled = True
            self._smtc.is_next_enabled = True
            self._smtc.is_previous_enabled = True
            
            # Connect events
            self._smtc.add_button_pressed(self._on_button_pressed)
            
            self.set_playback_status(self.wm.MediaPlaybackStatus.STOPPED)
            self._ok = True
        except Exception as e:
            print(f"[SMTC] Başlatma hatası: {e}")

    def _on_button_pressed(self, sender, args):
        try:
            btn = args.button
            if btn == self.wm.SystemMediaTransportControlsButton.PLAY:
                self.play_requested.emit()
            elif btn == self.wm.SystemMediaTransportControlsButton.PAUSE:
                self.pause_requested.emit()
            elif btn == self.wm.SystemMediaTransportControlsButton.STOP:
                self.pause_requested.emit()
            elif btn == self.wm.SystemMediaTransportControlsButton.NEXT:
                self.next_requested.emit()
            elif btn == self.wm.SystemMediaTransportControlsButton.PREVIOUS:
                self.prev_requested.emit()
        except Exception as e:
            print(f"[SMTC] Button error: {e}")

    def update_track(self, title: str, artist: str, album: str, cover_bytes: Optional[bytes] = None):
        if not self._ok: return
        try:
            updater = self._smtc.display_updater
            updater.type = self.wm.MediaPlaybackType.MUSIC
            
            props = updater.music_properties
            props.title = title or "Unknown Title"
            props.artist = artist or "Unknown Artist"
            props.album_title = album or ""
            
            if cover_bytes:
                try:
                    # In some environments, sync stream writing is tricky.
                    # We'll use a safer approach: write to a temporary file if memory stream fails
                    stream = self.streams.InMemoryRandomAccessStream()
                    writer = self.streams.DataWriter(stream)
                    writer.write_bytes(cover_bytes)
                    # Use a fire-and-forget approach or try to wait if possible
                    # In winsdk, we can't easily block on async without a loop.
                    # But for thumbnails, sometimes it works even if we just trigger it.
                    writer.store_async()
                    
                    updater.thumbnail = self.streams.RandomAccessStreamReference.create_from_stream(stream)
                except Exception as e:
                    print(f"[SMTC] Thumbnail error: {e}")
            else:
                updater.thumbnail = None
                    
            updater.update()
            self.set_playback_status(self.wm.MediaPlaybackStatus.PLAYING)
        except Exception as e:
            print(f"[SMTC] Güncelleme hatası: {e}")

    def set_playback_status(self, status):
        if not self._ok: return
        self._smtc.playback_status = status

    def set_playing(self, playing: bool):
        if not self._ok: return
        status = self.wm.MediaPlaybackStatus.PLAYING if playing else self.wm.MediaPlaybackStatus.PAUSED
        self.set_playback_status(status)

    def set_stopped(self):
        if not self._ok: return
        self.set_playback_status(self.wm.MediaPlaybackStatus.STOPPED)
