import os
import json
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QGroupBox, QDialogButtonBox, QTabWidget, QWidget,
    QColorDialog, QComboBox, QSlider, QFileDialog, QScrollArea,
    QGridLayout, QFrame
)
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from core.lastfm import LastFmService
from core.theme_manager import ThemeManager
from core.i18n import I18n
class SettingsDialog(QDialog):
    theme_changed = pyqtSignal()

    def __init__(self, lastfm: LastFmService, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{I18n.t('settings')} — Lossless Player")
        self.setMinimumWidth(650)
        self.setMinimumHeight(700)
        self.setModal(True)
        
        self._lastfm = lastfm
        theme_cfg = ThemeManager.load_theme_config()
        
        # Current Values
        self._current_primary = theme_cfg.get("primary_color", ThemeManager.DEFAULT_PRIMARY)
        self._current_bg      = theme_cfg.get("bg_color", ThemeManager.DEFAULT_BG)
        self._current_sidebar = theme_cfg.get("sidebar_bg", self._current_bg)
        self._current_bottom  = theme_cfg.get("bottom_bg", self._current_bg)
        self._current_card_bg = theme_cfg.get("card_bg", ThemeManager.DEFAULT_CARD_BG)
        self._current_font    = theme_cfg.get("font_family", ThemeManager.DEFAULT_FONT)
        self._current_bg_image = theme_cfg.get("bg_image", "")
        
        # Opacity
        self._win_alpha = theme_cfg.get("win_opacity", 100)
        self._side_alpha = theme_cfg.get("side_opacity", 100)
        self._bot_alpha = theme_cfg.get("bot_opacity", 100)
        self._card_alpha = theme_cfg.get("card_opacity", 100)
        
        # New Text Color Settings
        self._auto_text_color = theme_cfg.get("auto_text_color", True)
        self._custom_text_color = theme_cfg.get("custom_text_color", "#FFFFFF")
        
        self._current_lang = I18n.get_lang()
        
        self._build_ui()
        self._load_values()
        
        # Apply theme to dialog itself
        from resource_path import resource_path
        qss_path = resource_path(os.path.join("ui", "styles.qss"))
        ThemeManager.apply_theme(self, qss_path)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        self.tabs = QTabWidget()
        
        # ── Görünüm (Appearance) Sekmesi ──
        self.tab_appearance = QWidget()
        self._build_appearance_tab()
        self.tabs.addTab(self.tab_appearance, I18n.t("appearance"))

        # ── Last.fm Sekmesi ──
        self.tab_lastfm = QWidget()
        self._build_lastfm_tab()
        self.tabs.addTab(self.tab_lastfm, "Last.fm")

        # ── AI & Cloud Sekmesi ──
        self.tab_ai = QWidget()
        self._build_ai_tab()
        self.tabs.addTab(self.tab_ai, "AI & Cloud")

        root.addWidget(self.tabs)

        # ── OK / İptal ──
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText(I18n.t("save"))
        btns.button(QDialogButtonBox.Cancel).setText(I18n.t("cancel"))
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _build_appearance_tab(self):
        layout = QVBoxLayout(self.tab_appearance)
        layout.setSpacing(15)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # ── Hazır Temalar (Presets) ──
        preset_group = QGroupBox(I18n.t("theme_presets"))
        preset_v = QVBoxLayout(preset_group)
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Özel (Custom)", None)
        for name, values in ThemeManager.PRESETS.items():
            self.preset_combo.addItem(name, values)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_v.addWidget(self.preset_combo)
        scroll_layout.addWidget(preset_group)
        
        # ── Arka Plan Görseli ──
        bg_group = QGroupBox(I18n.t("background_image"))
        bg_layout = QVBoxLayout(bg_group)
        self.bg_path_lbl = QLabel(self._current_bg_image or "Görsel seçilmedi")
        self.bg_path_lbl.setWordWrap(True)
        self.bg_path_lbl.setStyleSheet("color: #8B949E; font-size: 11px;")
        
        h_bg = QHBoxLayout()
        btn_browse = QPushButton("Görsel Seç")
        btn_browse.setFixedWidth(100)
        btn_browse.clicked.connect(self._browse_bg_image)
        btn_clear = QPushButton("Kaldır")
        btn_clear.setFixedWidth(100)
        btn_clear.clicked.connect(self._clear_bg_image)
        h_bg.addWidget(btn_browse); h_bg.addWidget(btn_clear); h_bg.addStretch()
        
        bg_layout.addWidget(self.bg_path_lbl)
        bg_layout.addLayout(h_bg)
        scroll_layout.addWidget(bg_group)

        # ── Cam Modu (Glass Mode) ──
        glass_group = QGroupBox("Cam Modu (Glassmorphism)")
        glass_v = QVBoxLayout(glass_group)
        self.glass_combo = QComboBox()
        self.glass_combo.addItem("Yok (Kapalı)", "none")
        self.glass_combo.addItem("Var (Cam Modu)", "auto")
        self.glass_combo.addItem("Özel (Sürgüler)", "custom")
        
        self._glass_mode = ThemeManager.load_theme_config().get("glass_mode", "none")
        idx_glass = self.glass_combo.findData(self._glass_mode)
        if idx_glass >= 0: self.glass_combo.setCurrentIndex(idx_glass)
        
        self.glass_combo.currentIndexChanged.connect(self._on_glass_mode_changed)
        glass_v.addWidget(self.glass_combo)
        scroll_layout.addWidget(glass_group)

        # ── Renk ve Opaklık Ayarları ──
        self.color_group = QGroupBox("Görsel Özelleştirme")
        grid = QGridLayout(self.color_group)
        grid.setSpacing(12)
        grid.setColumnStretch(3, 1) # Give slider more room
        
        self.rows = {} # Store refs for updating

        def add_control_row(row_idx, label, current_color, pick_func, alpha_val, alpha_func):
            lbl_name = QLabel(label)
            
            prev = QLabel()
            prev.setFixedSize(28, 28)
            prev.setStyleSheet(f"background-color: {current_color}; border: 2px solid white; border-radius: 6px;")
            
            btn = QPushButton("Değiştir")
            btn.setFixedWidth(90)
            btn.clicked.connect(lambda: pick_func(prev))
            
            alpha_lbl = QLabel(f"%{alpha_val}")
            alpha_lbl.setFixedWidth(35)
            
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(alpha_val)
            slider.setFixedWidth(120)
            
            def on_val_changed(v):
                alpha_lbl.setText(f"%{v}")
                alpha_func(v)
                self.preset_combo.setCurrentIndex(0)

            slider.valueChanged.connect(on_val_changed)
            
            grid.addWidget(lbl_name, row_idx, 0)
            grid.addWidget(prev, row_idx, 1)
            grid.addWidget(btn, row_idx, 2)
            grid.addWidget(QLabel("Opaklık:"), row_idx, 3, Qt.AlignRight)
            grid.addWidget(alpha_lbl, row_idx, 4)
            grid.addWidget(slider, row_idx, 5)
            
            return prev, slider
        
        # Primary doesn't need opacity
        self.prev_primary, self.sld_primary = add_control_row(0, f"{I18n.t('accent_color')}:", self._current_primary, self._pick_primary, 100, lambda v: None)
        self.sld_primary.setEnabled(False) 
        
        self.prev_win, self.sld_win = add_control_row(1, "Ana Arka Plan:", self._current_bg, self._pick_win_bg, self._win_alpha, lambda v: setattr(self, '_win_alpha', v))
        self.prev_side, self.sld_side = add_control_row(2, "Yan Panel:", self._current_sidebar, self._pick_side_bg, self._side_alpha, lambda v: setattr(self, '_side_alpha', v))
        self.prev_bot, self.sld_bot = add_control_row(3, "Alt Panel:", self._current_bottom, self._pick_bot_bg, self._bot_alpha, lambda v: setattr(self, '_bot_alpha', v))
        self.prev_card, self.sld_card = add_control_row(4, "Kartlar:", self._current_card_bg, self._pick_card_bg, self._card_alpha, lambda v: setattr(self, '_card_alpha', v))

        scroll_layout.addWidget(self.color_group)
        self._update_glass_visibility()

        # ── Metin & Kontrast Ayarları ──
        from PyQt5.QtWidgets import QCheckBox, QFormLayout
        text_group = QGroupBox("Metin & Kontrast")
        text_form = QFormLayout(text_group)
        
        self.auto_text_cb = QCheckBox("Otomatik Metin Rengi (Akıllı Zıtlık)")
        self.auto_text_cb.setChecked(self._auto_text_color)
        
        self.custom_text_btn = QPushButton("Özel Renk Seç")
        self.custom_text_btn.setFixedWidth(120)
        self.custom_text_btn.setEnabled(not self._auto_text_color)
        self.custom_text_btn.clicked.connect(self._pick_custom_text)
        
        self.auto_text_cb.toggled.connect(lambda checked: self.custom_text_btn.setEnabled(not checked))
        self.auto_text_cb.toggled.connect(lambda: self.preset_combo.setCurrentIndex(0))
        
        text_form.addRow(self.auto_text_cb)
        text_form.addRow("Yazı Rengi:", self.custom_text_btn)
        scroll_layout.addWidget(text_group)


        # ── Genel Ayarlar ──
        gen_group = QGroupBox(I18n.t("general"))
        gen_form = QFormLayout(gen_group)
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Inter", "Segoe UI", "Roboto", "Monospace", "Tahoma"])
        self.font_combo.setCurrentText(self._current_font)
        gen_form.addRow(f"{I18n.t('font')}:", self.font_combo)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Türkçe", "tr")
        self.lang_combo.addItem("English", "en")
        idx_lang = self.lang_combo.findData(self._current_lang)
        if idx_lang >= 0: self.lang_combo.setCurrentIndex(idx_lang)
        gen_form.addRow(f"{I18n.t('language')}:", self.lang_combo)
        
        scroll_layout.addWidget(gen_group)
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def _on_preset_changed(self, index):
        data = self.preset_combo.currentData()
        if data:
            # Colors
            self._current_primary = data["primary_color"]
            self._current_bg = data["bg_color"]
            self._current_sidebar = data.get("sidebar_bg", self._current_bg)
            self._current_bottom = data.get("bottom_bg", self._current_bg)
            self._current_card_bg = data["card_bg"]
            
            # Opacities
            self._win_alpha = data.get("win_opacity", 100)
            self._side_alpha = data.get("side_opacity", 100)
            self._bot_alpha = data.get("bot_opacity", 100)
            self._card_alpha = data.get("card_opacity", 100)
            
            # Update UI
            self.prev_primary.setStyleSheet(f"background-color: {self._current_primary}; border: 2px solid white; border-radius: 6px;")
            self.prev_win.setStyleSheet(f"background-color: {self._current_bg}; border: 2px solid white; border-radius: 6px;")
            self.prev_side.setStyleSheet(f"background-color: {self._current_sidebar}; border: 2px solid white; border-radius: 6px;")
            self.prev_bot.setStyleSheet(f"background-color: {self._current_bottom}; border: 2px solid white; border-radius: 6px;")
            self.prev_card.setStyleSheet(f"background-color: {self._current_card_bg}; border: 2px solid white; border-radius: 6px;")
            
            self.sld_win.setValue(self._win_alpha)
            self.sld_side.setValue(self._side_alpha)
            self.sld_bot.setValue(self._bot_alpha)
            self.sld_card.setValue(self._card_alpha)
            
            self.font_combo.setCurrentText(data["font_family"])
            self.preset_combo.setCurrentIndex(index) # Keep index

    # ── Color Pickers ──
    def _pick_primary(self, lbl):
        c = QColorDialog.getColor(QColor(self._current_primary), self)
        if c.isValid(): 
            self._current_primary = c.name()
            lbl.setStyleSheet(f"background-color: {c.name()}; border: 2px solid white; border-radius: 6px;")
            self.preset_combo.setCurrentIndex(0)
    
    def _pick_win_bg(self, lbl):
        c = QColorDialog.getColor(QColor(self._current_bg), self)
        if c.isValid(): 
            self._current_bg = c.name()
            lbl.setStyleSheet(f"background-color: {c.name()}; border: 2px solid white; border-radius: 6px;")
            self.preset_combo.setCurrentIndex(0)

    def _pick_side_bg(self, lbl):
        c = QColorDialog.getColor(QColor(self._current_sidebar), self)
        if c.isValid(): 
            self._current_sidebar = c.name()
            lbl.setStyleSheet(f"background-color: {c.name()}; border: 2px solid white; border-radius: 6px;")
            self.preset_combo.setCurrentIndex(0)

    def _pick_bot_bg(self, lbl):
        c = QColorDialog.getColor(QColor(self._current_bottom), self)
        if c.isValid(): 
            self._current_bottom = c.name()
            lbl.setStyleSheet(f"background-color: {c.name()}; border: 2px solid white; border-radius: 6px;")
            self.preset_combo.setCurrentIndex(0)

    def _pick_card_bg(self, lbl):
        c = QColorDialog.getColor(QColor(self._current_card_bg), self)
        if c.isValid(): 
            self._current_card_bg = c.name()
            lbl.setStyleSheet(f"background-color: {c.name()}; border: 2px solid white; border-radius: 6px;")
            self.preset_combo.setCurrentIndex(0)

    # ── Background Image ──
    def _browse_bg_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Arka Plan Seç", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self._current_bg_image = path
            self.bg_path_lbl.setText(path)
            self.preset_combo.setCurrentIndex(0)

    def _clear_bg_image(self):
        self._current_bg_image = ""
        self.bg_path_lbl.setText("Görsel seçilmedi")
        self.preset_combo.setCurrentIndex(0)

    def _build_lastfm_tab(self):
        layout = QVBoxLayout(self.tab_lastfm)
        group = QGroupBox(I18n.t("scrobbling"))
        form  = QFormLayout(group)
        form.setSpacing(10)

        self._enabled = QCheckBox("Scrobbling aktif")
        form.addRow("", self._enabled)

        self._api_key = QLineEdit()
        self._api_key.setPlaceholderText("API Key")
        form.addRow("API Key:", self._api_key)

        self._api_secret = QLineEdit()
        self._api_secret.setPlaceholderText("API Secret")
        form.addRow("API Secret:", self._api_secret)

        self._username = QLineEdit()
        form.addRow("Kullanıcı Adı:", self._username)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        form.addRow("Şifre:", self._password)

        btn_row = QHBoxLayout()
        self._test_btn = QPushButton(I18n.t("test_connect"))
        self._status_lbl = QLabel("")
        btn_row.addWidget(self._test_btn); btn_row.addWidget(self._status_lbl, 1)
        form.addRow("", btn_row)

        layout.addWidget(group)
        layout.addStretch()

    def _build_ai_tab(self):
        layout = QVBoxLayout(self.tab_ai)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Neon Styled Container
        neon_frame = QFrame()
        neon_frame.setObjectName("AiNeonFrame")
        neon_layout = QVBoxLayout(neon_frame)
        neon_layout.setContentsMargins(32, 32, 32, 32)
        neon_layout.setSpacing(20)

        title = QLabel("AI WORKSTATION")
        title.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {self._current_primary}; letter-spacing: 3px;")
        neon_layout.addWidget(title)

        text_color = ThemeManager.get_text_color()
        sub_color = ThemeManager.get_subtext_color()
        
        desc = QLabel("Şarkılarınızı kanallarına (vokal, davul, bas vb.) ayırmak için LossLess'in yerleşik yapay zekasını kullanın.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {text_color}; font-size: 14px; line-height: 1.5;")
        neon_layout.addWidget(desc)

        # Features
        features = [
            "✨ Yüksek Kalite: Facebook Demucs (HTDemucs) motoru.",
            "🔒 Tam Gizlilik: Şarkılarınız asla internete yüklenmez.",
            "💎 Kayıpsız İşleme: FLAC ve WAV dosyalarınızın kalitesi korunur.",
            "⚡ Lokal Güç: Tamamen bilgisayarınızın donanımını kullanır."
        ]
        for f in features:
            f_lbl = QLabel(f)
            f_lbl.setStyleSheet(f"color: {sub_color}; font-size: 13px;")
            neon_layout.addWidget(f_lbl)

        # Requirements Table Simulation
        req_frame = QFrame()
        req_frame.setStyleSheet("background: rgba(0,0,0,0.2); border-radius: 8px; padding: 10px;")
        req_l = QGridLayout(req_frame)
        req_l.setSpacing(10)
        
        headers = ["Bileşen", "Minimum", "Önerilen"]
        for i, h in enumerate(headers):
            h_lbl = QLabel(h)
            h_lbl.setStyleSheet(f"font-weight: bold; color: {self._current_primary}; font-size: 11px;")
            req_l.addWidget(h_lbl, 0, i)
            
        specs = [
            ("CPU", "i3 / Ryzen 3", "i7 / M1-M3"),
            ("RAM", "4 GB", "16 GB"),
            ("GPU", "Dahili", "NVIDIA RTX"),
            ("Disk", "2 GB SSD", "10 GB NVMe")
        ]
        for row, (comp, mini, rec) in enumerate(specs, 1):
            req_l.addWidget(QLabel(comp), row, 0)
            req_l.addWidget(QLabel(mini), row, 1)
            req_l.addWidget(QLabel(rec), row, 2)
            
        neon_layout.addWidget(QLabel("Sistem Gereksinimleri:"))
        neon_layout.addWidget(req_frame)

        neon_layout.addStretch()
        
        info_box = QFrame()
        info_box.setStyleSheet(f"background: rgba(128,128,128,0.1); border-left: 4px solid {self._current_primary}; border-radius: 4px; padding: 15px;")
        info_l = QVBoxLayout(info_box)
        info_txt = QLabel("Lokal ayristirma icin FFmpeg yuklu olmalidir. Ilk kullanimda AI modelleri (yaklasik 1GB) otomatik olarak indirilir.")
        info_txt.setWordWrap(True)
        info_txt.setStyleSheet(f"font-size: 12px; color: {sub_color}; border: none;")
        info_l.addWidget(info_txt)
        neon_layout.addWidget(info_box)

        layout.addWidget(neon_frame)
        layout.addStretch()

        from PyQt5.QtGui import QColor
        p_c = QColor(self._current_primary)
        bg_c = QColor(self._current_bg)
        inner_bg = f"rgba({bg_c.red()//2}, {bg_c.green()//2}, {bg_c.blue()//2}, 0.9)"
        
        self.tab_ai.setStyleSheet(f"""
            QFrame#AiNeonFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {inner_bg}, stop:1 rgba(10, 10, 15, 0.95));
                border: 2px solid {self._current_primary};
                border-radius: 20px;
            }}
        """)

    def _load_values(self):
        cfg = LastFmService.load_config().get("lastfm", {})
        self._enabled.setChecked(cfg.get("enabled", False))
        self._api_key.setText(cfg.get("api_key", ""))
        self._api_secret.setText(cfg.get("api_secret", ""))
        self._username.setText(cfg.get("username", ""))
        self._password.setText(cfg.get("password", ""))

    def _on_glass_mode_changed(self):
        self._glass_mode = self.glass_combo.currentData()
        if self._glass_mode == "none":
            self._win_alpha = 100; self._side_alpha = 100; self._bot_alpha = 100; self._card_alpha = 100
        elif self._glass_mode == "auto":
            self._win_alpha = 45; self._side_alpha = 70; self._bot_alpha = 70; self._card_alpha = 70
        
        self.sld_win.setValue(self._win_alpha)
        self.sld_side.setValue(self._side_alpha)
        self.sld_bot.setValue(self._bot_alpha)
        self.sld_card.setValue(self._card_alpha)
        self._update_glass_visibility()

    def _update_glass_visibility(self):
        is_custom = self._glass_mode == "custom"
        for i in range(self.color_group.layout().rowCount()):
            item3 = self.color_group.layout().itemAtPosition(i, 3)
            item4 = self.color_group.layout().itemAtPosition(i, 4)
            item5 = self.color_group.layout().itemAtPosition(i, 5)
            if item3: item3.widget().setVisible(is_custom)
            if item4: item4.widget().setVisible(is_custom)
            if item5: item5.widget().setVisible(is_custom)

    def _save(self):
        LastFmService.save_config({
            "lastfm": {
                "enabled":    self._enabled.isChecked(),
                "api_key":    self._api_key.text().strip(),
                "api_secret": self._api_secret.text().strip(),
                "username":   self._username.text().strip(),
                "password":   self._password.text().strip(),
            }
        })
        
        I18n.set_lang(self.lang_combo.currentData())
        
        theme_data = {
            "primary_color": self._current_primary,
            "bg_color":      self._current_bg,
            "sidebar_bg":   self._current_sidebar,
            "bottom_bg":    self._current_bottom,
            "card_bg":      self._current_card_bg,
            "font_family":   self.font_combo.currentText(),
            "bg_image":      self._current_bg_image,
            "win_opacity":   self._win_alpha,
            "side_opacity":  self._side_alpha,
            "bot_opacity":   self._bot_alpha,
            "card_opacity":  self._card_alpha,
            "glass_mode":    self._glass_mode,
            "auto_text_color": self.auto_text_cb.isChecked(),
            "custom_text_color": self._custom_text_color,
        }
        ThemeManager.save_theme_config(theme_data)
        self.theme_changed.emit()
        self.accept()

    def _pick_custom_text(self):
        from PyQt5.QtWidgets import QColorDialog
        from PyQt5.QtGui import QColor
        color = QColorDialog.getColor(QColor(self._custom_text_color), self)
        if color.isValid():
            self._custom_text_color = color.name()
            self.preset_combo.setCurrentIndex(0)
