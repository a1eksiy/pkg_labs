import os
from threading import Event
from PySide6.QtCore import QObject, Signal, QThread, Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QCheckBox, QProgressBar, QLineEdit, QComboBox, QTableView,
    QMessageBox, QAbstractItemView
)
from scanner import scan
from exporter import export_csv
from .table_model import ImageTableModel

class ScanSignals(QObject):
    batch = Signal(object)
    progress = Signal(int)
    finished = Signal(int, bool)
    failed = Signal(str)

class ScanThread(QThread):
    def __init__(self, roots, recursive):
        super().__init__()
        self.roots = roots
        self.recursive = recursive
        self.cancel_event = Event()
        self.signals = ScanSignals()

    def run(self):
        try:
            count = scan(self.roots, self.recursive, self.cancel_event, self.signals.batch.emit, self.signals.progress.emit)
            self.signals.finished.emit(count, self.cancel_event.is_set())
        except Exception as e:
            self.signals.failed.emit(str(e))
            self.signals.finished.emit(0, self.cancel_event.is_set())

    def cancel(self):
        self.cancel_event.set()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Чтение информации из графических файлов")
        self.resize(1350, 760)
        self.model = ImageTableModel()
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.thread = None
        self.total = 0
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        top = QHBoxLayout()
        self.file_button = QPushButton("Выбрать файлы…")
        self.folder_button = QPushButton("Выбрать папку…")
        self.recursive = QCheckBox("Включая подпапки")
        self.recursive.setChecked(True)
        self.start_button = QPushButton("Начать сканирование")
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setEnabled(False)
        self.clear_button = QPushButton("Очистить")
        self.export_button = QPushButton("Экспорт CSV…")
        for widget in (self.file_button, self.folder_button, self.recursive, self.start_button, self.cancel_button, self.clear_button, self.export_button):
            top.addWidget(widget)
        root.addLayout(top)
        second = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Поиск по имени, пути, формату, статусу…")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все статусы", "Метаданные прочитаны", "Файл повреждён", "Неподдерживаемый формат", "Ошибка чтения"])
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setValue(0)
        self.progress.setMaximum(100)
        self.counter = QLabel("Файлов: 0")
        second.addWidget(self.filter, 3)
        second.addWidget(self.status_filter, 1)
        second.addWidget(self.progress, 2)
        second.addWidget(self.counter)
        root.addLayout(second)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        root.addWidget(self.table, 1)
        self.setCentralWidget(central)
        self.file_button.clicked.connect(self.choose_files)
        self.folder_button.clicked.connect(self.choose_folder)
        self.start_button.clicked.connect(self.start_scan)
        self.cancel_button.clicked.connect(self.cancel_scan)
        self.clear_button.clicked.connect(self.clear_results)
        self.export_button.clicked.connect(self.export_results)
        self.filter.textChanged.connect(self.proxy.setFilterRegularExpression)
        self.status_filter.currentTextChanged.connect(self.apply_status_filter)

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать изображения или файлы", "", "Все файлы (*.*)")
        if files:
            self._add_roots(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder:
            self._add_roots([folder])

    def _add_roots(self, roots):
        self.roots = list(dict.fromkeys(roots))

        self.model.clear()
        self.total = 0

        self.progress.setValue(0)
        self.counter.setText("Файлов: 0")

        self.statusBar().showMessage(
            f"Выбрано источников: {len(self.roots)}"
        )

        self.apply_status_filter()

    def start_scan(self):
        if self.thread and self.thread.isRunning():
            return
        roots = getattr(self, "roots", [])
        if not roots:
            QMessageBox.information(self, "Нет источников", "Сначала выберите файлы или папку.")
            return
        self.total = 0
        self.progress.setRange(0, 0)
        self.counter.setText(f"Файлов: {len(self.model.records)}; обработано в запуске: 0")
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.thread = ScanThread(roots, self.recursive.isChecked())
        self.thread.signals.batch.connect(self.receive_batch)
        self.thread.signals.progress.connect(self.receive_progress)
        self.thread.signals.finished.connect(self.scan_finished)
        self.thread.signals.failed.connect(lambda message: QMessageBox.warning(self, "Ошибка сканирования", message))
        self.thread.start()

    def receive_batch(self, records):
        self.model.add_records(records)
        self.apply_status_filter()

    def receive_progress(self, count):
        self.total = count
        self.counter.setText(f"Всего в таблице: {len(self.model.records)}; обработано: {count}")

    def scan_finished(self, count, cancelled):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.counter.setText(f"Всего в таблице: {len(self.model.records)}; в запуске: {count}" + ("; отменено" if cancelled else "; завершено"))
        self.statusBar().showMessage("Сканирование отменено" if cancelled else "Сканирование завершено")

    def cancel_scan(self):
        if self.thread:
            self.thread.cancel()
            self.cancel_button.setEnabled(False)

    def clear_results(self):
        if self.thread and self.thread.isRunning():
            QMessageBox.information(self, "Сканирование", "Сначала отмените текущее сканирование.")
            return
        self.model.clear()
        self.counter.setText("Файлов: 0")

    def apply_status_filter(self):
        text = self.status_filter.currentText()
        if text == "Все статусы":
            self.proxy.setFilterRegularExpression(self.filter.text())
            return
        escaped = QRegularExpression.escape(text)
        regex = QRegularExpression(escaped, QRegularExpression.PatternOption.CaseInsensitiveOption)
        self.proxy.setFilterRegularExpression(regex)
        self.proxy.setFilterKeyColumn(self.model.keys.index("status"))

    def export_results(self):
        if not self.model.records:
            QMessageBox.information(self, "Экспорт", "Нет данных для экспорта.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Экспорт CSV", "image_metadata.csv", "CSV (*.csv)")
        if path:
            try:
                export_csv(path, self.model.records)
                QMessageBox.information(self, "Экспорт", "CSV успешно сохранён.")
            except OSError as e:
                QMessageBox.warning(self, "Ошибка экспорта", str(e))
