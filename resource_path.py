"""
resource_path.py — PyInstaller uyumlu dosya yolu çözücü.

PyInstaller --onefile modunda tüm dosyalar geçici bir _MEIPASS
klasörüne çıkartılır. Bu modül, hem dev hem de frozen (exe) 
modda doğru dosya yollarını döndürür.
"""
import sys
import os


def resource_path(relative_path: str) -> str:
    """PyInstaller frozen exe veya dev modda doğru dosya yolunu döndürür."""
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş — _MEIPASS geçici dizini
        base_path = sys._MEIPASS
    else:
        # Normal Python çalışması — proje kök dizini
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_user_data_dir() -> str:
    """Kullanıcı verileri için yazılabilir dizin döndürür (config, db vs.)
    
    Frozen modda exe yanındaki klasörü kullanır.
    Dev modda proje kök dizinini kullanır.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
