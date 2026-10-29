from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from exporter import HEADERS

class ImageTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.records = []
        self.headers = [label for _, label in HEADERS]
        self.keys = [key for key, _ in HEADERS]

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.records)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.keys)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        record = self.records[index.row()].as_dict()
        value = record.get(self.keys[index.column()])
        if role == Qt.ItemDataRole.DisplayRole:
            return "" if value is None else str(value)
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(record.get("details") or record.get("path") or "")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self.headers[section]
            return str(section + 1)
        return None

    def add_records(self, records):
        if not records:
            return
        start = len(self.records)
        self.beginInsertRows(QModelIndex(), start, start + len(records) - 1)
        self.records.extend(records)
        self.endInsertRows()

    def clear(self):
        self.beginResetModel()
        self.records.clear()
        self.endResetModel()
