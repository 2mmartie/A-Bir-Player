import json
import os
import sys
import threading
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

def _get_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

CONFIG_PATH = _get_config_path()

class ThemeManager:
    _LOCK = threading.Lock()
    DEFAULT_PRIMARY = "#1DB954"
    DEFAULT_BG = "#121212"
    DEFAULT_SIDEBAR_BG = "#121212"
    DEFAULT_BOTTOM_BG = "#121212"
    DEFAULT_CARD_BG = "#181818"
    DEFAULT_FONT = "Inter"
    
    # Kawaii Colors
    KAWAII_PINK = "#FF85A1"
    KAWAII_BG = "#FFF5F7"
    KAWAII_TEXT = "#4A2C2C" # Deep mocha for readability
    KAWAII_SUB = "#8A6B6B"
    
    PRESETS = {
        "Kawaii Strawberry": {
            "primary_color": "#FF85A1", "bg_color": "#FFF5F7", "sidebar_bg": "#FFE4E9",
            "bottom_bg": "#FFD1DA", "card_bg": "#FFFFFF", "font_family": "Inter",
            "win_opacity": 100, "side_opacity": 100, "bot_opacity": 100, "card_opacity": 100
        },
        "CyberGlitch (Neon)": {
            "primary_color": "#00FF9D", "bg_color": "#050505", "sidebar_bg": "#120022",
            "bottom_bg": "#120022", "card_bg": "#261447", "font_family": "Monospace",
            "win_opacity": 100, "side_opacity": 90, "bot_opacity": 90, "card_opacity": 80
        },
        "Spotify (Varsayılan)": {
            "primary_color": "#1DB954", "bg_color": "#121212", "sidebar_bg": "#121212",
            "bottom_bg": "#121212", "card_bg": "#181818", "font_family": "Inter",
            "win_opacity": 100, "side_opacity": 100, "bot_opacity": 100, "card_opacity": 100
        },
        "Pastel Dream (Soft)": {
            "primary_color": "#FF85A2", "bg_color": "#FDF7FF", "sidebar_bg": "#FFFFFF",
            "bottom_bg": "#F9F0FF", "card_bg": "#FFFFFF", "font_family": "Inter",
            "win_opacity": 100, "side_opacity": 100, "bot_opacity": 100, "card_opacity": 100
        },
        "Deep Ocean": {
            "primary_color": "#00E5FF", "bg_color": "#0B1120", "sidebar_bg": "#0B1120",
            "bottom_bg": "#1E293B", "card_bg": "#1E293B", "font_family": "Segoe UI",
            "win_opacity": 100, "side_opacity": 90, "bot_opacity": 95, "card_opacity": 90
        }
    }
    
    @classmethod
    def load_theme_config(cls) -> dict:
        with cls._LOCK:
            try:
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data.get("theme", {})
            except Exception:
                pass
            return cls.PRESETS["Kawaii Strawberry"].copy()

    @classmethod
    def get_primary_color(cls) -> str:
        return cls.load_theme_config().get("primary_color", cls.DEFAULT_PRIMARY)

    @classmethod
    def get_primary_hover_color(cls) -> str:
        base = QColor(cls.get_primary_color())
        return base.lighter(120).name()

    @classmethod
    def save_theme_config(cls, theme_data: dict):
        with cls._LOCK:
            data = {}
            try:
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
            except Exception:
                pass
            
            if "theme" not in data:
                data["theme"] = {}
            
            data["theme"].update(theme_data)
            
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    _BRIGHTNESS_CACHE = {} # {path: brightness}

    @classmethod
    def get_complementary_color(cls, hex_color: str) -> str:
        """Calculates the exact opposite (complementary) color for high-contrast aesthetic."""
        c = QColor(hex_color)
        # Convert to HSL for better manipulation
        h, s, l, a = c.getHslF()
        
        # Rotate Hue slightly for more 'harmonious' contrast
        h = (h + 0.5) % 1.0
        
        # Adjust Lightness for maximum legibility
        # If background is dark (L < 0.5), return very light off-white
        # If background is light (L > 0.5), return very dark charcoal
        if l < 0.5:
            l = 0.96 # Soft white
        else:
            l = 0.08 # Soft charcoal
            
        # Keep saturation moderate for elegance
        s = min(s, 0.4)
        
        res = QColor.fromHslF(h, s, l, a)
        return res.name()

    _SVG_CACHE = {} # { (path, color): QIcon }

    @classmethod
    def get_colored_icon(cls, svg_path: str, color_hex: str):
        """Reads an SVG and replaces its fill color dynamically."""
        from PyQt5.QtGui import QIcon, QPixmap, QPainter
        from PyQt5.QtSvg import QSvgRenderer
        
        cache_key = (svg_path, color_hex)
        if cache_key in cls._SVG_CACHE:
            return cls._SVG_CACHE[cache_key]

        if not os.path.exists(svg_path):
            return QIcon()

        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_data = f.read()
            
            # Replace common fill/stroke placeholders or just inject a global style
            # Simple approach: replace all hex-like colors or 'currentColor'
            new_color = color_hex
            # Inject a style tag to override everything
            style_tag = f'<style>path, circle, rect, polygon, ellipse {{ fill: {new_color} !important; stroke: {new_color} !important; }}</style>'
            if "</svg>" in svg_data:
                svg_data = svg_data.replace("</svg>", f"{style_tag}</svg>")
            
            renderer = QSvgRenderer(svg_data.encode("utf-8"))
            pixmap = QPixmap(64, 64) # Standard high-res icon size
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            icon = QIcon(pixmap)
            cls._SVG_CACHE[cache_key] = icon
            return icon
        except Exception as e:
            print(f"SVG Colorize error: {e}")
            return QIcon(svg_path)

    @classmethod
    def get_smart_text_color(cls, target_hex: str, alpha: int, is_sub: bool = False) -> str:
        """Returns best text color based on settings and background blend."""
        theme = cls.load_theme_config()
        
        # 1. User Choice: Manual Color
        if not theme.get("auto_text_color", True):
            custom_hex = theme.get("custom_text_color", "#FFFFFF")
            if is_sub:
                c = QColor(custom_hex)
                return f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.6)"
            return custom_hex

        # 2. Auto Mode: Complementary logic
        bg_image = theme.get("bg_image", "")
        bg_img_brightness = 128
        
        if bg_image and os.path.exists(bg_image):
            if bg_image in cls._BRIGHTNESS_CACHE:
                bg_img_brightness = cls._BRIGHTNESS_CACHE[bg_image]
            else:
                try:
                    from PyQt5.QtGui import QImage
                    img = QImage(bg_image)
                    if not img.isNull():
                        avg_img = img.scaled(1, 1, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        avg_color = QColor(avg_img.pixel(0, 0))
                        bg_img_brightness = (avg_color.red() * 0.299 + avg_color.green() * 0.587 + avg_color.blue() * 0.114) * 255
                        cls._BRIGHTNESS_CACHE[bg_image] = bg_img_brightness
                except: pass

        target_c = QColor(target_hex)
        target_brightness = (target_c.red() * 0.299 + target_c.green() * 0.587 + target_c.blue() * 0.114) * 255
        
        alpha_f = alpha / 100.0
        blend_brightness = (target_brightness * alpha_f) + (bg_img_brightness * (1.0 - alpha_f))
        
        # Calculate the base color (opposite of background)
        comp_color = cls.get_complementary_color(target_hex)
        
        # For subtext, just add transparency to whatever we decided
        if is_sub:
            c = QColor(comp_color)
            return f"rgba({c.red()}, {c.green()}, {c.blue()}, 0.6)"
        
        return comp_color

    @classmethod
    def get_panel_text_color(cls, solid_bg_hex: str, is_sub: bool = False) -> str:
        """Returns best text color for glass panels.
        
        Unlike get_smart_text_color, this ignores opacity entirely.
        Decision is based ONLY on the solid panel bg color's brightness.
        This prevents white-on-white issues when a light-colored panel
        is semi-transparent over a dark/unknown background image.
        """
        c = QColor(solid_bg_hex)
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        if is_sub:
            # Sub text: softer contrast
            return "rgba(255,255,255,0.65)" if brightness < 145 else "rgba(0,0,0,0.45)"
        else:
            return "#FFFFFF" if brightness < 145 else "#2D2D2D"

    @classmethod
    def get_contrast_color(cls, bg_hex: str) -> str:
        """Returns white or soft dark brown based on background brightness."""
        c = QColor(bg_hex)
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        # If background is light (high brightness), return deep mocha/brown for Kawaii feel
        return "#FFFFFF" if brightness < 160 else "#4A2C2C"

    @classmethod
    def get_subtext_contrast_color(cls, bg_hex: str) -> str:
        """Returns light grey or soft brown based on background brightness."""
        c = QColor(bg_hex)
        brightness = (c.red() * 299 + c.green() * 587 + c.blue() * 114) / 1000
        return "#B3B3B3" if brightness < 160 else "#8A6B6B"

    @classmethod
    def get_text_color(cls) -> str:
        """Alias for backward compatibility."""
        theme = cls.load_theme_config()
        return cls.get_contrast_color(theme.get("bg_color", cls.DEFAULT_BG))

    @classmethod
    def get_subtext_color(cls) -> str:
        """Alias for backward compatibility."""
        theme = cls.load_theme_config()
        return cls.get_subtext_contrast_color(theme.get("bg_color", cls.DEFAULT_BG))

    @classmethod
    def get_rgba(cls, hex_color: str, alpha: int) -> str:
        """Converts hex color to rgba(r, g, b, a) string."""
        c = QColor(hex_color)
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha/100.0})"

    @classmethod
    def apply_theme(cls, app_or_widget, qss_path: str):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                qss = f.read()
                
            theme = cls.load_theme_config()
            primary = theme.get("primary_color", cls.DEFAULT_PRIMARY)
            bg = theme.get("bg_color", cls.DEFAULT_BG)
            sidebar_bg = theme.get("sidebar_bg", bg)
            bottom_bg = theme.get("bottom_bg", bg)
            card_bg = theme.get("card_bg", cls.DEFAULT_CARD_BG)
            font = theme.get("font_family", cls.DEFAULT_FONT)
            bg_image = theme.get("bg_image", "")
            
            # Opacity
            win_alpha = theme.get("win_opacity", 100)
            side_alpha = theme.get("side_opacity", 100)
            bot_alpha = theme.get("bot_opacity", 100)
            card_alpha = theme.get("card_opacity", 100)
            
            # Contrast Colors
            win_text = cls.get_smart_text_color(bg, win_alpha)
            win_sub = cls.get_smart_text_color(bg, win_alpha, True)
            side_text = cls.get_smart_text_color(sidebar_bg, side_alpha)
            side_sub = cls.get_smart_text_color(sidebar_bg, side_alpha, True)
            bot_text = cls.get_smart_text_color(bottom_bg, bot_alpha)
            bot_sub = cls.get_smart_text_color(bottom_bg, bot_alpha, True)
            card_text = cls.get_smart_text_color(card_bg, card_alpha)
            card_sub = cls.get_smart_text_color(card_bg, card_alpha, True)
            
            primary_hover = cls.get_primary_hover_color()
            
            # Compute dialog text — always high-contrast (dark on light, light on dark)
            dialog_text = cls.get_contrast_color(bg)
            
            # Compute primary text color for buttons
            primary_text = cls.get_contrast_color(primary)

            qss = qss.replace("@PRIMARY_COLOR@", primary)
            qss = qss.replace("@PRIMARY_HOVER@", primary_hover)
            qss = qss.replace("@BG_COLOR@", cls.get_rgba(bg, win_alpha))
            qss = qss.replace("@SIDEBAR_BG@", cls.get_rgba(sidebar_bg, side_alpha))
            qss = qss.replace("@BOTTOM_BAR_BG@", cls.get_rgba(bottom_bg, bot_alpha))
            qss = qss.replace("@CARD_BG@", cls.get_rgba(card_bg, card_alpha))
            qss = qss.replace("@FONT_FAMILY@", font)

            qss = qss.replace("@TEXT_COLOR@", win_text)
            qss = qss.replace("@SUBTEXT_COLOR@", win_sub)
            qss = qss.replace("@SIDE_TEXT@", side_text)
            qss = qss.replace("@SIDE_SUB@", side_sub)
            qss = qss.replace("@BOT_TEXT@", bot_text)
            qss = qss.replace("@BOT_SUB@", bot_sub)
            qss = qss.replace("@CARD_TEXT@", card_text)
            qss = qss.replace("@CARD_SUB@", card_sub)
            qss = qss.replace("@DIALOG_BG@", cls.get_rgba(bg, 100))
            qss = qss.replace("@DIALOG_TEXT@", dialog_text)
            qss = qss.replace("@DIALOG_SUBTEXT@", cls.get_subtext_contrast_color(bg))
            qss = qss.replace("@PRIMARY_TEXT@", primary_text)

            app_or_widget.setStyleSheet(qss)
        except Exception as e:
            print(f"Theme apply error: {e}")
