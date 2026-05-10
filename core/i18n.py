import json
import os
import sys

def _get_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return "config.json"

CONFIG_PATH = _get_config_path()

class I18n:
    _cached_lang = None  # In-memory cache to avoid reading JSON on every t() call
    LANGUAGES = {
        "tr": {
            "home": "Ana Sayfa",
            "stats": "İstatistikler",
            "add_music": "Müzik Ekle",
            "clear_library": "Kitaplığı Temizle",
            "settings": "Ayarlar",
            "search": "Ara...",
            "save": "Kaydet",
            "cancel": "İptal",
            "appearance": "Görünüm",
            "theme_presets": "Tema Şablonları",
            "theme_description": "Önceden tanımlı şablonları veya klasik modları seç:",
            "custom_settings": "Detaylı Özelleştirme",
            "accent_color": "Vurgu Rengi",
            "bg_color": "Arkaplan Rengi",
            "panel_color": "Panel Rengi",
            "font": "Yazı Tipi",
            "language": "Dil",
            "scrobbling": "Last.fm Scrobbling",
            "test_connect": "Bağlan ve Test Et",
            "now_playing": "ŞİMDİ ÇALIYOR",
            "queue": "SIRADAKİ",
            "top_artists": "TOP SANATÇILAR",
            "top_albums": "TOP ALBÜMLER",
            "play": "Oynat",
            "pause": "Duraklat",
            "next": "Sonraki",
            "prev": "Önceki",
            "remove_album": "Albümü Kaldır",
            "play_album": "Albümü Oynat",
            "add_to_queue": "Sıraya Ekle",
            "play_next": "Sıradakini Oynat",
            "theme_applied": "Temanız başarıyla uygulandı!",
            "restart_msg": "Tam güncelleme için uygulamayı yeniden başlatmanız önerilir.",
            "quick_picks": "Hızlı Seçimler",
            "play_all": "Tümünü Oynat",
            "your_library": "Müzik Kitaplığın",
            "search_results": "Arama Sonuçları",
            "results_for": "'{query}' için sonuçlar",
            "tracks": "Parçalar",
            "albums": "Albümler",
            "unknown_album": "Bilinmeyen Albüm",
            "album": "ALBÜM",
            "remove_from_library": "Kitaplıktan Kaldır",
            "remove_album_from_library": "Albümü Kitaplıktan Kaldır",
            "help": "Yardım",
            "background_image": "Arka Plan Görseli",
            "general": "Genel",
            "items_added": "{count} öğe kütüphaneye eklendi.",
            "no_song": "Şarkı Seçilmedi",
            "artist_label": "Sanatçı",
            "separate_album": "Tümünü Ayrıştır"
        },
        "en": {
            "home": "Home",
            "stats": "Statistics",
            "add_music": "Add Music",
            "clear_library": "Clear Library",
            "settings": "Settings",
            "search": "Search...",
            "save": "Save",
            "cancel": "Cancel",
            "appearance": "Appearance",
            "theme_presets": "Theme Presets",
            "theme_description": "Choose from predefined templates or classic modes:",
            "custom_settings": "Custom Settings",
            "accent_color": "Accent Color",
            "bg_color": "Background Color",
            "panel_color": "Panel Color",
            "font": "Font",
            "language": "Language",
            "scrobbling": "Last.fm Scrobbling",
            "test_connect": "Connect & Test",
            "now_playing": "NOW PLAYING",
            "queue": "QUEUE",
            "top_artists": "TOP ARTISTS",
            "top_albums": "TOP ALBUMS",
            "play": "Play",
            "pause": "Pause",
            "next": "Next",
            "prev": "Previous",
            "remove_album": "Remove Album",
            "play_album": "Play Album",
            "add_to_queue": "Add to Queue",
            "play_next": "Play Next",
            "theme_applied": "Theme applied successfully!",
            "restart_msg": "Restarting the app is recommended for a full update.",
            "quick_picks": "Quick Picks",
            "play_all": "Play All",
            "your_library": "Your Library",
            "search_results": "Search Results",
            "results_for": "Results for '{query}'",
            "tracks": "Tracks",
            "albums": "Albums",
            "unknown_album": "Unknown Album",
            "album": "ALBUM",
            "remove_from_library": "Remove from Library",
            "remove_album_from_library": "Remove Album from Library",
            "help": "Help",
            "background_image": "Background Image",
            "general": "General",
            "items_added": "{count} items added to library.",
            "no_song": "No Song Selected",
            "artist_label": "Artist",
            "separate_album": "Separate Album"
        }
    }

    @classmethod
    def get_lang(cls) -> str:
        if cls._cached_lang is not None:
            return cls._cached_lang
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cls._cached_lang = data.get("language", "tr")
                    return cls._cached_lang
        except Exception:
            pass
        cls._cached_lang = "tr"
        return "tr"

    @classmethod
    def set_lang(cls, lang: str):
        cls._cached_lang = lang  # Update cache immediately
        data = {}
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except Exception:
            pass
        
        data["language"] = lang
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def t(cls, key: str) -> str:
        lang = cls.get_lang()
        return cls.LANGUAGES.get(lang, cls.LANGUAGES["en"]).get(key, key)
