"""
main.py — Lossless Player giriş noktası.

Çalıştırma:
    python main.py
"""
import sys
import os

# Proje kök dizinini path'e ekle (core/ ve ui/ modüllerini bulmak için)
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont, QIcon

from ui.main_window import MainWindow
from resource_path import resource_path


def main():
    # HiDPI desteği
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,   True)

    app = QApplication(sys.argv)
    app.setApplicationName("A-Bir Player")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("LosslessPlayer")
    
    # Set app icon
    icon_path = resource_path(os.path.join("ui", "logo.png"))
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Global Exception Handler
    import traceback
    def exception_hook(exctype, value, tb):
        err = "".join(traceback.format_exception(exctype, value, tb))
        print(err)
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write("\n" + "="*40 + "\n")
            f.write(f"CRASH AT: {os.times()}\n")
            f.write(err)
        sys.exit(1)
    
    sys.excepthook = exception_hook

    if os.name == 'nt':
        import ctypes
        myappid = 'LosslessPlayer.App.1' 
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Varsayılan font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # QSS yükle
    qss_path = resource_path(os.path.join("ui", "styles.qss"))
    try:
        from core.theme_manager import ThemeManager
        ThemeManager.apply_theme(app, qss_path)
    except Exception as e:
        print(f"[UYARI] Tema yüklenemedi: {e}")

    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception:
        exception_hook(*sys.exc_info())


if __name__ == "__main__":
    main()
