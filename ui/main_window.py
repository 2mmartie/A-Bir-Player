"""
main_window.py — Next-Gen Professional UI Architecture
"""
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QSplitter, QStatusBar, QStackedWidget, QPushButton, QLabel, QFrame, QMessageBox,
    QLineEdit
)
from PyQt5.QtGui import QPixmap

from resource_path import resource_path

from core.audio_engine import AudioEngine
from core.metadata import TrackMetadata
from core.library import Library, Track
from core.library_manager import LibraryManager
from core.lastfm import LastFmService
from core.stats_manager import StatsManager
from core.smtc import SimpleSMTC
from core.ai_separator import AISeparator
from ui.player_panel import (
    HomeView, AlbumDetailView, NowPlayingView, BottomPlayerBar, StatsView, SearchView, HelpView, get_icon, _round_pixmap,
    AudioVisualizer
)

def _make_transparent(pixmap: QPixmap) -> QPixmap:
    from PyQt5.QtGui import QImage
    image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
    # Target common background colors (black or near-black)
    for y in range(image.height()):
        for x in range(image.width()):
            c = image.pixelColor(x, y)
            # If it's black or very dark, make it transparent
            if c.red() < 20 and c.green() < 20 and c.blue() < 20:
                image.setPixelColor(x, y, Qt.transparent)
    return QPixmap.fromImage(image)
from core.theme_manager import ThemeManager
from core.i18n import I18n
import json
import os
from ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("A-Bir Player")
        self.setMinimumSize(900, 600)
        self.resize(1100, 750)
        self.setAttribute(Qt.WA_TranslucentBackground) # Important for background image transparency
        
        # Set icon
        icon_path = resource_path(os.path.join("ui", "logo.png"))
        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        self._library = Library()
        self._engine  = AudioEngine(self)
        self._lastfm  = LastFmService(self)
        self._stats = StatsManager()
        self._smtc: SimpleSMTC | None = None

        self._current_track: Track | None = None
        self._track_start_time = 0.0
        self._shuffle_on = False
        self._repeat_on  = False
        self._play_queue = []
        self._quick_picks = []
        self._playing_queue_mode = False
        self._current_track_was_logged = False
        
        self._ai_batch_queue = [] # Queue for batch separation
        self._is_ai_busy = False

        self._build_ui()
        self._connect_signals()
        self._init_state()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        # ── Overlay Widget (for color & win_opacity) ──
        self._overlay_widget = QFrame(central)
        self._overlay_widget.setObjectName("MainWindowOverlay")
        
        # ── Background Widget (for image) ──
        from PyQt5.QtWidgets import QLabel
        self._bg_widget = QLabel(central)
        self._bg_widget.setObjectName("MainWindowBG")
        self._bg_widget.setScaledContents(True)
        
        # Correct stacking: BG at bottom, then Overlay, then Layout Content
        self._overlay_widget.lower()
        self._bg_widget.lower()
        
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        upper_layout = QHBoxLayout()
        upper_layout.setSpacing(0)

        # ── Sidebar ──
        self._sidebar = QFrame()
        self._sidebar.setObjectName("Sidebar")
        sidebar_v = QVBoxLayout(self._sidebar)
        sidebar_v.setContentsMargins(0, 0, 0, 0)
        sidebar_v.setAlignment(Qt.AlignTop)

        logo = QLabel()
        logo.setObjectName("SidebarLogo")
        logo_path = resource_path(os.path.join("ui", "logo.png"))
        if os.path.exists(logo_path):
            pm = QPixmap(logo_path)
            logo_pixmap = _round_pixmap(pm.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation), 24)
            logo.setPixmap(logo_pixmap)
        else:
            logo.setText("LOSSLESS")
            logo.setStyleSheet("font-size: 24px; font-weight: 900; padding: 20px;")
        logo.setAlignment(Qt.AlignCenter)
        logo.setContentsMargins(0, 20, 0, 20)
        sidebar_v.addWidget(logo)

        # Nav buttons (no search here anymore)
        self._btn_home = QPushButton(f"  {I18n.t('home')}")
        self._btn_home.setIcon(get_icon("home", "#B3B3B3", 20))
        self._btn_home.setProperty("active", "true")
        
        self._btn_stats = QPushButton(f"  {I18n.t('stats')}")
        self._btn_stats.setIcon(get_icon("stats", "#B3B3B3", 20))
        
        self._btn_add = QPushButton(f"  {I18n.t('add_music')}")
        self._btn_add.setIcon(get_icon("add", "#B3B3B3", 20))
        
        self._btn_clear = QPushButton(f"  {I18n.t('clear_library')}")
        self._btn_clear.setIcon(get_icon("clear", "#B3B3B3", 20))
        
        self._btn_settings = QPushButton(f"  {I18n.t('settings')}")
        self._btn_settings.setIcon(get_icon("settings", "#B3B3B3", 20))

        self._btn_help = QPushButton(f"  {I18n.t('help')}")
        self._btn_help.setIcon(get_icon("help", "#B3B3B3", 20))

        sidebar_v.addWidget(self._btn_home)
        sidebar_v.addWidget(self._btn_stats)
        sidebar_v.addWidget(self._btn_help)
        sidebar_v.addWidget(self._btn_add)
        sidebar_v.addWidget(self._btn_clear)
        sidebar_v.addStretch()
        sidebar_v.addWidget(self._btn_settings)

        upper_layout.addWidget(self._sidebar)

        # ── Right side: Top Bar + Content Stack ──
        right_column = QVBoxLayout()
        right_column.setSpacing(0)
        right_column.setContentsMargins(0, 0, 0, 0)

        # ── Top Bar ──
        self._top_bar = QFrame()
        self._top_bar.setObjectName("TopBar")
        self._top_bar.setFixedHeight(64)
        top_bar_layout = QHBoxLayout(self._top_bar)
        top_bar_layout.setContentsMargins(24, 0, 24, 0)
        top_bar_layout.setSpacing(16)

        # Page title label (changes with navigation)
        self._page_title = QLabel(I18n.t("home"))
        self._page_title.setObjectName("PageTitle")
        # Add text halo for readability against any background image
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor as _HC
        _halo = QGraphicsDropShadowEffect()
        _halo.setBlurRadius(6)
        _halo.setColor(_HC(0, 0, 0, 180))
        _halo.setOffset(0, 0)
        self._page_title.setGraphicsEffect(_halo)

        # Search input in top bar
        self._search_input = QLineEdit()
        self._search_input.setObjectName("TopBarSearch")
        self._search_input.setPlaceholderText(f"🔍  {I18n.t('search')}...")
        self._search_input.setFixedWidth(280)
        self._search_input.setFixedHeight(38)

        top_bar_layout.addWidget(self._page_title)
        top_bar_layout.addStretch()
        
        # Centered Visualizer
        self._visualizer = AudioVisualizer()
        top_bar_layout.addWidget(self._visualizer, 1)
        
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self._search_input)

        right_column.addWidget(self._top_bar)

        # ── Main Content Stack ──
        self._stack = QStackedWidget()
        self._stack.setObjectName("MainContent")
        
        self._home_view = HomeView()
        self._album_view = AlbumDetailView()
        self._playing_view = NowPlayingView()
        self._stats_view = StatsView(self._stats)
        self._search_view = SearchView()
        self._help_view = HelpView()
        
        self._stack.addWidget(self._home_view)
        self._stack.addWidget(self._album_view)
        self._stack.addWidget(self._playing_view)
        self._stack.addWidget(self._stats_view)
        self._stack.addWidget(self._search_view)
        self._stack.addWidget(self._help_view)
        
        right_column.addWidget(self._stack, 1)
        upper_layout.addLayout(right_column, 1)
        root.addLayout(upper_layout, 1)

        # ── Bottom Player Bar ──
        self._player_bar = BottomPlayerBar()
        root.addWidget(self._player_bar)

        # Initial geometry sync for background layers
        self.centralWidget().layout().activate()
        rect = self.centralWidget().rect()
        if hasattr(self, "_bg_widget"): self._bg_widget.setGeometry(rect)
        if hasattr(self, "_overlay_widget"): self._overlay_widget.setGeometry(rect)

    def _connect_signals(self):
        # Sidebar
        self._btn_home.clicked.connect(lambda: self._stack.setCurrentWidget(self._home_view))
        self._btn_home.clicked.connect(self._update_nav_active)
        self._btn_stats.clicked.connect(self._show_stats)
        self._btn_help.clicked.connect(self._show_help)
        self._btn_add.clicked.connect(self._add_music_dialog)
        self._btn_clear.clicked.connect(self._clear_library_confirm)
        self._btn_settings.clicked.connect(self._open_settings)
        
        # Search
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_view.album_selected.connect(self._show_album_detail)
        self._search_view.track_selected.connect(self._play_track_manual)
        
        # Views
        self._home_view.album_selected.connect(self._show_album_detail)
        self._home_view.album_remove_requested.connect(self._remove_album)
        self._home_view.album_play_requested.connect(self._play_album_directly)
        self._home_view.quick_pick_played.connect(self._play_quick_pick_track)
        self._home_view.quick_pick_play_all.connect(self._play_quick_picks_all)
        self._home_view.quick_pick_refresh.connect(self._refresh_quick_picks)
        
        self._album_view.track_selected.connect(self._play_track_manual)
        self._album_view.track_remove_requested.connect(self._remove_track)
        self._album_view.separate_album_requested.connect(self._start_album_separation)
        
        self._player_bar.art_clicked.connect(lambda: self._stack.setCurrentWidget(self._playing_view))
        self._player_bar.album_clicked.connect(self._show_album_detail)

        # Controls
        self._player_bar.play_pause_clicked.connect(self._engine.toggle_pause)
        self._player_bar.prev_clicked.connect(self._play_prev)
        self._player_bar.next_clicked.connect(self._play_next)
        self._player_bar.seek_requested.connect(self._engine.seek)
        self._player_bar.volume_changed.connect(self._engine.set_volume)
        self._player_bar.stems_updated.connect(self._on_stems_updated)
        self._player_bar.start_separation.connect(self._start_ai_separation)
        self._player_bar.repeat_clicked.connect(self._toggle_repeat)

        # Audio Engine
        self._engine.position_changed.connect(self._player_bar.update_position)
        self._engine.position_changed.connect(self._on_position_changed_gapless)
        self._engine.track_finished.connect(self._on_track_finished)
        self._engine.state_changed.connect(self._on_state_changed)

        # Visualizer
        self._visualizer.set_engine(self._engine)

        # Signal connections for Queue (from player views)
        self._home_view.track_selected.connect(self._play_track_manual) 
        self._album_view.play_next_requested.connect(self._add_to_queue_next)
        self._album_view.add_queue_requested.connect(self._add_to_queue_end)

    def _show_stats(self):
        self._stats_view.refresh()
        self._stack.setCurrentWidget(self._stats_view)

    def _show_help(self):
        self._stack.setCurrentWidget(self._help_view)
        self._update_nav_active()

    def _update_nav_active(self):
        cur = self._stack.currentWidget()
        self._btn_home.setProperty("active", "true" if cur == self._home_view else "false")
        self._btn_stats.setProperty("active", "true" if cur == self._stats_view else "false")

        # Update page title in top bar
        if hasattr(self, "_page_title"):
            if cur == self._home_view:
                self._page_title.setText(I18n.t("home"))
            elif cur == self._stats_view:
                self._page_title.setText(I18n.t("stats"))
            elif cur == self._album_view:
                self._page_title.setText(I18n.t("album"))
            elif cur == self._playing_view:
                self._page_title.setText(I18n.t("now_playing") if I18n.t("now_playing") != "now_playing" else "Now Playing")
            elif cur == self._search_view:
                self._page_title.setText(I18n.t("search_results"))

        # High-contrast icon colors
        theme_cfg = ThemeManager.load_theme_config()
        sidebar_bg = theme_cfg.get("sidebar_bg", ThemeManager.DEFAULT_SIDEBAR_BG)
        from PyQt5.QtGui import QColor as _QC
        _sb = _QC(sidebar_bg)
        _br = (_sb.red() * 299 + _sb.green() * 587 + _sb.blue() * 114) / 1000
        icon_color = "#FFFFFF" if _br < 160 else "#2D2D2D"
        sub_color  = "#FFFFFF" if _br < 160 else "#555555"

        self._btn_home.setIcon(get_icon("home", icon_color if cur == self._home_view else sub_color, 20))
        self._btn_stats.setIcon(get_icon("stats", icon_color if cur == self._stats_view else sub_color, 20))
        self._btn_add.setIcon(get_icon("add", sub_color, 20))
        self._btn_clear.setIcon(get_icon("clear", sub_color, 20))
        self._btn_settings.setIcon(get_icon("settings", sub_color, 20))

        # Force style update
        for btn in [self._btn_home, self._btn_stats, self._btn_add, self._btn_clear, self._btn_settings]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_search_changed(self, text):
        if not text:
            if self._stack.currentWidget() == self._search_view:
                self._stack.setCurrentWidget(self._home_view)
            return
        
        results = self._library.search(text)
        self._search_view.set_results(text, results)
        self._stack.setCurrentWidget(self._search_view)
        self._update_nav_active()

    def _add_music_dialog(self):
        from PyQt5.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, I18n.t("add_music"))
        if path:
            self._library.add_folder(path)
            self._refresh_home_grid()
            LibraryManager.save_library(self._library)

    def _clear_library_confirm(self):
        res = QMessageBox.question(self, I18n.t("clear_library"), "...", 
                                 QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            LibraryManager.clear_library(self._library)
            self._refresh_home_grid()

    def _remove_track(self, track):
        LibraryManager.remove_track(self._library, track)
        self._refresh_ui_after_removal()

    def _remove_album(self, album_name):
        LibraryManager.remove_album(self._library, album_name)
        self._refresh_ui_after_removal()

    def _refresh_ui_after_removal(self):
        self._refresh_home_grid()
        if self._stack.currentWidget() == self._album_view:
            self._stack.setCurrentWidget(self._home_view)
        elif self._stack.currentWidget() == self._playing_view:
             self._playing_view.set_track(self._current_track.metadata, self._current_track.metadata.cover_art, self._library.tracks, self._current_track)

    def _refresh_home_grid(self):
        albums = {}
        for track in self._library.tracks:
            alb_name = track.metadata.album or "Unknown Album"
            if alb_name not in albums:
                albums[alb_name] = {
                    'name': alb_name,
                    'artist': track.metadata.artist,
                    'cover': track.metadata.cover_art
                }
        self._home_view.update_albums(list(albums.values()))
        self._refresh_quick_picks()

    def _refresh_quick_picks(self):
        import random
        if not self._library.tracks:
            self._home_view.update_quick_picks([])
            return

        # Optimization: Don't load metadata for ALL tracks at once (slow on HDD)
        # Instead, take a sample first
        all_tracks = self._library.tracks
        if not all_tracks:
            self._home_view.update_quick_picks([])
            return
            
        sample_size = min(100, len(all_tracks))
        sample = random.sample(all_tracks, sample_size)
        
        def _is_real(t):
            # Only access metadata for the sample
            meta = t.metadata
            title = (meta.title or "").strip().lower()
            artist = (meta.artist or "").strip().lower()
            bad_titles = {"unknown title", "unknown", ""}
            bad_artists = {"unknown artist", "unknown", ""}
            return title not in bad_titles and artist not in bad_artists

        real_tracks = [t for t in sample if _is_real(t)]
        if not real_tracks:
            # Fallback to first few if none are "real" in the sample
            real_tracks = all_tracks[:21]

        count = min(21, len(real_tracks))
        self._quick_picks = random.sample(real_tracks, count)
        self._home_view.update_quick_picks(self._quick_picks)

    def _show_album_detail(self, album_name):
        tracks = [t for t in self._library.tracks if (t.metadata.album or "Unknown Album") == album_name]
        if tracks:
            self._album_view.set_album(album_name, tracks[0].metadata.artist, tracks[0].metadata.cover_art, tracks, self._current_track)
            self._stack.setCurrentWidget(self._album_view)
            self._update_nav_active()

    def _play_album_directly(self, album_name):
        tracks = [t for t in self._library.tracks if (t.metadata.album or "Unknown Album") == album_name]
        if tracks:
            self._shuffle_on = False
            self._playing_queue_mode = True
            self._play_queue = tracks[1:]
            self._play_track(tracks[0])

    @pyqtSlot(object)
    def _play_track_manual(self, track: Track):
        self._shuffle_on = False
        album_name = track.metadata.album or "Unknown Album"
        album_tracks = [t for t in self._library.tracks if (t.metadata.album or "Unknown Album") == album_name]
        try:
            idx = album_tracks.index(track)
            self._play_queue = album_tracks[idx+1:]
            self._playing_queue_mode = True
        except ValueError:
            self._play_queue.clear()
            self._playing_queue_mode = False
        self._play_track(track)

    @pyqtSlot(object)
    def _play_quick_pick_track(self, track: Track):
        self._play_queue.clear()
        self._playing_queue_mode = False
        self._shuffle_on = True
        self._library.reshuffle()
        self._play_track(track)

    @pyqtSlot()
    def _play_quick_picks_all(self):
        if not self._quick_picks: return
        self._play_queue = list(self._quick_picks)
        first_track = self._play_queue.pop(0)
        self._shuffle_on = False
        self._playing_queue_mode = True
        self._play_track(first_track)

    @pyqtSlot(object)
    def _play_track(self, track: Track, start_pos: float = 0.0):
        # 1. Log previous track before switching
        if self._current_track and not self._current_track_was_logged:
            listen_duration = self._engine.position
            meta_prev = self._current_track.metadata
            self._stats.log_play(self._current_track.path, meta_prev.artist, meta_prev.album or "", meta_prev.title, listen_duration)
            self._current_track_was_logged = True # Mark as logged immediately

        self._current_track_was_logged = False
        self._current_track = track
        meta = track.metadata
        if self._engine.load(track.path):
            if start_pos > 0:
                self._engine.seek(start_pos)
            self._engine.play()
            
            # Update player bar with stem availability info
            stems_available = self._engine._stem_mode
            self._player_bar.set_track(meta, meta.cover_art, stems_available)
            
            self._playing_view.set_track(meta, meta.cover_art, self._library.tracks, track)
            
            if self._stack.currentWidget() == self._album_view:
                self._album_view.set_album(meta.album or "Unknown Album", meta.artist, meta.cover_art, 
                                         [t for t in self._library.tracks if (t.metadata.album or "Unknown Album") == (meta.album or "Unknown Album")], track)

            if self._smtc:
                self._smtc.update_track(meta.title, meta.artist, meta.album, meta.cover_art)

            if self._lastfm.is_connected:
                self._lastfm.track_started(meta.artist, meta.title, meta.album or "", meta.duration)

    @pyqtSlot()
    def _play_next(self):
        if not self._library.tracks: return
        if getattr(self, '_playing_queue_mode', False):
            if self._play_queue:
                nxt = self._play_queue.pop(0)
                self._play_track(nxt)
                return
            else:
                self._playing_queue_mode = False
                self._shuffle_on = True
                self._library.reshuffle()
                nxt = self._library.next_track(self._current_track, self._shuffle_on)
                if nxt: self._play_track(nxt)
                return
        nxt = self._library.next_track(self._current_track, self._shuffle_on)
        if nxt: self._play_track(nxt)

    @pyqtSlot()
    def _play_prev(self):
        if self._engine.position > 3.0:
            self._engine.seek(0.0)
        else:
            prv = self._library.prev_track(self._current_track, self._shuffle_on)
            if prv: self._play_track(prv)

    def _toggle_shuffle(self):
        self._shuffle_on = not self._shuffle_on
        if self._shuffle_on: self._library.reshuffle()
        self._player_bar.set_shuffle(self._shuffle_on)

    def _toggle_repeat(self):
        self._repeat_on = not self._repeat_on
        self._player_bar.set_repeat(self._repeat_on)

    def _add_to_queue_next(self, track: Track):
        if not hasattr(self, '_play_queue'): self._play_queue = []
        self._play_queue.insert(0, track)
        self._playing_queue_mode = True

    def _add_to_queue_end(self, track: Track):
        if not hasattr(self, '_play_queue'): self._play_queue = []
        self._play_queue.append(track)
        self._playing_queue_mode = True

    @pyqtSlot(str)
    def _on_state_changed(self, state: str):
        playing = (state == "playing")
        self._player_bar.set_playing(playing)
        self._visualizer.set_playing(playing)
        if self._smtc:
            if state == "stopped": self._smtc.set_stopped()
            else: self._smtc.set_playing(playing)

    def _on_position_changed_gapless(self, pos: float):
        """Triggers pre-loading of the next track when current track is near end."""
        dur = self._engine.duration
        if dur > 0 and (dur - pos) < 10.0:
            # Check if already pre-loaded
            if hasattr(self._engine, "_next_ready") and not self._engine._next_ready:
                next_track = self._get_next_track_peek()
                if next_track:
                    self._engine.load(next_track.path, is_preload=True)

    def _get_next_track_peek(self) -> Track | None:
        """Looks ahead to see what's next in line."""
        if self._playing_queue_mode and self._play_queue:
            return self._play_queue[0]
        return self._library.next_track(self._current_track, self._shuffle_on)

    def _on_track_finished(self):
        # Use a local ref to avoid race condition if _current_track changes while logging
        track_to_log = self._current_track
        if track_to_log and not self._current_track_was_logged:
            meta = track_to_log.metadata
            # Verify if the engine is actually at the end of THIS track
            # (duration is a property of the current engine state)
            self._stats.log_play(track_to_log.path, meta.artist, meta.album or "", meta.title, self._engine.duration)
            self._current_track_was_logged = True
        if self._repeat_on: self._engine.seek(0.0); self._engine.play()
        else: self._play_next()

    def _init_state(self):
        # ── Apply saved theme FIRST (background image + overlay) ──
        self._apply_startup_theme()

        cfg = LastFmService.load_config()
        last_track = cfg.get("last_track")
        last_pos = cfg.get("last_position", 0.0)
        
        # Last.fm
        api_key = cfg.get("lastfm", {}).get("api_key")
        if api_key:
            # Reconnect logic
            pass
        # Library
        paths = cfg.get("library_paths", [])
        if paths:
            self._library.add_files(paths)
            self._refresh_home_grid()

        if last_track and os.path.exists(last_track):
            track = Track(last_track)
            # Use a slightly delayed load or ensure it doesn't block
            self._play_track(track, start_pos=last_pos)
            self._engine.pause() # Stay paused at startup
        
        # Ensure focus doesn't block
        self._btn_home.setFocus()

    def _apply_startup_theme(self):
        """Apply the full saved theme (stylesheet + background image) on startup."""
        qss_path = resource_path(os.path.join("ui", "styles.qss"))
        from PyQt5.QtWidgets import QApplication
        ThemeManager.apply_theme(QApplication.instance(), qss_path)

        cfg = ThemeManager.load_theme_config()
        img_path = cfg.get("bg_image", "")
        if img_path and os.path.exists(img_path):
            self._bg_widget.setPixmap(QPixmap(img_path))
            self._bg_widget.show()
        else:
            self._bg_widget.setPixmap(QPixmap())
            self._bg_widget.hide()

        self._update_nav_active()


    def _open_settings(self):
        dlg = SettingsDialog(self._lastfm, self)
        dlg.theme_changed.connect(self._on_theme_changed)
        dlg.exec_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        rect = self.centralWidget().rect()
        if hasattr(self, "_bg_widget"):
            self._bg_widget.setGeometry(rect)
        if hasattr(self, "_overlay_widget"):
            self._overlay_widget.setGeometry(rect)

    def keyPressEvent(self, event):
        """Uygulama içi klavye kısayolları."""
        key = event.key()
        
        # Space -> Play/Pause
        if key == Qt.Key_Space:
            self._engine.toggle_pause()
            
        # Left -> -5 seconds
        elif key == Qt.Key_Left:
            self._engine.seek(max(0, self._engine.position - 5))
            
        # Right -> +5 seconds
        elif key == Qt.Key_Right:
            self._engine.seek(min(self._engine.duration, self._engine.position + 5))
            
        # Up -> Volume Up
        elif key == Qt.Key_Up:
            new_vol = min(1.0, self._engine._volume + 0.05)
            self._player_bar._vol_slider.setValue(int(new_vol * 100))
            
        # Down -> Volume Down
        elif key == Qt.Key_Down:
            new_vol = max(0.0, self._engine._volume - 0.05)
            self._player_bar._vol_slider.setValue(int(new_vol * 100))
            
        else:
            super().keyPressEvent(event)

    def _on_theme_changed(self):
        qss_path = resource_path(os.path.join("ui", "styles.qss"))
        from PyQt5.QtWidgets import QApplication
        ThemeManager.apply_theme(QApplication.instance(), qss_path)
        
        # Update background image manually (to avoid QSS inheritance issues)
        cfg = ThemeManager.load_theme_config()
        img_path = cfg.get("bg_image", "")
        if img_path and os.path.exists(img_path):
            self._bg_widget.setPixmap(QPixmap(img_path))
            self._bg_widget.show()
        else:
            self._bg_widget.setPixmap(QPixmap())
            self._bg_widget.hide()

        self._update_nav_active()
        self._player_bar.update_theme_colors()
        
        # Update Logo for new background
        logo_path = resource_path(os.path.join("ui", "logo.png"))
        if os.path.exists(logo_path):
             for label in self.findChildren(QLabel):
                 if label.objectName() == "SidebarLogo":
                     pm = QPixmap(logo_path)
                     pm = _make_transparent(pm)
                     logo_pixmap = _round_pixmap(pm.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation), 24)
                     label.setPixmap(logo_pixmap)

        self._update_nav_active()
        QMessageBox.information(self, I18n.t("theme_applied"), I18n.t("restart_msg"))

    def showEvent(self, event):
        super().showEvent(event)
        # Sync background layers to final window size
        rect = self.centralWidget().rect()
        if hasattr(self, "_bg_widget"):
            self._bg_widget.setGeometry(rect)
        if hasattr(self, "_overlay_widget"):
            self._overlay_widget.setGeometry(rect)
        self._apply_startup_theme()
        
        # Enable Drag and Drop
        self.setAcceptDrops(True)

        if self._smtc is None:
            self._smtc = SimpleSMTC(int(self.winId()), self)
            self._smtc.play_requested.connect(lambda: self._engine.play())
            self._smtc.pause_requested.connect(lambda: self._engine.pause())
            self._smtc.next_requested.connect(self._play_next)
            self._smtc.prev_requested.connect(self._play_prev)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self._library.add_paths(files)
            self._refresh_home_grid()
            QMessageBox.information(self, "LossLess", I18n.t("items_added").replace("{count}", str(len(files))))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self._player_bar.play_pause_clicked.emit()
        super().keyPressEvent(event)

    def _on_ai_progress(self, msg):
        # If in batch mode, prepend the current progress (e.g. [1/12])
        if self._ai_batch_queue and hasattr(self, "_ai_batch_total"):
            current_idx = self._ai_batch_total - len(self._ai_batch_queue)
            msg = f"[{current_idx}/{self._ai_batch_total}] {msg}"
        self._player_bar._stem_popup.set_loading(msg)

    def _on_ai_finished(self, path, success):
        # Update UI first
        if success:
            if self._current_track and self._current_track.path == path:
                pos = self._engine.position
                self._engine.load(path)
                self._engine.seek(pos)
                self._engine.play()
                meta = self._current_track.metadata
                self._player_bar.set_track(meta, meta.cover_art, True)
        
        # Check for next in batch
        if self._ai_batch_queue:
            next_track = self._ai_batch_queue.pop(0)
            self._start_single_ai_separation(next_track)
        else:
            self._is_ai_busy = False
            if not success:
                self._player_bar._stem_popup.set_available(False)
                current_text = self._player_bar._stem_popup.empty_lbl.text()
                if "Hata" not in current_text and "Detay" not in current_text:
                    self._player_bar._stem_popup.empty_lbl.setText("Ayrıştırma başarısız oldu.")

    def _start_album_separation(self, tracks: list):
        """Starts sequential separation for all tracks in an album."""
        # Filter out already separated tracks
        to_separate = []
        for t in tracks:
            base_dir = os.path.dirname(t.path)
            file_name = os.path.basename(t.path).rsplit('.', 1)[0]
            output_dir = os.path.join(base_dir, f"{file_name}_stems")
            if not os.path.exists(output_dir):
                to_separate.append(t)
        
        if not to_separate:
            QMessageBox.information(self, "AI", "Bu albümdeki tüm parçalar zaten ayrıştırılmış.")
            return

        if self._is_ai_busy:
            QMessageBox.warning(self, "AI Meşgul", "Şu anda başka bir ayrıştırma işlemi devam ediyor.")
            return

        self._ai_batch_queue = to_separate
        self._ai_batch_total = len(to_separate)
        self._is_ai_busy = True
        
        # Start the first one
        first_track = self._ai_batch_queue.pop(0)
        self._start_single_ai_separation(first_track)

    def _start_ai_separation(self):
        """Original single-track trigger from player bar."""
        if not self._current_track: return
        if self._is_ai_busy: return
        self._is_ai_busy = True
        self._ai_batch_queue = [] # Ensure no batch queue
        self._start_single_ai_separation(self._current_track)

    def _start_single_ai_separation(self, track: Track):
        """Internal method to start separation for a specific track."""
        self._ai_thread = AISeparator(track.path)
        self._ai_thread.progress.connect(self._on_ai_progress)
        self._ai_thread.finished.connect(self._on_ai_finished)
        self._ai_thread.start()
        
        # Open the popup to show progress if it's the current track or first of batch
        self._player_bar._stem_popup.set_loading("Lokal İşlem Hazırlanıyor...")
        if not self._player_bar._stem_popup.isVisible():
            self._player_bar._stem_popup.show_above(self._player_bar._ai_btn)

    def _on_stems_updated(self, config: dict):
        """Called when user moves mixer sliders or toggles stems."""
        self._engine.set_stem_volumes(config)
        # Update UI feedback for bit-perfect mode
        all_max = all(v >= 0.99 for v in config.values())
        self._player_bar.update_lossless_status(all_max)

    def closeEvent(self, event):
        cfg = LastFmService.load_config()
        if self._current_track:
            cfg["last_track"] = self._current_track.path
            cfg["last_position"] = self._engine.position
        LastFmService.save_config(cfg)
        self._engine.stop()
        event.accept()
