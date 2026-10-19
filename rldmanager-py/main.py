#!/usr/bin/env python3

import sys
import os
from dataclasses import dataclass, field

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QLabel, QDialog, QDialogButtonBox,
    QSizePolicy, QStatusBar, QHeaderView, QAbstractItemView,
    QMessageBox, QTableWidgetItem, QTabWidget,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui  import QAction, QKeySequence, QColor, QIcon, QFont
from PyQt6.QtWidgets import QFrame

from qfluentwidgets import (
    TableWidget, LineEdit, TextEdit, PushButton, ComboBox,
    FluentIcon, setTheme, Theme, isDarkTheme,
    SmoothScrollDelegate, InfoBar, InfoBarPosition, ProgressBar,
)

from rld_engine import (
    RLD, KNOWN_KEYS, KeyFinder,
    extract_to_text, parse_text_block, apply_translations,
)
try:
    import gyu_engine
    _GYU_AVAILABLE = True
except Exception:
    _GYU_AVAILABLE = False
import i18n


def resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def app_icon() -> QIcon:
    ico = resource_path("icon.ico")
    if os.path.exists(ico):
        return QIcon(ico)
    return QIcon()


@dataclass
class ScriptTab:
    path:     str
    filename: str
    rld:      RLD
    strings:  list[str]
    speakers: list[str]
    genders:  list[str]
    modified: bool = False


class FileLoaderWorker(QThread):
    file_loaded  = pyqtSignal(object)
    file_error   = pyqtSignal(str, str)
    all_done     = pyqtSignal()

    def __init__(self, paths: list[str], parent=None):
        super().__init__(parent)
        self._paths = paths

    def run(self):
        for path in self._paths:
            try:
                data     = open(path, "rb").read()
                rld      = RLD(data)
                strings  = rld.import_strings()
                speakers = rld.get_speakers()
                genders  = rld.get_genders()
                fname    = os.path.basename(path)
                tab      = ScriptTab(path, fname, rld, strings, speakers, genders)
                self.file_loaded.emit(tab)
            except Exception as ex:
                self.file_error.emit(os.path.basename(path), str(ex))
        self.all_done.emit()


class SaveAllWorker(QThread):
    file_saved  = pyqtSignal(str)
    file_error  = pyqtSignal(str, str)
    all_done    = pyqtSignal(int)

    def __init__(self, jobs: list[tuple], parent=None):
        super().__init__(parent)
        self._jobs = jobs

    def run(self):
        saved = 0
        for tab, strings, out_path in self._jobs:
            try:
                data = tab.rld.export_strings(strings)
                with open(out_path, "wb") as f:
                    f.write(data)
                self.file_saved.emit(tab.filename)
                saved += 1
            except Exception as ex:
                self.file_error.emit(tab.filename, str(ex))
        self.all_done.emit(saved)


class BruteForceWorker(QThread):
    progress_signal = pyqtSignal(int, int)
    done_signal     = pyqtSignal(list)

    def __init__(self, script: bytes, parent=None):
        super().__init__(parent)
        self._finder = KeyFinder(script)
        self._finder.on_progress = lambda d, t: self.progress_signal.emit(d, t)
        self._finder.on_done     = lambda k:    self.done_signal.emit(k)

    def run(self):
        self._finder.start()
        if self._finder._thread:
            self._finder._thread.join()

    def stop(self):
        self._finder.stop()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.setWindowTitle(i18n.t("about_title"))
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        title_label = QLabel(f"<b>RLD Manager</b>", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px;")
        lay.addWidget(title_label)

        version_label = QLabel(i18n.t("about_version"), self)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(version_label)

        sep1 = QFrame(self)
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        lay.addWidget(sep1)

        desc_label = QLabel(i18n.t("about_description"), self)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(desc_label)

        credits_header = QLabel(f"<b>{i18n.t('about_credits')}</b>", self)
        lay.addWidget(credits_header)

        credits_label = QLabel(i18n.t("about_credits_text"), self)
        credits_label.setWordWrap(True)
        credits_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        credits_label.setStyleSheet("font-family: monospace; font-size: 11px;")
        lay.addWidget(credits_label)

        btns = QDialogButtonBox(parent=self)
        close_btn = btns.addButton(
            i18n.t("about_close"), QDialogButtonBox.ButtonRole.AcceptRole)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(btns)


class KeySelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_key: int = 0
        self._build()

    def _build(self):
        self.setWindowTitle(i18n.t("dlg_select_game"))
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)

        self.combo = ComboBox(self)
        for name in KNOWN_KEYS:
            self.combo.addItem(name)
        self.combo.addItem(i18n.t("dlg_other"))
        self.combo.currentIndexChanged.connect(self._on_combo)
        lay.addWidget(self.combo)

        row = QHBoxLayout()
        row.addWidget(QLabel(i18n.t("dlg_key_label"), self))
        self.key_edit = LineEdit(self)
        self.key_edit.setPlaceholderText("0x00000000")
        self.key_edit.setEnabled(False)
        row.addWidget(self.key_edit)
        lay.addLayout(row)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel, parent=self)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _on_combo(self, _):
        other = self.combo.currentText() == i18n.t("dlg_other")
        self.key_edit.setEnabled(other)
        self.key_edit.clear()

    def _on_accept(self):
        if self.key_edit.isEnabled():
            raw = self.key_edit.text().strip()
            try:
                self.selected_key = int(raw, 16) if raw.lower().startswith("0x") else int(raw)
                self.accept()
            except ValueError:
                self.reject()
        else:
            name = self.combo.currentText()
            if name in KNOWN_KEYS:
                self.selected_key = KNOWN_KEYS[name]
                self.accept()
            else:
                self.reject()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(app_icon())
        self._tabs:       list[ScriptTab]          = []
        self._brute:      BruteForceWorker | None  = None
        self._loader:     FileLoaderWorker | None  = None
        self._saver:      SaveAllWorker    | None  = None
        self._load_errors: list[str]               = []
        self._save_progress: int                   = 0
        self._save_errors:   list[str]             = []
        self._setup_ui()
        self._setup_menu()
        self._retranslate()

    def _setup_ui(self):
        self.setMinimumSize(960, 620)

        from qfluentwidgets import CommandBar
        self._toolbar = CommandBar(self)
        self._toolbar.setFixedHeight(44)

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 4)
        root.setSpacing(6)

        root.addWidget(self._toolbar)

        search_row = QHBoxLayout()
        self.search_edit = LineEdit(self)
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedHeight(36)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_edit)
        root.addLayout(search_row)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._run_filter)

        self.splitter = QSplitter(Qt.Orientation.Vertical, self)
        root.addWidget(self.splitter, stretch=1)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.splitter.addWidget(self.tab_widget)

        from qfluentwidgets import ElevatedCardWidget
        edit_widget = ElevatedCardWidget(self)
        edit_lay    = QVBoxLayout(edit_widget)
        edit_lay.setContentsMargins(0, 4, 0, 0)
        from qfluentwidgets import BodyLabel
        self.edit_label = BodyLabel(self)
        edit_lay.addWidget(self.edit_label)
        self.dialog_edit = TextEdit(self)
        self.dialog_edit.setMaximumHeight(120)
        edit_lay.addWidget(self.dialog_edit)
        self.dialog_edit.installEventFilter(self)

        btn_row = QHBoxLayout()
        self.commit_btn = PushButton(FluentIcon.ACCEPT, "", self)
        self.commit_btn.clicked.connect(self._commit_and_advance)
        btn_row.addWidget(self.commit_btn)
        btn_row.addStretch()
        edit_lay.addLayout(btn_row)
        self.splitter.addWidget(edit_widget)
        self.splitter.setSizes([420, 180])

        self.progress_bar = ProgressBar(self)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        self.status_bar   = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        from qfluentwidgets import CaptionLabel
        self.status_label = CaptionLabel(self)
        self.status_bar.addWidget(self.status_label)

    def _make_table(self) -> TableWidget:
        t = TableWidget()
        t.setColumnCount(4)
        t.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        hdr = t.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        t.setHorizontalHeaderLabels([
            i18n.t("col_index"),
            i18n.t("col_file"),
            i18n.t("col_speaker"),
            i18n.t("col_dialogue"),
        ])
        t.itemSelectionChanged.connect(self._on_row_selected)
        t._scroll_delegate = SmoothScrollDelegate(t)
        return t

    def _setup_menu(self):
        mb = self.menuBar()

        self.menu_file  = mb.addMenu("")
        self.act_open   = QAction(FluentIcon.FOLDER.icon(), "", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self._open_files)
        self.act_save   = QAction(FluentIcon.SAVE.icon(), "", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self._save_current)
        self.act_save_all = QAction(FluentIcon.SAVE_AS.icon(), "", self)
        self.act_save_all.triggered.connect(self._save_all)
        self.menu_file.addActions([self.act_open, self.act_save, self.act_save_all])

        self.menu_tools      = mb.addMenu("")
        self.act_export_txt  = QAction(FluentIcon.DOCUMENT.icon(), "", self)
        self.act_export_txt.triggered.connect(self._export_text)
        self.act_export_plain = QAction(FluentIcon.COPY.icon(), "", self)
        self.act_export_plain.triggered.connect(self._export_plain_text)
        self.act_import_txt  = QAction(FluentIcon.ADD.icon(), "", self)
        self.act_import_txt.triggered.connect(self._import_text)
        self.act_find_key    = QAction(FluentIcon.SEARCH.icon(), "", self)
        self.act_find_key.triggered.connect(self._find_key)
        self.act_crypt       = QAction(FluentIcon.CODE.icon(), "", self)
        self.act_crypt.triggered.connect(self._crypt)
        self.menu_tools.addActions([self.act_export_txt, self.act_export_plain,
                                     self.act_import_txt, self.act_find_key, self.act_crypt])
        if _GYU_AVAILABLE:
            self.act_decode_gyu = QAction(FluentIcon.PHOTO.icon(), "", self)
            self.act_decode_gyu.triggered.connect(self._decode_gyu)
            self.menu_tools.addAction(self.act_decode_gyu)

        self.menu_settings = mb.addMenu("")
        theme_menu = self.menu_settings.addMenu("")
        self.act_light  = QAction(FluentIcon.BRIGHTNESS.icon(), "", self)
        self.act_light.triggered.connect(lambda: self._set_theme("light"))
        self.act_dark   = QAction(FluentIcon.BRIGHTNESS.icon(), "", self)
        self.act_dark.triggered.connect(lambda: self._set_theme("dark"))
        self.act_system = QAction(FluentIcon.SETTING.icon(), "", self)
        self.act_system.triggered.connect(lambda: self._set_theme("system"))
        theme_menu.addActions([self.act_light, self.act_dark, self.act_system])
        self._theme_menu = theme_menu

        lang_menu = self.menu_settings.addMenu("")
        self.act_lang_en    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_en.triggered.connect(lambda: self._set_lang("en"))
        self.act_lang_es    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_es.triggered.connect(lambda: self._set_lang("es"))
        self.act_lang_pt    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_pt.triggered.connect(lambda: self._set_lang("pt"))
        self.act_lang_pt_br = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_pt_br.triggered.connect(lambda: self._set_lang("pt_br"))
        self.act_lang_fr    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_fr.triggered.connect(lambda: self._set_lang("fr"))
        self.act_lang_it    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_it.triggered.connect(lambda: self._set_lang("it"))
        self.act_lang_de    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_de.triggered.connect(lambda: self._set_lang("de"))
        self.act_lang_ru    = QAction(FluentIcon.LANGUAGE.icon(), "", self)
        self.act_lang_ru.triggered.connect(lambda: self._set_lang("ru"))
        lang_menu.addActions([self.act_lang_en, self.act_lang_es, self.act_lang_pt,
                              self.act_lang_pt_br, self.act_lang_fr, self.act_lang_it,
                              self.act_lang_de, self.act_lang_ru])
        self._lang_menu = lang_menu

        self.menu_help = mb.addMenu("")
        self.act_about = QAction(FluentIcon.INFO.icon(), "", self)
        self.act_about.triggered.connect(self._show_about)
        self.menu_help.addAction(self.act_about)

        self._toolbar.addAction(self.act_open)
        self._toolbar.addAction(self.act_save)
        self._toolbar.addAction(self.act_save_all)
        self._toolbar.addSeparator()
        self._toolbar.addAction(self.act_export_txt)
        self._toolbar.addAction(self.act_export_plain)

    def _retranslate(self):
        self.setWindowTitle(i18n.t("app_title"))
        self.search_edit.setPlaceholderText(i18n.t("search_placeholder"))
        self.edit_label.setText(i18n.t("edit_label"))
        self.commit_btn.setText(i18n.t("commit_next"))

        self.menu_file.setTitle(i18n.t("menu_file"))
        self.act_open.setText(i18n.t("menu_open"))
        self.act_save.setText(i18n.t("menu_save"))
        self.act_save_all.setText(i18n.t("menu_save_all"))
        self.menu_tools.setTitle(i18n.t("menu_tools"))
        self.act_export_txt.setText(i18n.t("menu_export_text"))
        self.act_export_plain.setText(i18n.t("menu_export_plain"))
        self.act_import_txt.setText(i18n.t("menu_import_text"))
        self.act_find_key.setText(i18n.t("menu_find_key"))
        self.act_crypt.setText(i18n.t("menu_crypt"))
        self.menu_settings.setTitle(i18n.t("menu_settings"))
        self._theme_menu.setTitle(i18n.t("menu_theme"))
        self.act_light.setText(i18n.t("theme_light"))
        self.act_dark.setText(i18n.t("theme_dark"))
        self.act_system.setText(i18n.t("theme_system"))
        self._lang_menu.setTitle(i18n.t("menu_language"))
        self.act_lang_en.setText(i18n.t("lang_en"))
        self.act_lang_es.setText(i18n.t("lang_es"))
        self.act_lang_pt.setText(i18n.t("lang_pt"))
        self.act_lang_pt_br.setText(i18n.t("lang_pt_br"))
        self.act_lang_fr.setText(i18n.t("lang_fr"))
        self.act_lang_it.setText(i18n.t("lang_it"))
        self.act_lang_de.setText(i18n.t("lang_de"))
        self.act_lang_ru.setText(i18n.t("lang_ru"))
        self.menu_help.setTitle(i18n.t("menu_help"))
        self.act_about.setText(i18n.t("menu_about"))

        if not self._tabs:
            self.status_label.setText(i18n.t("status_ready"))

        for idx, tab in enumerate(self._tabs):
            self.tab_widget.setTabText(idx, tab.filename)
            table = self.tab_widget.widget(idx)
            if isinstance(table, TableWidget):
                table.setHorizontalHeaderLabels([
                    i18n.t("col_index"), i18n.t("col_file"),
                    i18n.t("col_speaker"), i18n.t("col_dialogue"),
                ])

    def _set_theme(self, mode: str):
        setTheme({"light": Theme.LIGHT, "dark": Theme.DARK, "system": Theme.AUTO}.get(mode, Theme.AUTO))

    def _set_lang(self, lang: str):
        i18n.set_lang(lang)  # type: ignore
        self._retranslate()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _current_table(self) -> TableWidget | None:
        w = self.tab_widget.currentWidget()
        return w if isinstance(w, TableWidget) else None

    def _current_script(self) -> ScriptTab | None:
        idx = self.tab_widget.currentIndex()
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx]
        return None

    def _open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, i18n.t("dlg_open_title"), "",
            i18n.t("dlg_filter"),
        )
        if not paths:
            return
        self.act_open.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(i18n.t("status_loading", n=len(paths)))
        self._load_errors = []
        self._loader = FileLoaderWorker(paths, self)
        self._loader.file_loaded.connect(self._on_file_loaded)
        self._loader.file_error.connect(self._on_file_load_error)
        self._loader.all_done.connect(self._on_loading_done)
        self._loader.start()

    def _on_file_loaded(self, tab: ScriptTab):
        self._tabs.append(tab)
        table = self._make_table()
        self._populate_table(table, tab)
        self.tab_widget.addTab(table, tab.filename)
        self.status_label.setText(i18n.t("status_loaded_file",
                                          name=tab.filename, n=len(tab.strings)))

    def _on_file_load_error(self, basename: str, msg: str):
        self._load_errors.append(f"{basename}: {msg}")

    def _on_loading_done(self):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.act_open.setEnabled(True)
        if self._load_errors:
            QMessageBox.warning(self, i18n.t("dlg_error"), "\n".join(self._load_errors))
        n = len(self._tabs)
        self.status_label.setText(i18n.t("status_files", n=n))
        if n:
            self.tab_widget.setCurrentIndex(n - 1)

    def _populate_table(self, table: TableWidget, tab: ScriptTab):
        table.blockSignals(True)
        table.setUpdatesEnabled(False)
        try:
            table.clearContents()
            table.setRowCount(len(tab.strings))
            for i, (spk, dlg) in enumerate(zip(tab.speakers, tab.strings)):
                table.setItem(i, 0, QTableWidgetItem(str(i)))
                table.setItem(i, 1, QTableWidgetItem(tab.filename))
                table.setItem(i, 2, QTableWidgetItem(spk))
                table.setItem(i, 3, QTableWidgetItem(dlg))
        finally:
            table.setUpdatesEnabled(True)
            table.blockSignals(False)
        table.resizeRowsToContents()

    def _collect_strings(self, table: TableWidget) -> list[str]:
        out = []
        for i in range(table.rowCount()):
            item = table.item(i, 3)
            out.append(item.text() if item else "")
        return out

    def _on_search_text_changed(self, text: str):
        self._search_timer.start()

    def _run_filter(self):
        self._filter_table(self.search_edit.text())

    def _filter_table(self, text: str):
        table = self._current_table()
        if not table:
            return
        text = (text or "").lower()
        table.setUpdatesEnabled(False)
        try:
            for row in range(table.rowCount()):
                match = any(
                    (table.item(row, col) is not None and
                     text in table.item(row, col).text().lower())
                    for col in range(table.columnCount())
                )
                table.setRowHidden(row, bool(text) and not match)
        finally:
            table.setUpdatesEnabled(True)

    def _on_tab_changed(self, _):
        self.dialog_edit.clear()
        self._filter_table(self.search_edit.text())

    def _on_row_selected(self):
        table = self._current_table()
        tab   = self._current_script()
        if not table or not tab:
            return
        row = table.currentRow()
        if row < 0:
            return
        item = table.item(row, 3)
        spk  = table.item(row, 2)
        self.dialog_edit.setPlainText(item.text() if item else "")
        self.setWindowTitle(i18n.t("window_title_id",
                                    id=row,
                                    speaker=spk.text() if spk else "—"))

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self.dialog_edit and event.type() == QEvent.Type.KeyPress:
            ke = event
            if ke.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (ke.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                self._commit_and_advance()
                return True
        return super().eventFilter(obj, event)

    def _commit_and_advance(self):
        table = self._current_table()
        tab   = self._current_script()
        if not table or not tab:
            return
        row = table.currentRow()
        if row < 0:
            return
        new_text = self.dialog_edit.toPlainText()
        table.setItem(row, 3, QTableWidgetItem(new_text))
        if 0 <= row < len(tab.strings):
            tab.strings[row] = new_text
            tab.modified = True
        next_row = row + 1
        if next_row < table.rowCount():
            table.selectRow(next_row)
            table.scrollToItem(table.item(next_row, 0))

    def _save_tab(self, idx: int):
        tab   = self._tabs[idx]
        table = self.tab_widget.widget(idx)
        if not isinstance(table, TableWidget):
            return
        strings = self._collect_strings(table)
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("dlg_save_title"),
            tab.path, i18n.t("dlg_filter"))
        if not path:
            return
        try:
            out = tab.rld.export_strings(strings)
            open(path, "wb").write(out)
            tab.modified = False
            InfoBar.success(title="", content=i18n.t("dlg_saved"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))

    def _save_current(self):
        idx = self.tab_widget.currentIndex()
        if 0 <= idx < len(self._tabs):
            self._save_tab(idx)

    def _save_all(self):
        if not self._tabs:
            InfoBar.warning(title="", content=i18n.t("dlg_no_tabs"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
            return
        dest_dir = QFileDialog.getExistingDirectory(
            self, i18n.t("dlg_save_all_title"),
            os.path.dirname(self._tabs[0].path),
        )
        if not dest_dir:
            return
        jobs = []
        for idx, tab in enumerate(self._tabs):
            table = self.tab_widget.widget(idx)
            strings = (
                self._collect_strings(table)
                if isinstance(table, TableWidget)
                else tab.strings
            )
            out_path = os.path.join(dest_dir, tab.filename)
            jobs.append((tab, strings, out_path))
        self._set_saving_ui(True, len(jobs))
        self._saver = SaveAllWorker(jobs, self)
        self._saver.file_saved.connect(self._on_file_saved)
        self._saver.file_error.connect(self._on_save_error)
        self._saver.all_done.connect(self._on_save_all_done)
        self._saver.start()

    def _set_saving_ui(self, busy: bool, total: int = 0):
        self.act_save_all.setEnabled(not busy)
        self.act_save.setEnabled(not busy)
        self.progress_bar.setVisible(busy)
        if busy:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(0)
            self._save_progress = 0

    def _on_file_saved(self, basename: str):
        self._save_progress += 1
        self.progress_bar.setValue(self._save_progress)
        self.status_label.setText(
            i18n.t("status_saving", done=self._save_progress,
                   total=self.progress_bar.maximum()))

    def _on_save_error(self, basename: str, msg: str):
        self._save_errors.append(f"{basename}: {msg}")

    def _on_save_all_done(self, saved: int):
        self._set_saving_ui(False)
        errors = self._save_errors[:]
        self._save_errors.clear()
        for tab in self._tabs:
            tab.modified = False
        self.status_label.setText(i18n.t("status_files", n=len(self._tabs)))
        if errors:
            QMessageBox.warning(self, i18n.t("dlg_error"), "\n".join(errors))
        else:
            InfoBar.success(
                title="", content=i18n.t("dlg_saved_all", n=saved),
                parent=self, position=InfoBarPosition.BOTTOM, duration=2500)

    def _export_text(self):
        if not self._tabs:
            InfoBar.warning(title="", content=i18n.t("dlg_no_tabs"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("dlg_export_title"), "export.txt",
            i18n.t("dlg_txt_filter"))
        if not path:
            return
        all_lines: list[str] = []
        for tab in self._tabs:
            lines = extract_to_text(
                tab.rld, tab.filename,
                tab.strings, tab.speakers, tab.genders)
            all_lines.extend(lines)
            all_lines.append("")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(all_lines))
            InfoBar.success(title="", content=i18n.t("dlg_done"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))

    def _export_plain_text(self):
        if not self._tabs:
            InfoBar.warning(title="", content=i18n.t("dlg_no_tabs"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
            return
        path, _ = QFileDialog.getSaveFileName(
            self, i18n.t("dlg_export_plain_title"), "export_plain.txt",
            i18n.t("dlg_txt_filter"))
        if not path:
            return
        lines: list[str] = []
        for tab in self._tabs:
            for text in tab.strings:
                lines.append(text)
            lines.append("")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            InfoBar.success(title="", content=i18n.t("status_exported_plain"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))

    def _import_text(self):
        if not self._tabs:
            InfoBar.warning(title="", content=i18n.t("dlg_no_tabs"),
                            parent=self, position=InfoBarPosition.BOTTOM, duration=2000)
            return
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("dlg_import_title"), "",
            i18n.t("dlg_txt_filter"))
        if not path:
            return
        try:
            content = open(path, "r", encoding="utf-8").read()
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))
            return
        translations = parse_text_block(content)
        total_applied = 0
        for t_idx, tab in enumerate(self._tabs):
            if tab.filename not in translations:
                continue
            tr_map   = translations[tab.filename]
            merged   = apply_translations(tab.rld, tab.strings, tr_map)
            tab.strings  = merged
            tab.modified = True
            total_applied += len(tr_map)
            table = self.tab_widget.widget(t_idx)
            if isinstance(table, TableWidget):
                for row_idx, text in enumerate(merged):
                    item = table.item(row_idx, 3)
                    if item:
                        item.setText(text)
                    else:
                        table.setItem(row_idx, 3, QTableWidgetItem(text))
                for row_idx in tr_map:
                    for col in range(table.columnCount()):
                        cell = table.item(row_idx, col)
                        if cell:
                            cell.setForeground(QColor("#4CAF50"))
        if total_applied:
            InfoBar.success(
                title="", content=i18n.t("dlg_imported", n=total_applied),
                parent=self, position=InfoBarPosition.BOTTOM, duration=3000)
        else:
            InfoBar.warning(
                title="", content=i18n.t("dlg_no_match"),
                parent=self, position=InfoBarPosition.BOTTOM, duration=3000)

    def _find_key(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("dlg_open_title"), "", i18n.t("dlg_filter"))
        if not path:
            return
        QMessageBox.information(self, i18n.t("app_title"), i18n.t("dlg_brute_warn"))
        self.status_label.setText(i18n.t("status_searching_keys"))
        script = open(path, "rb").read()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.act_find_key.setEnabled(False)
        self._brute = BruteForceWorker(script, self)
        self._brute.progress_signal.connect(self._on_brute_progress)
        self._brute.done_signal.connect(self._on_brute_done)
        self._brute.start()

    def _on_brute_progress(self, done: int, total: int):
        pct = int(done / total * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(i18n.t("status_searching", pct=pct, rem=total - done))

    def _on_brute_done(self, keys: list[int]):
        self.progress_bar.setVisible(False)
        self.act_find_key.setEnabled(True)
        self.status_label.setText(i18n.t("status_ready"))
        if keys:
            key_hex = f"{keys[-1]:08X}"
            try:
                open("RLDKeys.txt", "w").write(f"0x{key_hex}")
            except Exception:
                pass
            QMessageBox.information(self, i18n.t("app_title"),
                                    i18n.t("dlg_key_found", key=key_hex))
        else:
            QMessageBox.warning(self, i18n.t("app_title"), i18n.t("dlg_key_not_found"))

    def _decode_gyu(self):
        if not _GYU_AVAILABLE:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open GYU image…", "", "GYU image (*.gyu)")
        if not path:
            return
        try:
            data = open(path, "rb").read()
            raw, w, h, bpp = gyu_engine.decode_gyu(data)
            out = path + ".tga"
            import struct
            if bpp == 8:
                pal = data[0x24:0x24 + 256 * 4]
                hdr = struct.pack("<2B2B9H", 1, 1, 0, 0) + struct.pack("<6H", 0, 0, w, h, 8, 0)
                open(out, "wb").write(hdr + pal + raw)
            else:
                hdr = struct.pack("<2B2B9H", 0, 2, 0, 0) + struct.pack("<6H", 0, 0, w, h, 24, 0)
                open(out, "wb").write(hdr + raw)
            InfoBar.success(title="", content=f"Decoded {w}x{h} -> {out}",
                            parent=self, position=InfoBarPosition.BOTTOM, duration=3000)
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))

    def _crypt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, i18n.t("dlg_open_title"), "", i18n.t("dlg_filter"))
        if not path:
            return
        dlg = KeySelectorDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            data = bytearray(open(path, "rb").read())
            rld  = RLD(bytes(data), dlg.selected_key)
            rld.xor(data)
            out  = path + ".crypt"
            open(out, "wb").write(data)
            self.status_label.setText(i18n.t("status_crypt_done", path=out))
            InfoBar.success(title="", content=i18n.t("dlg_done") + f"\n→ {out}",
                            parent=self, position=InfoBarPosition.BOTTOM, duration=3000)
        except Exception as ex:
            QMessageBox.critical(self, i18n.t("dlg_error"), str(ex))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RLD Manager")
    app.setWindowIcon(app_icon())

    base_font = QFont("Segoe UI", 9)
    app.setFont(base_font)

    setTheme(Theme.AUTO)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
