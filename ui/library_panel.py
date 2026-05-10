"""
library_panel.py — Sol panel: albüme göre gruplu kütüphane + track play butonları.

Yapı (QTreeWidget):
  ┌─ Album Adı  —  Sanatçı  (top-level, açılır/kapanır)
  │   ├─ [▶] 01  Parça Adı              3:42
  │   ├─ [▶] 02  Parça Adı              4:11
  │   └─ …
  └─ …
"""
import threading
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QAbstractItemView, QSizePolicy, QApplication,
)
from PyQt5.QtGui import QColor, QFont, QIcon

from core.library import Library, Track
from core.metadata import TrackMetadata


# ── Metadata toplu yükleyici ─────────────────────────────────────────────
class BatchMetaLoader(QThread):
    """Tüm parçaların metadata'sını arka planda yükler."""
    finished = pyqtSignal()

    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self._tracks = tracks

    def run(self):
        for track in self._tracks:
            _ = track.metadata   # lazy load tetikle
        self.finished.emit()


# ── Parça satır widget'ı ─────────────────────────────────────────────────
class TrackRowWidget(QWidget):
    """Tek bir parça satırı: [▶] [no] [başlık]  [süre]"""
    play_clicked = pyqtSignal(object)   # Track

    def __init__(self, track: Track, parent=None):
        super().__init__(parent)
        self._track = track
        self.setObjectName("TrackRowWidget")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 12, 2)
        layout.setSpacing(6)

        # Play butonu
        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("TrackPlayBtn")
        self._play_btn.setFixedSize(26, 26)
        self._play_btn.setToolTip("Oynat")
        self._play_btn.clicked.connect(lambda: self.play_clicked.emit(self._track))

        # Parça numarası
        self._num_lbl = QLabel("")
        self._num_lbl.setObjectName("TrackNum")
        self._num_lbl.setFixedWidth(22)
        self._num_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Başlık
        self._title_lbl = QLabel(Path(track.path).stem)
        self._title_lbl.setObjectName("TrackItemTitle")
        self._title_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Süre
        self._dur_lbl = QLabel("—")
        self._dur_lbl.setObjectName("TimeLabel")
        self._dur_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._dur_lbl.setFixedWidth(42)

        layout.addWidget(self._play_btn)
        layout.addWidget(self._num_lbl)
        layout.addWidget(self._title_lbl)
        layout.addWidget(self._dur_lbl)

    def apply_meta(self, meta: TrackMetadata):
        num = str(meta.track_number) if meta.track_number else ""
        self._num_lbl.setText(num)
        self._title_lbl.setText(meta.title)
        self._dur_lbl.setText(meta.duration_str)

    def set_active(self, active: bool):
        """Oynatılan parçayı vurgula."""
        self._play_btn.setText("♪" if active else "▶")
        prop = "true" if active else "false"
        for w in (self._title_lbl, self._num_lbl):
            w.setProperty("active", prop)
            w.style().unpolish(w)
            w.style().polish(w)


# ── Kütüphane Paneli ─────────────────────────────────────────────────────
class LibraryPanel(QWidget):
    track_selected = pyqtSignal(object)   # Track

    def __init__(self, library: Library, parent=None):
        super().__init__(parent)
        self.setObjectName("LibraryPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(440)

        self._library = library
        self._loaders: list[BatchMetaLoader] = []
        self._row_widgets: dict[str, TrackRowWidget] = {}   # path → widget
        self._active_path: str | None = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Başlık + Ayarlar butonu ──
        header_row = QHBoxLayout()
        header_row.setContentsMargins(16, 18, 10, 8)
        header_row.setSpacing(8)

        header = QLabel("KÜTÜPHANE")
        header.setObjectName("LibraryHeader")

        self._folder_btn = QPushButton("📂")
        self._folder_btn.setObjectName("AddFolderBtn")
        self._folder_btn.setToolTip("Klasör Ekle")
        self._folder_btn.clicked.connect(self._add_folder)

        self._files_btn = QPushButton("➕")
        self._files_btn.setObjectName("AddFilesBtn")
        self._files_btn.setToolTip("Dosya Ekle")
        self._files_btn.clicked.connect(self._add_files)

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setObjectName("ShuffleBtn")   # aynı stil
        self._settings_btn.setToolTip("Ayarlar (Last.fm vb.)")
        self._settings_btn.setFixedSize(30, 30)

        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self._folder_btn)
        header_row.addWidget(self._files_btn)
        header_row.addWidget(self._settings_btn)
        layout.addLayout(header_row)

        # ── Sayaç + Temizle ──
        info_row = QHBoxLayout()
        info_row.setContentsMargins(14, 0, 10, 6)

        self._count_lbl = QLabel("0 parça")
        self._count_lbl.setObjectName("StatusLabel")

        self._clear_btn = QPushButton("Temizle")
        self._clear_btn.setObjectName("ClearBtn")
        self._clear_btn.clicked.connect(self._clear)

        info_row.addWidget(self._count_lbl)
        info_row.addStretch()
        info_row.addWidget(self._clear_btn)
        layout.addLayout(info_row)

        # ── Ağaç ──
        self._tree = QTreeWidget()
        self._tree.setObjectName("TrackList")
        self._tree.setHeaderHidden(True)
        self._tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tree.setIndentation(0)
        self._tree.setAnimated(True)
        layout.addWidget(self._tree)

    # ------------------------------------------------------------------ #
    # Dosya ekleme
    # ------------------------------------------------------------------ #
    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if folder:
            new = self._library.add_folder(folder)
            self._load_and_rebuild(new)

    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "FLAC Dosyaları Seç", "", "FLAC Dosyaları (*.flac)"
        )
        if paths:
            self.add_paths(paths)

    def add_paths(self, paths: list[str]):
        """Kayıtlı yollardan kütüphaneye parça ekler."""
        if paths:
            new = self._library.add_files(paths)
            self._load_and_rebuild(new)

    def _clear(self):
        self._library.clear()
        self._tree.clear()
        self._row_widgets.clear()
        self._count_lbl.setText("0 parça")

    # ------------------------------------------------------------------ #
    # Metadata yükle → ağacı yeniden kur
    # ------------------------------------------------------------------ #
    def _load_and_rebuild(self, new_tracks: list[Track]):
        if not new_tracks:
            return
        self._folder_btn.setEnabled(False)
        self._files_btn.setEnabled(False)
        self._count_lbl.setText("Yükleniyor…")

        loader = BatchMetaLoader(self._library.tracks, self)
        loader.finished.connect(self._on_meta_loaded)
        self._loaders.append(loader)
        loader.start()

    @pyqtSlot()
    def _on_meta_loaded(self):
        self._rebuild_tree()
        self._folder_btn.setEnabled(True)
        self._files_btn.setEnabled(True)
        n = len(self._library.tracks)
        self._count_lbl.setText(f"{n} parça")

    # ------------------------------------------------------------------ #
    # Ağaç kurma
    # ------------------------------------------------------------------ #
    def _rebuild_tree(self):
        self._tree.clear()
        self._row_widgets.clear()

        # Albümlere göre grupla → {(artist, album): [Track]}
        albums: dict[tuple, list[Track]] = {}
        for track in self._library.tracks:
            m = track.metadata
            key = (m.artist, m.album)
            albums.setdefault(key, []).append(track)

        for (artist, album), tracks in sorted(albums.items()):
            # Albüm başlığı
            album_item = QTreeWidgetItem(self._tree)
            album_item.setFlags(
                Qt.ItemIsEnabled | Qt.ItemIsDropEnabled
            )
            album_label = f"  {album}"
            if artist and artist != "Unknown Artist":
                album_label += f"    {artist}"
            album_item.setText(0, album_label)
            album_item.setData(0, Qt.UserRole, "album_header")

            font = QFont()
            font.setBold(True)
            album_item.setFont(0, font)
            album_item.setForeground(0, QColor("#c4b5fd"))
            album_item.setExpanded(True)

            # Parçaları track_number'a göre sırala
            sorted_tracks = sorted(tracks, key=lambda t: t.metadata.track_number)

            for track in sorted_tracks:
                track_item = QTreeWidgetItem(album_item)
                track_item.setData(0, Qt.UserRole, track)
                track_item.setSizeHint(0, QSize(0, 48))

                widget = TrackRowWidget(track)
                widget.apply_meta(track.metadata)
                widget.play_clicked.connect(self.track_selected.emit)
                self._tree.setItemWidget(track_item, 0, widget)
                self._row_widgets[track.path] = widget

        # Aktif parçayı yeniden vurgula
        if self._active_path and self._active_path in self._row_widgets:
            self._row_widgets[self._active_path].set_active(True)

    # ------------------------------------------------------------------ #
    # Dışarıdan çağrılan metodlar
    # ------------------------------------------------------------------ #
    def highlight_track(self, track: Track):
        """Oynatılan parçayı vurgula."""
        # Eskiyi temizle
        if self._active_path and self._active_path in self._row_widgets:
            self._row_widgets[self._active_path].set_active(False)

        self._active_path = track.path

        if track.path in self._row_widgets:
            widget = self._row_widgets[track.path]
            widget.set_active(True)
            # Ağaçta bul ve scroll et
            it = self._find_item(track)
            if it:
                self._tree.scrollToItem(it)
                self._tree.setCurrentItem(it)

    def _find_item(self, track: Track) -> QTreeWidgetItem | None:
        root = self._tree.invisibleRootItem()
        for i in range(root.childCount()):
            album_item = root.child(i)
            for j in range(album_item.childCount()):
                child = album_item.child(j)
                if child.data(0, Qt.UserRole) is track:
                    return child
        return None

    @property
    def settings_btn(self) -> QPushButton:
        return self._settings_btn
