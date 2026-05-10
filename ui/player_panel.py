"""
player_panel.py — Next-Gen Professional UI Views
"""
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QRectF, QPointF
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QScrollArea, QFrame, QGridLayout, QStackedWidget,
    QSizePolicy, QListWidget, QListWidgetItem, QMenu, QAction, QStyle,
    QProgressBar, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor, QFont, QIcon, QPen, QLinearGradient, QBrush
from PyQt5.QtSvg import QSvgRenderer

from core.metadata import TrackMetadata
from core.theme_manager import ThemeManager
from core.i18n import I18n

def _round_pixmap(pixmap: QPixmap, radius: int = 4) -> QPixmap:
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded

# ── SVG Icons ───────────────────────────────────────────────────────
ICONS = {
    "home": "M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z",
    "stats": "M5 9.2h3V19H5zM10.6 5h2.8v14h-2.8zm5.6 8H19v6h-2.8z",
    "add": "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "clear": "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
    "settings": "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z",
    "play": "M8 5v14l11-7z",
    "pause": "M6 19h4V5H6v14zm8-14v14h4V5h-4z",
    "prev": "M6 6h2v12H6zm3.5 6L18 18V6z",
    "next": "M6 18l8.5-6L6 6v12zM16 6v12h2V6z",
    "shuffle": "M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z",
    "repeat": "M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z",
    "search": "M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "volume": "M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z",
    "ai": "M21 16.5C21 16.88 20.79 17.21 20.47 17.38L12.57 21.82C12.41 21.94 12.21 22 12 22C11.79 22 11.59 21.94 11.43 21.82L3.53 17.38C3.21 17.21 3 16.88 3 16.5V7.5C3 7.12 3.21 6.79 3.53 6.62L11.43 2.18C11.59 2.06 11.79 2 12 2C12.21 2 12.41 2.06 12.57 2.18L20.47 6.62C20.79 6.79 21 7.12 21 7.5V16.5ZM12 4.15L5 8.09V15.91L12 19.85L19 15.91V8.09L12 4.15ZM12 12.5C10.62 12.5 9.5 11.38 9.5 10C9.5 8.62 10.62 7.5 12 7.5C13.38 7.5 14.5 8.62 14.5 10C14.5 11.38 13.38 12.5 12 12.5Z",
    "help": "M11 18h2v-2h-2v2zm1-16C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-2.21 0-4 1.79-4 4h2c0-1.1.9-2 2-2s2 .9 2 2c0 2-3 1.75-3 5h2c0-2.25 3-2.5 3-5 0-2.21-1.79-4-4-4z",
    "github": "M12 2C6.477 2 2 6.477 2 12c0 4.419 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12c0-5.523-4.477-10-10-10z",
    "refresh": "M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z",
    "music_note": "M12 3v10.55c-.59-.34-1.27-.55-2-.55C7.79 13 6 14.79 6 17s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"
}

def get_icon(name: str, color: str = "#FFFFFF", size: int = 24) -> QIcon:
    if name not in ICONS: return QIcon()
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    svg_data = f'<svg viewBox="0 0 24 24" fill="{color}"><path d="{ICONS[name]}"/></svg>'
    renderer = QSvgRenderer(svg_data.encode())
    renderer.render(painter)
    painter.end()
    return QIcon(pm)

def _get_dominant_color(pixmap: QPixmap) -> QColor:
    img = pixmap.toImage().scaled(64, 64, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    r, g, b = 0, 0, 0
    count = img.width() * img.height()
    for y in range(img.height()):
        for x in range(img.width()):
            c = QColor(img.pixel(x, y))
            r += c.red()
            g += c.green()
            b += c.blue()
    return QColor(r // count, g // count, b // count)

def _default_cover(size: int) -> QPixmap:
    theme = ThemeManager.load_theme_config()
    card_bg = theme.get("card_bg", "#181818")
    primary = theme.get("primary_color", "#1DB954")
    pm = QPixmap(size, size)
    pm.fill(QColor(card_bg).darker(110))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    svg_data = f'<svg viewBox="0 0 24 24" fill="{primary}" opacity="0.4"><path d="{ICONS["music_note"]}"/></svg>'
    renderer = QSvgRenderer(svg_data.encode())
    icon_size = int(size * 0.4)
    offset = (size - icon_size) // 2
    from PyQt5.QtCore import QRectF
    renderer.render(painter, QRectF(offset, offset, icon_size, icon_size))
    painter.end()
    return _round_pixmap(pm)

def _add_text_halo(label, text_color: str = "#FFFFFF", radius: int = 3):
    from PyQt5.QtWidgets import QGraphicsDropShadowEffect
    from PyQt5.QtGui import QColor as _C
    c = _C(text_color)
    brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
    shadow_color = _C(255, 255, 255, 160) if brightness < 128 else _C(0, 0, 0, 160)
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(radius)
    effect.setColor(shadow_color)
    effect.setOffset(0, 0)
    label.setGraphicsEffect(effect)

# ── Clickable UI Elements ──────────────────────────────────────────
class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
            self.setValue(val)
            self.sliderReleased.emit()
        super().mousePressEvent(event)

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

class StemSelectorPopup(QFrame):
    stems_updated = pyqtSignal(dict)
    start_separation = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(240)
        self.active_stems = {"vocals": True, "drums": True, "bass": True, "other": True}
        self._is_available = False
        self._is_loading = False
        self._build_ui()

    def _build_ui(self):
        if self.layout():
            QWidget().setLayout(self.layout()) # Reparent old layout to a temporary widget for deletion
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)
        theme = ThemeManager.load_theme_config()
        bg = theme.get("bottom_bg", "#121212")
        alpha = theme.get("bot_opacity", 90)
        from PyQt5.QtGui import QColor
        c = QColor(bg)
        safe_alpha = max(alpha, 85) / 100.0 if alpha < 50 else alpha / 100.0
        rgba = f"rgba({c.red()}, {c.green()}, {c.blue()}, {safe_alpha})"
        self.txt_color = ThemeManager.get_panel_text_color(bg)
        self.primary = theme.get("primary_color", "#FF85A1")
        self.setStyleSheet(f"""
            QFrame {{ background-color: {rgba}; border: 2px solid {self.primary}44; border-radius: 16px; }}
            QLabel {{ color: {self.txt_color}; font-weight: 800; font-size: 11px; letter-spacing: 1px; background: transparent; margin-bottom: 4px; }}
            QPushButton#StemBtn {{ background: rgba(128, 128, 128, 0.1); border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 8px; padding: 8px; text-align: left; color: {self.txt_color}; font-size: 13px; font-weight: 500; }}
            QPushButton#StemBtn:checked {{ background: {self.primary}; color: white; border: none; }}
            QPushButton#ActionBtn {{ background: {self.primary}22; border: 1px solid {self.primary}44; border-radius: 8px; padding: 10px; color: {self.primary}; font-weight: 700; font-size: 12px; }}
            QPushButton#ActionBtn:hover {{ background: {self.primary}44; }}
        """)
        self.header = QLabel("AI NEURAL MIXER")
        self.header.setStyleSheet(f"font-size: 14px; color: {self.primary}; font-weight: 900; letter-spacing: 2px; margin-bottom: 12px;")
        self.main_layout.addWidget(self.header)
        self.stem_container = QWidget()
        self.stem_container.setStyleSheet("background: transparent; border: none;")
        self.stem_layout = QHBoxLayout(self.stem_container)
        self.stem_layout.setContentsMargins(0,0,0,0)
        self.stem_layout.setSpacing(10)
        self.faders = {}
        self.buttons = {}
        stem_icons = {"vocals": "🎤", "drums": "🥁", "bass": "🎸", "other": "🎹"}
        for stem, icon in stem_icons.items():
            strip = QFrame()
            strip.setObjectName("MixerStrip")
            strip.setStyleSheet("QFrame#MixerStrip { background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 8px; }")
            strip_v = QVBoxLayout(strip)
            strip_v.setContentsMargins(4, 4, 4, 4)
            strip_v.setSpacing(8)
            meter = QFrame()
            meter.setFixedHeight(4)
            meter.setStyleSheet(f"background: qlineargradient(x1:0, x2:1, stop:0 {self.primary}, stop:0.8 {self.primary}88); border-radius: 2px;")
            strip_v.addWidget(meter)
            lbl = QLabel(icon)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px;")
            strip_v.addWidget(lbl)
            slider = QSlider(Qt.Vertical)
            slider.setRange(0, 100); slider.setValue(100); slider.setFixedHeight(120)
            slider.setStyleSheet(f"QSlider::groove:vertical {{ background: rgba(255,255,255,0.05); width: 4px; border-radius: 2px; }} QSlider::handle:vertical {{ background: {self.primary}; border: 2px solid white; height: 14px; margin: 0 -5px; border-radius: 7px; }}")
            slider.valueChanged.connect(self._on_toggle)
            strip_v.addWidget(slider, 0, Qt.AlignCenter)
            self.faders[stem] = slider
            btn = QPushButton("ON")
            btn.setObjectName("StemBtn"); btn.setCheckable(True); btn.setChecked(True); btn.setFixedSize(36, 24); btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(self._on_toggle)
            strip_v.addWidget(btn, 0, Qt.AlignCenter)
            self.buttons[stem] = btn
            self.stem_layout.addWidget(strip)
        self.main_layout.addWidget(self.stem_container)
        self.empty_widget = QFrame()
        self.empty_widget.setObjectName("ProcessingCard")
        self.empty_widget.setStyleSheet(f"QFrame#ProcessingCard {{ background: rgba(0, 0, 0, 0.4); border: 1px solid {self.primary}44; border-radius: 10px; padding: 15px; }}")
        empty_l = QVBoxLayout(self.empty_widget)
        empty_l.setContentsMargins(10, 10, 10, 10); empty_l.setSpacing(12)
        self.empty_lbl = QLabel("Bu parça henüz ayrıştırılmadı.")
        self.empty_lbl.setWordWrap(True); self.empty_lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {self.txt_color}; background: transparent;"); self.empty_lbl.setAlignment(Qt.AlignCenter)
        self.loading_bar = QProgressBar()
        self.loading_bar.setFixedHeight(4); self.loading_bar.setRange(0, 0); self.loading_bar.setTextVisible(False)
        self.loading_bar.setStyleSheet(f"QProgressBar {{ background: rgba(255,255,255,0.1); border: none; border-radius: 2px; }} QProgressBar::chunk {{ background: {self.primary}; border-radius: 2px; }}")
        self.loading_bar.hide()
        self.start_btn = QPushButton("AI İLE KANALLARA AYIR")
        self.start_btn.setObjectName("ActionBtn"); self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_separation.emit)
        empty_l.addWidget(self.empty_lbl); empty_l.addWidget(self.loading_bar); empty_l.addWidget(self.start_btn)
        self.main_layout.addWidget(self.empty_widget)

    def set_available(self, available: bool):
        self._is_available = available; self._is_loading = False
        self.stem_container.setVisible(available); self.empty_widget.setVisible(not available); self.loading_bar.hide()
        if not available: self.start_btn.setVisible(True)

    def set_loading(self, text: str):
        self._is_loading = True; self.stem_container.hide(); self.empty_widget.show()
        self.empty_lbl.setText(text); self.loading_bar.show(); self.start_btn.hide()
        if "%" in text:
            import re
            match = re.search(r"(\d+)", text)
            if match:
                val = int(match.group(1))
                self.loading_bar.setRange(0, 100); self.loading_bar.setValue(val)
        elif "Aşama" in text:
            if "1/4" in text: self.loading_bar.setValue(25)
            elif "2/4" in text: self.loading_bar.setValue(50)
            elif "3/4" in text: self.loading_bar.setValue(75)
            elif "4/4" in text: self.loading_bar.setValue(95)
        else: self.loading_bar.setRange(0, 0)

    def _on_toggle(self):
        config = {}
        for stem, slider in self.faders.items():
            btn = self.buttons[stem]
            vol = slider.value() / 100.0 if btn.isChecked() else 0.0
            config[stem] = vol
            btn.setText("ON" if btn.isChecked() else "MUTE")
            btn.setStyleSheet(f"color: {'white' if btn.isChecked() else '#666'}; font-weight: 800;")
        self.stems_updated.emit(config)

    def show_above(self, widget):
        pos = widget.mapToGlobal(widget.rect().topLeft())
        self.move(pos.x() - (self.width() // 2) + (widget.width() // 2), pos.y() - self.sizeHint().height() - 10)
        self.show()

# ── Track Row Widget ────────────────────────────────────────────────
class TrackRowWidget(QWidget):
    play_clicked = pyqtSignal(object)
    remove_requested = pyqtSignal(object)
    play_next_requested = pyqtSignal(object)
    add_queue_requested = pyqtSignal(object)

    def __init__(self, index: int, track, parent=None):
        super().__init__(parent)
        self.setObjectName("TrackRowWidget")
        self.track = track
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 16, 8); layout.setSpacing(16)
        theme = ThemeManager.load_theme_config()
        sidebar_bg = theme.get("sidebar_bg", ThemeManager.DEFAULT_SIDEBAR_BG)
        txt_color = ThemeManager.get_panel_text_color(sidebar_bg)
        sub_color = ThemeManager.get_panel_text_color(sidebar_bg, is_sub=True)
        self.indicator = QFrame(); self.indicator.setObjectName("ActiveIndicator"); self.indicator.setFixedWidth(4); self.indicator.setFixedHeight(24); self.indicator.setVisible(False)
        self.idx_label = QLabel(str(index)); self.idx_label.setFixedWidth(24); self.idx_label.setStyleSheet(f"color: {sub_color}; font-weight: 700; background: transparent;")
        self.play_btn = QPushButton(); self.play_btn.setFixedSize(28, 28); self.play_btn.setCursor(Qt.PointingHandCursor); self.play_btn.setIcon(get_icon("play", txt_color, 16)); self.play_btn.setStyleSheet("background: transparent; border: none;")
        self.play_btn.clicked.connect(lambda: self.play_clicked.emit(self.track))
        self.title_label = QLabel(track.metadata.title); self.title_label.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {txt_color}; background: transparent;")
        _add_text_halo(self.title_label, txt_color, radius=4)
        self.duration_label = QLabel(track.metadata.duration_str); self.duration_label.setStyleSheet(f"color: {sub_color}; font-family: monospace; font-size: 13px; background: transparent;"); self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.indicator); layout.addWidget(self.idx_label); layout.addWidget(self.play_btn); layout.addWidget(self.title_label, 1); layout.addWidget(self.duration_label)
        self.setContextMenuPolicy(Qt.CustomContextMenu); self.customContextMenuRequested.connect(self._show_menu)

    def set_active(self, active: bool):
        self.indicator.setVisible(active); self.idx_label.setVisible(not active)
        primary_color = ThemeManager.get_primary_color()
        if active:
            self.title_label.setStyleSheet(f"font-weight: 700; color: {primary_color}; background: transparent;")
            _add_text_halo(self.title_label, primary_color, radius=4)
        else:
            theme = ThemeManager.load_theme_config()
            sidebar_bg = theme.get("sidebar_bg", ThemeManager.DEFAULT_SIDEBAR_BG)
            txt_color = ThemeManager.get_panel_text_color(sidebar_bg)
            self.title_label.setStyleSheet(f"font-weight: 600; color: {txt_color}; background: transparent;")
            _add_text_halo(self.title_label, txt_color, radius=4)

    def _show_menu(self, pos):
        menu = QMenu(self)
        play_next = menu.addAction(I18n.t("play_next"))
        add_queue = menu.addAction(I18n.t("add_to_queue"))
        menu.addSeparator()
        remove_act = menu.addAction(I18n.t("remove_from_library"))
        act = menu.exec_(self.mapToGlobal(pos))
        if act == play_next: self.play_next_requested.emit(self.track)
        elif act == add_queue: self.add_queue_requested.emit(self.track)
        elif act == remove_act: self.remove_requested.emit(self.track)

# ── Album Card ────────────────────────────────────────────────────────
class AlbumCard(QFrame):
    clicked = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    play_requested = pyqtSignal(str)

    def __init__(self, album_name: str, artist: str, cover_bytes: bytes | None, parent=None):
        super().__init__(parent)
        self.setObjectName("AlbumCard"); self.setMinimumSize(180, 280); self.setMaximumWidth(220)
        self.album_name = album_name; self.artist = artist
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 16, 16, 16); layout.setSpacing(8)
        self.art_label = QLabel(); self.art_label.setObjectName("AlbumCardArt"); self.art_label.setFixedSize(168, 168); self.art_label.setAlignment(Qt.AlignCenter)
        if cover_bytes:
            img = QImage.fromData(cover_bytes)
            if not img.isNull():
                pm = QPixmap.fromImage(img).scaled(168, 168, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                self.art_label.setPixmap(_round_pixmap(pm))
            else: self.art_label.setPixmap(_default_cover(168))
        else: self.art_label.setPixmap(_default_cover(168))
        self.title_label = QLabel(album_name); self.title_label.setObjectName("AlbumCardTitle"); self.title_label.setWordWrap(True); self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.artist_label = QLabel(artist); self.artist_label.setObjectName("AlbumCardArtist"); self.artist_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.play_btn = QPushButton(); self.play_btn.setFixedSize(48, 48); self.play_btn.setCursor(Qt.PointingHandCursor); self.play_btn.setObjectName("HoverPlayBtn"); self.play_btn.setIcon(get_icon("play", "#000000", 32)); self.play_btn.setIconSize(QSize(32, 32)); self.play_btn.setVisible(False)
        primary_color = ThemeManager.get_primary_color(); primary_hover = ThemeManager.get_primary_hover_color()
        self.play_btn.setStyleSheet(f"QPushButton#HoverPlayBtn {{ background-color: {primary_color}; color: #000000; border-radius: 24px; }} QPushButton#HoverPlayBtn:hover {{ background-color: {primary_hover}; }}")
        self.play_btn.clicked.connect(lambda: self.play_requested.emit(self.album_name))
        layout.addWidget(self.art_label, 0, Qt.AlignCenter); layout.addSpacing(4); layout.addWidget(self.title_label); layout.addWidget(self.artist_label); layout.addStretch()
        self._overlay_layout = QVBoxLayout(self.art_label); self._overlay_layout.setContentsMargins(0, 0, 8, 8); self._overlay_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom); self._overlay_layout.addWidget(self.play_btn)
        self.setContextMenuPolicy(Qt.CustomContextMenu); self.customContextMenuRequested.connect(self._show_menu)

    def enterEvent(self, event): self.play_btn.setVisible(True); super().enterEvent(event)
    def leaveEvent(self, event): self.play_btn.setVisible(False); super().leaveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.album_name)

    def _show_menu(self, pos):
        menu = QMenu(self)
        remove_act = menu.addAction(I18n.t("remove_album_from_library"))
        remove_act.triggered.connect(lambda: self.remove_requested.emit(self.album_name))
        menu.exec_(self.mapToGlobal(pos))

# ── Quick Pick Card ───────────────────────────────────────────────────
class QuickPickCard(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, track, parent=None):
        super().__init__(parent)
        self.setObjectName("QuickPickCard"); self.track = track; self.setFixedHeight(64); self.setMinimumWidth(200); self.setCursor(Qt.PointingHandCursor)
        layout = QHBoxLayout(self); layout.setContentsMargins(8, 8, 12, 8); layout.setSpacing(12)
        ART_SIZE = 48
        self.art_label = QLabel(); self.art_label.setFixedSize(ART_SIZE, ART_SIZE); self.art_label.setAlignment(Qt.AlignCenter)
        cover = track.metadata.cover_art
        if cover:
            img = QImage.fromData(cover)
            if not img.isNull():
                pm = QPixmap.fromImage(img); side = min(pm.width(), pm.height()); pm = pm.copy((pm.width()-side)//2, (pm.height()-side)//2, side, side); pm = pm.scaled(ART_SIZE, ART_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation); self.art_label.setPixmap(_round_pixmap(pm, 8))
            else: self.art_label.setPixmap(_default_cover(ART_SIZE))
        else: self.art_label.setPixmap(_default_cover(ART_SIZE))
        info_v = QVBoxLayout(); info_v.setSpacing(2)
        self.title_lbl = QLabel(track.metadata.title); theme = ThemeManager.load_theme_config(); txt_color = ThemeManager.get_smart_text_color(theme.get("card_bg", "#181818"), theme.get("card_opacity", 100)); self.title_lbl.setStyleSheet(f"font-weight: 700; color: {txt_color}; font-size: 14px;")
        font_metrics = self.title_lbl.fontMetrics(); elided_title = font_metrics.elidedText(track.metadata.title, Qt.ElideRight, 180); self.title_lbl.setText(elided_title)
        self.artist_lbl = QLabel(track.metadata.artist); sub_color = ThemeManager.get_smart_text_color(theme.get("card_bg", "#181818"), theme.get("card_opacity", 100), True); self.artist_lbl.setStyleSheet(f"color: {sub_color}; font-size: 12px; font-weight: 500;")
        info_v.addWidget(self.title_lbl); info_v.addWidget(self.artist_lbl); info_v.addStretch()
        layout.addWidget(self.art_label); layout.addLayout(info_v, 1)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.clicked.emit(self.track)

# ── Home View (Album Grid) ───────────────────────────────────────────
class HomeView(QWidget):
    album_selected = pyqtSignal(str)
    album_remove_requested = pyqtSignal(str)
    album_play_requested = pyqtSignal(str)
    track_selected = pyqtSignal(object)
    quick_pick_played = pyqtSignal(object)
    quick_pick_play_all = pyqtSignal()
    quick_pick_refresh = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeView"); self._albums_data = []; self._current_cols = 0
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0); layout.setSpacing(0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_container = QWidget(); self.main_layout = QVBoxLayout(self.main_container); self.main_layout.setContentsMargins(40, 40, 40, 40); self.main_layout.setSpacing(48)
        quick_header_row = QHBoxLayout(); qh_lbl = QLabel(I18n.t("quick_picks")); qh_lbl.setStyleSheet("font-size: 28px; font-weight: 900;")
        self.btn_play_all = QPushButton(I18n.t("play_all")); primary_color = ThemeManager.get_primary_color(); self.btn_play_all.setStyleSheet(f"background: transparent; color: {primary_color}; border: 1px solid {primary_color}; border-radius: 12px; padding: 4px 12px; font-weight: 500; font-size: 11px;"); self.btn_play_all.setCursor(Qt.PointingHandCursor); self.btn_play_all.clicked.connect(self.quick_pick_play_all.emit)
        self.btn_refresh = QPushButton(); self.btn_refresh.setFixedSize(32, 32); sub_color = ThemeManager.get_subtext_color(); self.btn_refresh.setIcon(get_icon("refresh", sub_color, 18)); self.btn_refresh.setStyleSheet("background: transparent; border: 1px solid rgba(128,128,128,0.2); border-radius: 16px;"); self.btn_refresh.setCursor(Qt.PointingHandCursor); self.btn_refresh.clicked.connect(self.quick_pick_refresh.emit)
        quick_header_row.addWidget(qh_lbl); quick_header_row.addStretch(); quick_header_row.addWidget(self.btn_refresh); quick_header_row.addWidget(self.btn_play_all)
        self.quick_picks_grid = QGridLayout(); self.quick_picks_grid.setSpacing(12); self.quick_picks_grid.setContentsMargins(0, 0, 0, 0)
        for _c in range(5): self.quick_picks_grid.setColumnStretch(_c, 1)
        self.quick_grid_container = QWidget(); self.quick_grid_container.setLayout(self.quick_picks_grid)
        self.quick_picks_widget = QWidget(); quick_v = QVBoxLayout(self.quick_picks_widget); quick_v.setContentsMargins(0, 0, 0, 0); quick_v.addLayout(quick_header_row); quick_v.addSpacing(24); quick_v.addWidget(self.quick_grid_container)
        self.main_layout.addWidget(self.quick_picks_widget); self.main_layout.addSpacing(48)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);"); sep.setFixedHeight(1); self.main_layout.addWidget(sep); self.main_layout.addSpacing(48)
        alb_lbl = QLabel(I18n.t("your_library")); alb_lbl.setStyleSheet("font-size: 28px; font-weight: 900;"); self.main_layout.addWidget(alb_lbl)
        self.grid_container = QWidget(); self.grid_layout = QGridLayout(self.grid_container); self.grid_layout.setSpacing(32); self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop); self.main_layout.addWidget(self.grid_container); self.main_layout.addStretch(); self.scroll.setWidget(self.main_container); layout.addWidget(self.scroll)

    def update_quick_picks(self, tracks: list):
        if not tracks: self.quick_picks_widget.hide(); return
        self.quick_picks_widget.show()
        while self.quick_picks_grid.count():
            item = self.quick_picks_grid.takeAt(0); w = item.widget()
            if w: w.setParent(None); w.deleteLater()
        def _has_real_meta(t):
            title = (t.metadata.title or "").strip(); artist = (t.metadata.artist or "").strip(); bad = {"unknown title", "unknown", ""}
            return title.lower() not in bad and artist.lower() not in {"unknown artist", "unknown", ""}
        real_tracks = [t for t in tracks if _has_real_meta(t)]
        if not real_tracks: self.quick_picks_widget.hide(); return
        MAX_CARDS = 10; row, col = 0, 0
        for track in real_tracks[:MAX_CARDS]:
            card = QuickPickCard(track); card.clicked.connect(self.quick_pick_played.emit); self.quick_picks_grid.addWidget(card, row, col); col += 1
            if col >= 5: col = 0; row += 1

    def update_albums(self, albums_data: list): self._albums_data = albums_data; self._refresh_grid(force=True)
    def _refresh_grid(self, force=False):
        width = self.width() - 64; card_w = 200 + 32; cols = max(1, width // card_w)
        if not force and cols == self._current_cols: return
        self._current_cols = cols
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0); w = item.widget()
            if w: w.setParent(None); w.deleteLater()
        row, col = 0, 0
        for album in self._albums_data:
            card = AlbumCard(album['name'], album['artist'], album['cover']); card.clicked.connect(self.album_selected.emit); card.remove_requested.connect(self.album_remove_requested.emit); card.play_requested.connect(self.album_play_requested.emit); self.grid_layout.addWidget(card, row, col); col += 1
            if col >= cols: col = 0; row += 1
    def resizeEvent(self, event): super().resizeEvent(event); self._refresh_grid()

# ── Search View ──────────────────────────────────────────────────────
class SearchView(QWidget):
    album_selected = pyqtSignal(str)
    track_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchView"); self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(24, 16, 24, 16); outer.setSpacing(0)
        self._panel = QFrame(); self._panel.setObjectName("SearchPanel"); self._panel.setAttribute(Qt.WA_StyledBackground, True); self._apply_panel_style()
        panel_layout = QVBoxLayout(self._panel); panel_layout.setContentsMargins(0, 0, 0, 0); panel_layout.setSpacing(0)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); self.scroll.setStyleSheet("background: transparent;")
        content = QWidget(); content.setStyleSheet("background: transparent;"); self.content_layout = QVBoxLayout(content); self.content_layout.setContentsMargins(28, 24, 28, 24); self.content_layout.setSpacing(24)
        self.title_lbl = QLabel(I18n.t("search_results")); self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; background: transparent;")
        self.content_layout.addWidget(self.title_lbl)
        div = QFrame(); div.setFrameShape(QFrame.HLine); div.setStyleSheet("background: rgba(128,128,128,0.15); max-height: 1px;"); self.content_layout.addWidget(div)
        self.tracks_title = QLabel(I18n.t("tracks")); self.tracks_title.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 1px; color: rgba(128,128,128,0.8); background: transparent; margin-top: 4px;")
        self.content_layout.addWidget(self.tracks_title)
        self.track_list = QListWidget(); self.track_list.setFrameShape(QFrame.NoFrame); self.track_list.setStyleSheet("background: transparent; border: none;"); self.track_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.content_layout.addWidget(self.track_list)
        self.albums_title = QLabel(I18n.t("albums")); self.albums_title.setStyleSheet("font-size: 13px; font-weight: 700; letter-spacing: 1px; color: rgba(128,128,128,0.8); background: transparent; margin-top: 8px;")
        self.content_layout.addWidget(self.albums_title)
        self.album_grid = QGridLayout(); self.album_grid.setSpacing(16); self.album_grid_container = QWidget(); self.album_grid_container.setStyleSheet("background: transparent;"); self.album_grid_container.setLayout(self.album_grid); self.content_layout.addWidget(self.album_grid_container); self.content_layout.addStretch(); self.scroll.setWidget(content); panel_layout.addWidget(self.scroll); outer.addWidget(self._panel)

    def _apply_panel_style(self):
        theme = ThemeManager.load_theme_config(); sidebar_bg = theme.get("sidebar_bg", "#FFE4E9"); side_alpha = theme.get("side_opacity", 100)
        from PyQt5.QtGui import QColor
        c = QColor(sidebar_bg); rgba = f"rgba({c.red()},{c.green()},{c.blue()},{side_alpha/100.0:.2f})"
        text_color = ThemeManager.get_panel_text_color(sidebar_bg)
        self._panel.setStyleSheet(f"QFrame#SearchPanel {{ background-color: {rgba}; border-radius: 18px; border: 1px solid rgba(255,255,255,0.18); color: {text_color}; }} QFrame#SearchPanel QLabel {{ color: {text_color}; background: transparent; }} QFrame#SearchPanel QListWidget {{ color: {text_color}; }} QFrame#SearchPanel QListWidget::item {{ color: {text_color}; }}")

    def showEvent(self, event): super().showEvent(event); self._apply_panel_style()
    def set_results(self, query: str, tracks: list):
        self.title_lbl.setText(f"Results for \"{query}\""); self._apply_panel_style()
        self.track_list.clear()
        if not tracks: self.track_list.hide(); self.tracks_title.hide()
        else:
            self.track_list.show(); self.tracks_title.show(); self.track_list.setFixedHeight(min(len(tracks), 8) * 56)
            for i, track in enumerate(tracks[:20]):
                item = QListWidgetItem(self.track_list); item.setSizeHint(QSize(0, 56)); row = TrackRowWidget(i + 1, track); row.play_clicked.connect(self.track_selected.emit); self.track_list.setItemWidget(item, row)
        while self.album_grid.count():
            item = self.album_grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        albums = {}
        for track in tracks:
            alb = track.metadata.album or I18n.t("unknown_album")
            if alb not in albums: albums[alb] = {'name': alb, 'artist': track.metadata.artist, 'cover': track.metadata.cover_art}
        if not albums: self.albums_title.hide()
        else:
            self.albums_title.show(); row, col = 0, 0
            for album in list(albums.values())[:9]:
                card = AlbumCard(album['name'], album['artist'], album['cover']); card.clicked.connect(self.album_selected.emit); card.play_requested.connect(lambda name: self.album_selected.emit(name)); self.album_grid.addWidget(card, row, col); col += 1
                if col >= 3: col = 0; row += 1

# ── Album Detail View ───────────────────────────────────────────────
class AlbumDetailView(QWidget):
    track_selected = pyqtSignal(object); track_remove_requested = pyqtSignal(object); 
    play_next_requested = pyqtSignal(object); add_queue_requested = pyqtSignal(object)
    separate_album_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("AlbumDetailView"); self._tracks = []; self._build_ui()
    
    def _build_ui(self):
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(0, 0, 0, 0); self.layout.setSpacing(0)
        self.header_frame = QFrame(); self.header_frame.setObjectName("AlbumDetailHeader"); self.header_frame.setFixedHeight(220)
        header_l = QHBoxLayout(self.header_frame); header_l.setContentsMargins(32, 24, 32, 24); header_l.setSpacing(28)
        self.art_label = QLabel(); self.art_label.setFixedSize(168, 168); self.art_label.setObjectName("AlbumDetailArt")
        info_v = QVBoxLayout(); info_v.setSpacing(6); info_v.setAlignment(Qt.AlignVCenter)
        
        type_lbl = QLabel(I18n.t("album").upper()); type_lbl.setStyleSheet("font-size: 10px; font-weight: 800; letter-spacing: 2px; opacity: 0.6;")
        self.title_label = QLabel("Album Title"); self.title_label.setObjectName("AlbumDetailTitle"); self.title_label.setWordWrap(True)
        
        info_sub = QHBoxLayout(); info_sub.setSpacing(12)
        self.info_label = QLabel("Artist • Year • Track Count"); self.info_label.setObjectName("AlbumDetailInfo")
        
        self.sep_btn = QPushButton("✨ Tümünü Ayrıştır")
        self.sep_btn.setCursor(Qt.PointingHandCursor)
        primary = ThemeManager.get_primary_color()
        self.sep_btn.setStyleSheet(f"""
            QPushButton {{
                background: {primary}22;
                border: 1px solid {primary}44;
                border-radius: 12px;
                padding: 6px 12px;
                color: {primary};
                font-weight: 700;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {primary}44;
            }}
        """)
        self.sep_btn.clicked.connect(lambda: self.separate_album_requested.emit(self._tracks))
        
        info_sub.addWidget(self.info_label); info_sub.addWidget(self.sep_btn); info_sub.addStretch()
        
        info_v.addWidget(type_lbl); info_v.addWidget(self.title_label); info_v.addLayout(info_sub)
        header_l.addWidget(self.art_label); header_l.addLayout(info_v, 1)
        
        self._track_panel = QFrame(); self._track_panel.setObjectName("AlbumTrackPanel"); self._track_panel.setAttribute(Qt.WA_StyledBackground, True)
        track_panel_layout = QVBoxLayout(self._track_panel); track_panel_layout.setContentsMargins(0, 0, 0, 0); track_panel_layout.setSpacing(0)
        self.track_list = QListWidget(); self.track_list.setFrameShape(QFrame.NoFrame); self.track_list.setStyleSheet("background: transparent; border: none;"); track_panel_layout.addWidget(self.track_list)
        self.layout.addWidget(self.header_frame); self.layout.addWidget(self._track_panel, 1)

    def _apply_track_panel_style(self):
        theme = ThemeManager.load_theme_config(); sidebar_bg = theme.get("sidebar_bg", "#FFE4E9"); side_alpha = theme.get("side_opacity", 100)
        from PyQt5.QtGui import QColor as _QC
        c = _QC(sidebar_bg); rgba = f"rgba({c.red()},{c.green()},{c.blue()},{side_alpha/100.0:.2f})"
        text_color = ThemeManager.get_panel_text_color(sidebar_bg)
        self._track_panel.setStyleSheet(f"QFrame#AlbumTrackPanel {{ background-color: {rgba}; border-top: 1px solid rgba(255,255,255,0.1); color: {text_color}; }} QFrame#AlbumTrackPanel QLabel {{ color: {text_color}; background: transparent; }} QFrame#AlbumTrackPanel QListWidget {{ color: {text_color}; }} QFrame#AlbumTrackPanel QListWidget::item {{ color: {text_color}; }}")

    def set_album(self, name: str, artist: str, cover_bytes: bytes | None, tracks: list, current_track=None):
        self._tracks = tracks
        self._apply_track_panel_style(); self.title_label.setText(name)
        if len(name) > 25: self.title_label.setStyleSheet("font-size: 28px; font-weight: 900; background: transparent;")
        elif len(name) > 15: self.title_label.setStyleSheet("font-size: 38px; font-weight: 900; background: transparent;")
        else: self.title_label.setStyleSheet("font-size: 48px; font-weight: 900; background: transparent;")
        self.info_label.setText(f"{artist} • {len(tracks)} {I18n.t('tracks')}"); self.info_label.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent; opacity: 0.7;")
        dom_color = QColor(24, 24, 24)
        if cover_bytes:
            img = QImage.fromData(cover_bytes)
            if not img.isNull():
                pm = QPixmap.fromImage(img).scaled(168, 168, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation); self.art_label.setPixmap(_round_pixmap(pm, 12)); dom_color = _get_dominant_color(pm)
            else: self.art_label.setPixmap(_default_cover(168))
        else: self.art_label.setPixmap(_default_cover(168))
        bg_color = dom_color.name(); self.header_frame.setStyleSheet(f"QFrame#AlbumDetailHeader {{ background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg_color}, stop:1 rgba(0,0,0,0)); }}")
        self.track_list.clear()
        for i, track in enumerate(tracks):
            item = QListWidgetItem(self.track_list); item.setData(Qt.UserRole, track); item.setSizeHint(QSize(0, 56)); row_widget = TrackRowWidget(i + 1, track); row_widget.play_clicked.connect(self.track_selected.emit); row_widget.remove_requested.connect(self.track_remove_requested.emit); row_widget.play_next_requested.connect(self.play_next_requested.emit); row_widget.add_queue_requested.connect(self.add_queue_requested.emit)
            if current_track and track.path == current_track.path: row_widget.set_active(True)
            self.track_list.setItemWidget(item, row_widget)

# ── Now Playing View ───────────────────────────────────────────────
class NowPlayingView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("NowPlayingView"); self._build_ui()
    def _build_ui(self):
        root = QHBoxLayout(self); root.setContentsMargins(24, 16, 24, 16); root.setSpacing(16)
        self._info_panel = QFrame(); self._info_panel.setObjectName("NowPlayingInfoPanel"); self._info_panel.setAttribute(Qt.WA_StyledBackground, True); self._info_panel.setFixedWidth(280)
        info_layout = QVBoxLayout(self._info_panel); info_layout.setContentsMargins(24, 28, 24, 28); info_layout.setSpacing(16); info_layout.setAlignment(Qt.AlignTop)
        self.art_label = QLabel(); self.art_label.setFixedSize(232, 232); self.art_label.setObjectName("NowPlayingArt"); self.art_label.setAlignment(Qt.AlignCenter)
        self.track_title_lbl = QLabel("—"); self.track_title_lbl.setObjectName("NowPlayingTitle"); self.track_title_lbl.setWordWrap(True); self.track_title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; background: transparent; margin-top: 8px;")
        self.track_artist_lbl = QLabel("—"); self.track_artist_lbl.setObjectName("NowPlayingArtist"); self.track_artist_lbl.setStyleSheet("font-size: 13px; font-weight: 500; background: transparent; opacity: 0.7;")
        info_layout.addWidget(self.art_label, 0, Qt.AlignHCenter); info_layout.addWidget(self.track_title_lbl); info_layout.addWidget(self.track_artist_lbl); info_layout.addStretch()
        self._queue_panel = QFrame(); self._queue_panel.setObjectName("QueuePanel"); self._queue_panel.setAttribute(Qt.WA_StyledBackground, True)
        panel_layout = QVBoxLayout(self._queue_panel); panel_layout.setContentsMargins(16, 20, 16, 20); panel_layout.setSpacing(12)
        queue_header = QLabel(I18n.t("queue").upper()); queue_header.setStyleSheet("font-size: 11px; font-weight: 800; letter-spacing: 2px; background: transparent;")
        self.queue_list = QListWidget(); self.queue_list.setFrameShape(QFrame.NoFrame); self.queue_list.setStyleSheet("background: transparent; border: none;"); self.queue_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        panel_layout.addWidget(queue_header); panel_layout.addWidget(self.queue_list); root.addWidget(self._info_panel); root.addWidget(self._queue_panel, 1); self._apply_panel_styles()

    def _apply_panel_styles(self):
        theme = ThemeManager.load_theme_config(); sidebar_bg = theme.get("sidebar_bg", "#FFE4E9"); side_alpha = theme.get("side_opacity", 100)
        from PyQt5.QtGui import QColor
        c = QColor(sidebar_bg); rgba = f"rgba({c.red()},{c.green()},{c.blue()},{side_alpha/100.0:.2f})"; text_color = ThemeManager.get_panel_text_color(sidebar_bg); sub_color = ThemeManager.get_panel_text_color(sidebar_bg, is_sub=True)
        shared_qss = f"background-color: {rgba}; border-radius: 18px; border: 1px solid rgba(255,255,255,0.18); color: {text_color};"; child_qss = f"color: {text_color}; background: transparent;"
        self._info_panel.setStyleSheet(f"QFrame#NowPlayingInfoPanel {{ {shared_qss} }} QFrame#NowPlayingInfoPanel QLabel {{ {child_qss} }}")
        self.track_artist_lbl.setStyleSheet(f"font-size: 13px; font-weight: 500; background: transparent; color: {sub_color};")
        self._queue_panel.setStyleSheet(f"QFrame#QueuePanel {{ {shared_qss} }} QFrame#QueuePanel QLabel {{ {child_qss} }} QFrame#QueuePanel QListWidget {{ color: {text_color}; background: transparent; border: none; }} QFrame#QueuePanel QListWidget::item {{ color: {text_color}; }}")

    def showEvent(self, event): super().showEvent(event); self._apply_panel_styles()
    def set_track(self, meta: TrackMetadata, cover_bytes: bytes | None, queue: list, current_track=None):
        self._apply_panel_styles(); self.track_title_lbl.setText(meta.title or "—"); self.track_artist_lbl.setText(meta.artist or "—")
        if cover_bytes:
            img = QImage.fromData(cover_bytes)
            if not img.isNull():
                pm = QPixmap.fromImage(img).scaled(232, 232, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation); self.art_label.setPixmap(_round_pixmap(pm, 16))
            else: self.art_label.setPixmap(_default_cover(232))
        else: self.art_label.setPixmap(_default_cover(232))
        self.queue_list.clear()
        for i, track in enumerate(queue):
            item = QListWidgetItem(self.queue_list); item.setSizeHint(QSize(0, 52)); row = TrackRowWidget(i + 1, track)
            if current_track and track.path == current_track.path: row.set_active(True)
            self.queue_list.setItemWidget(item, row)

class BottomPlayerBar(QFrame):
    play_pause_clicked = pyqtSignal(); prev_clicked = pyqtSignal(); next_clicked = pyqtSignal(); shuffle_clicked = pyqtSignal(); repeat_clicked = pyqtSignal(); seek_requested = pyqtSignal(float); volume_changed = pyqtSignal(float); art_clicked = pyqtSignal(); mute_toggled = pyqtSignal(bool); album_clicked = pyqtSignal(str); stems_updated = pyqtSignal(dict); start_separation = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("BottomBar"); self.setAttribute(Qt.WA_StyledBackground); self.setFixedHeight(100); self._duration = 0.0; self._current_album = ""; self._user_seeking = False; self._is_muted = False; self._vol_before_mute = 80; self._build_ui()
    def _build_ui(self):
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self._seek_slider = ClickableSlider(Qt.Horizontal); self._seek_slider.setObjectName("BottomSeekSlider"); self._seek_slider.setRange(0, 1000); self._seek_slider.setFixedHeight(12); self._seek_slider.sliderPressed.connect(self._on_seek_press); self._seek_slider.sliderReleased.connect(self._on_seek_release)
        self._time_cur = QLabel("0:00"); self._time_tot = QLabel("0:00")
        theme = ThemeManager.load_theme_config(); primary = theme.get("primary_color", "#1DB954"); bottom_bg = theme.get("bottom_bg", "#121212"); bot_text = ThemeManager.get_smart_text_color(bottom_bg, theme.get("bot_opacity", 100)); bot_sub = ThemeManager.get_smart_text_color(bottom_bg, theme.get("bot_opacity", 100), True); self._bot_text = bot_text; self._bot_sub = bot_sub
        left_layout = QHBoxLayout(); left_layout.setSpacing(12)
        self._cover_label = ClickableLabel()
        self._cover_label.setFixedSize(56, 56)
        self._cover_label.setCursor(Qt.PointingHandCursor)
        self._cover_label.setStyleSheet("border-radius: 8px; background: rgba(128,128,128,0.1);")
        self._cover_label.clicked.connect(self.art_clicked.emit)
        
        text_layout = QVBoxLayout(); text_layout.setSpacing(2); title_row = QHBoxLayout(); self._title_label = QLabel(I18n.t("no_song")); self._title_label.setObjectName("PlayerTitle")
        self._lossless_badge = QLabel("LOSSLESS"); self._lossless_badge.setStyleSheet(f"font-size: 9px; font-weight: 900; color: {primary}; border: 1px solid {primary}88; border-radius: 4px; padding: 1px 4px; letter-spacing: 1px; margin-left: 8px;"); self._lossless_badge.setToolTip("Bit-perfect FLAC")
        title_row.addWidget(self._title_label); title_row.addWidget(self._lossless_badge); title_row.addStretch(); self._artist_label = ClickableLabel(I18n.t("artist_label")); self._artist_label.setObjectName("PlayerArtist"); self._artist_label.clicked.connect(lambda: self.album_clicked.emit(self._current_album))
        text_layout.addLayout(title_row); text_layout.addWidget(self._artist_label); seek_row = QHBoxLayout(); seek_row.setContentsMargins(16, 2, 16, 0); seek_row.setSpacing(12); self._time_cur.setStyleSheet(f"color: {bot_sub}; font-size: 11px; font-family: monospace;"); self._time_tot.setStyleSheet(f"color: {bot_sub}; font-size: 11px; font-family: monospace;"); seek_row.addWidget(self._time_cur); seek_row.addWidget(self._seek_slider, 1); seek_row.addWidget(self._time_tot); main_layout.addLayout(seek_row); content_layout = QHBoxLayout(); content_layout.setContentsMargins(16, 0, 16, 8); content_layout.setSpacing(20); content_layout.addLayout(left_layout); left_layout.addWidget(self._cover_label); left_layout.addLayout(text_layout); left_layout.addStretch()
        self._center_panel = QWidget(); center_layout = QVBoxLayout(self._center_panel); center_layout.setContentsMargins(0, 0, 0, 0); center_layout.setSpacing(4); btn_row = QHBoxLayout(); btn_row.setSpacing(20); btn_row.setAlignment(Qt.AlignCenter)
        theme = ThemeManager.load_theme_config(); bottom_bg = theme.get("bottom_bg", "#121212"); bot_alpha = theme.get("bot_opacity", 100)
        from PyQt5.QtGui import QColor as _QColor
        _bg_c = _QColor(bottom_bg); _brightness = (_bg_c.red() * 299 + _bg_c.green() * 587 + _bg_c.blue() * 114) / 1000
        if bot_alpha < 50: ic_color = "#FFFFFF"
        else: ic_color = "#FFFFFF" if _brightness < 160 else "#2D2D2D"
        self._shuffle_btn = QPushButton(); self._shuffle_btn.setObjectName("BottomShuffleBtn"); self._shuffle_btn.setIcon(get_icon("shuffle", ic_color, 18)); self._shuffle_btn.setFixedSize(40, 40); self._shuffle_btn.setCursor(Qt.PointingHandCursor); self._shuffle_btn.setFocusPolicy(Qt.NoFocus); self._shuffle_btn.clicked.connect(self.shuffle_clicked)
        self._prev_btn = QPushButton(); self._prev_btn.setObjectName("BottomPrevBtn"); self._prev_btn.setIcon(get_icon("prev", ic_color, 22)); self._prev_btn.setFixedSize(40, 40); self._prev_btn.setCursor(Qt.PointingHandCursor); self._prev_btn.setFocusPolicy(Qt.NoFocus); self._prev_btn.clicked.connect(self.prev_clicked)
        self._play_btn = QPushButton(); self._play_btn.setObjectName("BottomPlayBtn")
        _primary_c = _QColor(theme.get("primary_color", "#121212")); _primary_brightness = (_primary_c.red() * 299 + _primary_c.green() * 587 + _primary_c.blue() * 114) / 1000; _play_icon_color = "#1A1A1A" if _primary_brightness > 160 else "#FFFFFF"
        self._play_btn.setIcon(get_icon("play", _play_icon_color, 28)); self._play_btn.setIconSize(QSize(28, 28)); self._play_btn.setFixedSize(56, 56); self._play_btn.setCursor(Qt.PointingHandCursor); self._play_btn.setFocusPolicy(Qt.NoFocus); self._play_btn.clicked.connect(self.play_pause_clicked)
        self._next_btn = QPushButton(); self._next_btn.setObjectName("BottomNextBtn"); self._next_btn.setIcon(get_icon("next", ic_color, 22)); self._next_btn.setFixedSize(40, 40); self._next_btn.setCursor(Qt.PointingHandCursor); self._next_btn.setFocusPolicy(Qt.NoFocus); self._next_btn.clicked.connect(self.next_clicked)
        self._repeat_btn = QPushButton(); self._repeat_btn.setObjectName("BottomRepeatBtn"); self._repeat_btn.setIcon(get_icon("repeat", ic_color, 18)); self._repeat_btn.setFixedSize(40, 40); self._repeat_btn.setCursor(Qt.PointingHandCursor); self._repeat_btn.setFocusPolicy(Qt.NoFocus); self._repeat_btn.clicked.connect(self.repeat_clicked)
        btn_row.addWidget(self._shuffle_btn); btn_row.addWidget(self._prev_btn); btn_row.addWidget(self._play_btn); btn_row.addWidget(self._next_btn); btn_row.addWidget(self._repeat_btn); center_layout.addLayout(btn_row)
        self._right_panel = QWidget(); right_layout = QHBoxLayout(self._right_panel); right_layout.setContentsMargins(0, 0, 8, 0); right_layout.setSpacing(6); right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._vol_btn = QPushButton(); self._vol_btn.setObjectName("VolBtn"); self._vol_btn.setFixedSize(36, 36); self._vol_btn.setCursor(Qt.PointingHandCursor); self._vol_btn.setFocusPolicy(Qt.NoFocus); self._vol_btn.setIcon(get_icon("volume", ic_color, 18)); self._vol_btn.setStyleSheet("QPushButton#VolBtn { background: rgba(128,128,128,0.15); border: 1px solid rgba(128,128,128,0.25); border-radius: 18px; padding: 0; } QPushButton#VolBtn:hover { background: rgba(128,128,128,0.30); }")
        self._vol_btn.clicked.connect(self._toggle_mute); self._vol_slider = QSlider(Qt.Horizontal); self._vol_slider.setFixedWidth(100); self._vol_slider.setFixedHeight(20); self._vol_slider.setRange(0, 100); self._vol_slider.setValue(80); self._vol_slider.valueChanged.connect(self._on_volume_slider_changed)
        self._ai_btn = QPushButton(); self._ai_btn.setObjectName("AiBtn"); self._ai_btn.setFixedSize(36, 36); self._ai_btn.setCursor(Qt.PointingHandCursor); self._ai_btn.setFocusPolicy(Qt.NoFocus); self._ai_btn.setIcon(get_icon("ai", ic_color, 20)); self._ai_btn.setStyleSheet("QPushButton#AiBtn { background: rgba(128,128,128,0.15); border: 1px solid rgba(128,128,128,0.25); border-radius: 18px; padding: 0; } QPushButton#AiBtn:hover { background: rgba(128,128,128,0.30); }")
        self._stem_popup = StemSelectorPopup(self); self._stem_popup.stems_updated.connect(self.stems_updated.emit); self._stem_popup.start_separation.connect(self.start_separation.emit); self._ai_btn.clicked.connect(lambda: self._stem_popup.show_above(self._ai_btn))
        right_layout.addWidget(self._ai_btn); right_layout.addWidget(self._vol_btn); right_layout.addWidget(self._vol_slider); content_layout.addWidget(self._center_panel, 2); content_layout.addWidget(self._right_panel, 1); main_layout.addLayout(content_layout)
    def update_theme_colors(self):
        theme = ThemeManager.load_theme_config()
        primary = theme.get("primary_color", "#1DB954")
        bottom_bg = theme.get("bottom_bg", "#121212")
        bot_alpha = theme.get("bot_opacity", 100)
        
        from PyQt5.QtGui import QColor as _QColor
        bg_c = _QColor(bottom_bg)
        brightness = (bg_c.red() * 299 + bg_c.green() * 587 + bg_c.blue() * 114) / 1000
        
        # High-contrast logic
        if bot_alpha < 50:
            ic_color = "#FFFFFF"
        else:
            ic_color = "#FFFFFF" if brightness < 160 else "#2D2D2D"
            
        self._bot_text = ThemeManager.get_smart_text_color(bottom_bg, bot_alpha)
        self._bot_sub = ThemeManager.get_smart_text_color(bottom_bg, bot_alpha, True)
        
        # Update labels
        self._time_cur.setStyleSheet(f"color: {self._bot_sub}; font-size: 11px; font-family: monospace;")
        self._time_tot.setStyleSheet(f"color: {self._bot_sub}; font-size: 11px; font-family: monospace;")
        self._title_label.setStyleSheet(f"color: {self._bot_text}; font-size: 15px; font-weight: 700;")
        self._artist_label.setStyleSheet(f"color: {self._bot_sub}; font-size: 13px; font-weight: 500;")
        self._lossless_badge.setStyleSheet(f"font-size: 9px; font-weight: 900; color: {primary}; border: 1px solid {primary}88; border-radius: 4px; padding: 1px 4px; letter-spacing: 1px; margin-left: 8px;")
        
        # Update icons
        self._shuffle_btn.setIcon(get_icon("shuffle", primary if self._shuffle_btn.property("active") == "true" else ic_color, 18))
        self._prev_btn.setIcon(get_icon("prev", ic_color, 22))
        
        # Play/Pause color logic (background of primary color)
        primary_c = _QColor(primary)
        primary_brightness = (primary_c.red() * 299 + primary_c.green() * 587 + primary_c.blue() * 114) / 1000
        play_icon_color = "#1A1A1A" if primary_brightness > 160 else "#FFFFFF"
        
        # Current play/pause state
        is_playing = self._play_btn.property("playing") == "true"
        self._play_btn.setIcon(get_icon("pause" if is_playing else "play", play_icon_color, 28))
        self._play_btn.setStyleSheet(f"QPushButton#BottomPlayBtn {{ background-color: {primary}; border-radius: 28px; }}")

        self._next_btn.setIcon(get_icon("next", ic_color, 22))
        self._repeat_btn.setIcon(get_icon("repeat", primary if self._repeat_btn.property("active") == "true" else ic_color, 18))
        
        # Right panel items
        self._vol_btn.setIcon(get_icon("volume", "#FF5555" if self._is_muted else ic_color, 18))
        self._ai_btn.setIcon(get_icon("ai", ic_color, 20))
        
        # Re-apply styles for buttons
        btn_qss = f"background: rgba(128,128,128,0.15); border: 1px solid rgba(128,128,128,0.25); border-radius: 18px; padding: 0;"
        self._vol_btn.setStyleSheet(f"QPushButton#VolBtn {{ {btn_qss} }} QPushButton#VolBtn:hover {{ background: rgba(128,128,128,0.30); }}")
        self._ai_btn.setStyleSheet(f"QPushButton#AiBtn {{ {btn_qss} }} QPushButton#AiBtn:hover {{ background: rgba(128,128,128,0.30); }}")
        
        # Update popup
        self._stem_popup._build_ui()

    def _on_volume_slider_changed(self, v: int):
        if not self._is_muted: self._vol_before_mute = v
        self.volume_changed.emit(v / 100.0)

    def _toggle_mute(self):
        self._is_muted = not self._is_muted
        if self._is_muted: self._vol_before_mute = self._vol_slider.value(); self._vol_slider.setValue(0); self.volume_changed.emit(0.0); self._vol_btn.setIcon(get_icon("volume", "#FF5555", 18))
        else:
            self._vol_slider.setValue(self._vol_before_mute); self.volume_changed.emit(self._vol_before_mute / 100.0)
            ic = self._bot_text if hasattr(self, '_bot_text') else "#FFFFFF"; self._vol_btn.setIcon(get_icon("volume", ic, 18))
        self.mute_toggled.emit(self._is_muted)

    def set_track(self, meta: TrackMetadata, cover_bytes: bytes | None, stems_available: bool = False, is_lossless: bool = True):
        self._title_label.setText(meta.title); self._current_album = meta.album or ""; album_text = f" - {meta.album}" if meta.album else ""; self._artist_label.setText(f"{meta.artist}{album_text}"); self._duration = meta.duration; self._update_time(0); self._stem_popup.set_available(stems_available); self.update_lossless_status(is_lossless)
        if cover_bytes:
            img = QImage.fromData(cover_bytes)
            if not img.isNull(): self._cover_label.setPixmap(QPixmap.fromImage(img).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else: self._cover_label.clear()

    def update_lossless_status(self, active: bool):
        if active: self._lossless_badge.setStyleSheet(self._lossless_badge.styleSheet().replace("opacity: 0.3;", "")); self._lossless_badge.setToolTip("Bit-perfect orijinal FLAC kalitesi aktif.")
        else:
            if "opacity: 0.3;" not in self._lossless_badge.styleSheet(): self._lossless_badge.setStyleSheet(self._lossless_badge.styleSheet() + "opacity: 0.3;")
            self._lossless_badge.setToolTip("AI Stem Miksi aktif (Kalite ayrıştırılmış dosyalara göre).")

    def _update_time(self, elapsed):
        cur, tot = int(elapsed), int(self._duration); self._time_cur.setText(f"{cur//60}:{cur%60:02d}"); self._time_tot.setText(f"{tot//60}:{tot%60:02d}")
    def update_position(self, seconds: float):
        if self._user_seeking or self._duration <= 0: return
        self._seek_slider.setValue(int(seconds / self._duration * 1000)); self._update_time(seconds)
    def set_playing(self, playing: bool):
        self._play_btn.setProperty("playing", "true" if playing else "false")
        icon_name = "pause" if playing else "play"; theme = ThemeManager.load_theme_config(); primary_c = QColor(theme.get("primary_color", "#1DB954")); _br = (primary_c.red() * 299 + primary_c.green() * 587 + primary_c.blue() * 114) / 1000; play_icon_color = "#1A1A1A" if _br > 160 else "#FFFFFF"; self._play_btn.setIcon(get_icon(icon_name, play_icon_color, 28))
    def set_shuffle(self, on: bool):
        primary_color = ThemeManager.get_primary_color(); sub_color = ThemeManager.get_subtext_color(); color = primary_color if on else sub_color; self._shuffle_btn.setIcon(get_icon("shuffle", color, 20)); self._shuffle_btn.setProperty("active", "true" if on else "false"); self._shuffle_btn.style().unpolish(self._shuffle_btn); self._shuffle_btn.style().polish(self._shuffle_btn)
    def set_repeat(self, on: bool):
        primary_color = ThemeManager.get_primary_color(); sub_color = ThemeManager.get_subtext_color(); color = primary_color if on else sub_color; self._repeat_btn.setIcon(get_icon("repeat", color, 20)); self._repeat_btn.setProperty("active", "true" if on else "false"); self._repeat_btn.style().unpolish(self._repeat_btn); self._repeat_btn.style().polish(self._repeat_btn)
    def _on_seek_press(self): self._user_seeking = True
    def _on_seek_release(self):
        self._user_seeking = False
        if self._duration > 0: self.seek_requested.emit(self._seek_slider.value() / 1000 * self._duration)
    def _on_artist_clicked(self):
        if self._current_album: self.album_clicked.emit(self._current_album)

# ── Stats UI Components ─────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, title, value, sub_value="", parent=None):
        super().__init__(parent); self.setObjectName("StatCard"); self.setFixedWidth(260); self.setFixedHeight(140)
        layout = QVBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20)
        text_color = ThemeManager.get_text_color(); sub_color = ThemeManager.get_subtext_color(); primary_color = ThemeManager.get_primary_color()
        title_lbl = QLabel(title.upper()); title_lbl.setStyleSheet(f"color: {sub_color}; font-size: 11px; font-weight: 900; letter-spacing: 1px;")
        val_lbl = QLabel(value); val_lbl.setStyleSheet(f"color: {text_color}; font-size: 24px; font-weight: 700; margin-top: 4px;")
        sub_lbl = QLabel(sub_value); sub_lbl.setStyleSheet(f"color: {primary_color}; font-size: 13px; font-weight: 500;")
        layout.addWidget(title_lbl); layout.addWidget(val_lbl); layout.addWidget(sub_lbl); layout.addStretch()

class StatBar(QWidget):
    def __init__(self, label, value, percentage, parent=None):
        super().__init__(parent); layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 16); layout.setSpacing(6)
        text_color = ThemeManager.get_text_color(); sub_color = ThemeManager.get_subtext_color()
        info = QHBoxLayout(); lbl = QLabel(label); lbl.setStyleSheet(f"color: {text_color}; font-weight: 600; font-size: 14px;"); val = QLabel(value); val.setStyleSheet(f"color: {sub_color}; font-size: 13px;"); info.addWidget(lbl); info.addStretch(); info.addWidget(val)
        self.bar = QProgressBar(); self.bar.setFixedHeight(6); self.bar.setRange(0, 100); self.bar.setValue(int(percentage)); self.bar.setTextVisible(False)
        primary_color = ThemeManager.get_primary_color(); bg_color = ThemeManager.load_theme_config().get("bg_color", "#121212"); groove_color = QColor(bg_color).darker(120).name(); self.bar.setStyleSheet(f"QProgressBar {{ background: {groove_color}; border: none; border-radius: 3px; }} QProgressBar::chunk {{ background: {primary_color}; border-radius: 3px; }}")
        layout.addLayout(info); layout.addWidget(self.bar)

# ── Stats View ──────────────────────────────────────────────────────
class StatsView(QWidget):
    def __init__(self, stats_manager, parent=None):
        super().__init__(parent); self.setObjectName("StatsView"); self.stats = stats_manager; self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(0)
        hero = QFrame(); hero.setObjectName("StatsHero"); hero.setFixedHeight(180); hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(32, 0, 32, 0)
        title_v = QVBoxLayout(); title_v.setAlignment(Qt.AlignVCenter); main_title = QLabel(I18n.t("stats")); main_title.setStyleSheet("font-size: 32px; font-weight: 900;"); sub_title = QLabel("Dinleme aliskanliklarinin derinlemesine analizi."); sub_title.setStyleSheet("font-size: 14px;"); title_v.addWidget(main_title); title_v.addWidget(sub_title)
        self.total_time_lbl = QLabel("0.0 SAAT"); primary_color = ThemeManager.get_primary_color(); self.total_time_lbl.setStyleSheet(f"font-size: 48px; font-weight: 900; color: {primary_color};")
        hero_layout.addLayout(title_v, 1); hero_layout.addWidget(self.total_time_lbl); layout.addWidget(hero); layout.addSpacing(40)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget(); self.content_layout = QVBoxLayout(content); self.content_layout.setSpacing(48); self.content_layout.setContentsMargins(0, 0, 40, 0)
        cols = QHBoxLayout(); cols.setSpacing(40); sub_color = ThemeManager.get_subtext_color(); art_v = QVBoxLayout(); art_title = QLabel(I18n.t("top_artists")); art_title.setStyleSheet(f"color: {sub_color}; font-weight: 900; font-size: 12px; letter-spacing: 2px;"); self.artist_list = QVBoxLayout(); art_v.addWidget(art_title); art_v.addSpacing(24); art_v.addLayout(self.artist_list); art_v.addStretch()
        alb_v = QVBoxLayout(); alb_title = QLabel(I18n.t("top_albums")); alb_title.setStyleSheet(f"color: {sub_color}; font-weight: 900; font-size: 12px; letter-spacing: 2px;"); self.album_list = QVBoxLayout(); alb_v.addWidget(alb_title); alb_v.addSpacing(24); alb_v.addLayout(self.album_list); alb_v.addStretch()
        cols.addLayout(art_v, 1); cols.addLayout(alb_v, 1); self.content_layout.addLayout(cols)
        hist_title = QLabel("SON DINLEDIKLERIN"); hist_title.setStyleSheet(f"color: {sub_color}; font-weight: 900; font-size: 12px; letter-spacing: 2px;"); self.history_list = QVBoxLayout(); self.content_layout.addWidget(hist_title); self.content_layout.addLayout(self.history_list); self.scroll.setWidget(content); layout.addWidget(self.scroll)

    def refresh(self):
        total_sec = self.stats.get_total_listening_time(); self.total_time_lbl.setText(f"{total_sec/3600:.1f} SAAT")
        for l in [self.artist_list, self.album_list, self.history_list]:
            while l.count():
                c = l.takeAt(0); 
                if c.widget(): c.widget().deleteLater()
                elif c.layout():
                    while c.layout().count():
                        sub = c.layout().takeAt(0)
                        if sub.widget(): sub.widget().deleteLater()
        artists = self.stats.get_top_artists(5); max_time = artists[0][2] if artists else 1
        for name, count, total_time in artists:
            h = int(total_time // 3600); m = int((total_time % 3600) // 60); time_str = f"{h}s {m}d" if h > 0 else f"{m} dk"; self.artist_list.addWidget(StatBar(name, f"{count} dinleme • {time_str}", (total_time/max_time)*100))
        albums = self.stats.get_top_albums(5); max_alb_time = albums[0][3] if albums else 1
        for name, artist, count, total_time in albums:
            h = int(total_time // 3600); m = int((total_time % 3600) // 60); time_str = f"{h}s {m}d" if h > 0 else f"{m} dk"; self.album_list.addWidget(StatBar(f"{name}", f"{artist} • {time_str}", (total_time/max_alb_time)*100))
        for title, artist, ts in self.stats.get_recent_history(10):
            from datetime import datetime; dt = datetime.fromtimestamp(ts).strftime('%H:%M'); row = QFrame(); row.setObjectName("HistoryRow"); row_l = QHBoxLayout(row); row_l.setContentsMargins(16, 12, 16, 12); text_color = ThemeManager.get_text_color(); sub_color = ThemeManager.get_subtext_color(); t_lbl = QLabel(title); t_lbl.setStyleSheet(f"color: {text_color}; font-weight: 600;"); a_lbl = QLabel(artist); a_lbl.setStyleSheet(f"color: {sub_color};"); ts_lbl = QLabel(dt); ts_lbl.setStyleSheet(f"color: {sub_color}; font-family: monospace;"); row_l.addWidget(t_lbl); row_l.addSpacing(12); row_l.addWidget(a_lbl, 1); row_l.addWidget(ts_lbl); self.history_list.addWidget(row)

# ── Help View ──────────────────────────────────────────────────────
class HelpView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("HelpView"); self._build_ui()
    def _build_ui(self):
        layout = QVBoxLayout(self); layout.setContentsMargins(60, 60, 60, 60); layout.setSpacing(40)
        header = QVBoxLayout(); title = QLabel("LOSSLESS PLAYER"); theme = ThemeManager.load_theme_config(); primary = theme.get("primary_color", "#FF85A1"); text_color = ThemeManager.get_text_color(); sub_color = ThemeManager.get_subtext_color(); title.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {primary}; letter-spacing: 2px;"); desc = QLabel(I18n.t("help")); desc.setStyleSheet(f"font-size: 14px; color: {sub_color};"); header.addWidget(title); header.addWidget(desc); layout.addLayout(header)
        grid = QGridLayout(); grid.setSpacing(24)
        def create_help_card(icon_name, title_txt, desc_txt, link_url="#"):
            card = QFrame(); card.setStyleSheet(f"QFrame {{ background: rgba(128, 128, 128, 0.05); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 24px; }} QFrame:hover {{ background: rgba(128, 128, 128, 0.1); border: 1px solid {primary}44; }}")
            c_lay = QVBoxLayout(card); ic_lbl = QLabel(); ic_lbl.setPixmap(get_icon(icon_name, primary, 40).pixmap(40, 40)); ic_lbl.setStyleSheet("background: transparent; border: none;"); t_lbl = QLabel(title_txt); t_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {text_color}; border: none;"); d_lbl = QLabel(desc_txt); d_lbl.setWordWrap(True); d_lbl.setStyleSheet(f"font-size: 13px; color: {sub_color}; border: none;"); btn = QPushButton(I18n.t("help")); btn.setCursor(Qt.PointingHandCursor); btn.setStyleSheet(f"QPushButton {{ background: {primary}22; color: {primary}; border-radius: 8px; padding: 8px; font-weight: 600; margin-top: 10px; }} QPushButton:hover {{ background: {primary}; color: white; }}")
            import webbrowser; btn.clicked.connect(lambda: webbrowser.open(link_url)); c_lay.addWidget(ic_lbl); c_lay.addSpacing(10); c_lay.addWidget(t_lbl); c_lay.addWidget(d_lbl); c_lay.addStretch(); c_lay.addWidget(btn); return card
        grid.addWidget(create_help_card("github", "GitHub Repository", "Kaynak kodları inceleyin, hata bildirin veya projeye katkıda bulunun.", "https://github.com"), 0, 0); grid.addWidget(create_help_card("stats", "Kullanım Kılavuzu", "Uygulamanın tüm özelliklerini ve kısayollarını detaylıca öğrenin.", "https://github.com"), 0, 1); grid.addWidget(create_help_card("ai", "AI Stem Separation", "Şarkıları nasıl kanallarına ayırabileceğiniz hakkında bilgi alın.", "https://github.com"), 1, 0); grid.addWidget(create_help_card("settings", "Topluluk & Destek", "Discord veya diğer kanallar üzerinden topluluğa katılın.", "https://github.com"), 1, 1); layout.addLayout(grid); layout.addStretch()

# ── Audio Visualizer (Real-time FFT) ────────────────────────────────
class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setMinimumWidth(300)
        self._levels = np.zeros(32)
        self._decay = 0.85
        self._engine = None
        self._is_playing = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(33) # ~30 FPS

    def set_engine(self, engine):
        self._engine = engine

    def set_playing(self, playing):
        """Called when playback state changes."""
        self._is_playing = playing
        if not playing:
            # Optionally we could slow down decay here, 
            # but current timer-based decay is fine.
            pass

    def set_levels(self, levels):
        self._levels = np.maximum(self._levels * self._decay, levels)
        self.update()

    def _update_animation(self):
        if self._engine and hasattr(self._engine, "_viz_levels"):
            # Pull directly from engine's FFT buffer
            self.set_levels(self._engine._viz_levels)
        else:
            self._levels *= self._decay
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        n_bars = len(self._levels)
        bar_w = (w / n_bars) * 0.8
        spacing = (w / n_bars) * 0.2
        
        primary_color = ThemeManager.get_primary_color()
        grad = QLinearGradient(0, h, 0, 0)
        grad.setColorAt(0, QColor(primary_color))
        grad.setColorAt(1, QColor(primary_color).lighter(150))
        
        brush = QBrush(grad)
        
        for i in range(n_bars):
            level = self._levels[i]
            bar_h = max(2, level * h)
            x = i * (bar_w + spacing)
            y = (h - bar_h) / 2
            
            rect = QRectF(x, y, bar_w, bar_h)
            painter.setBrush(brush)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 2, 2)
