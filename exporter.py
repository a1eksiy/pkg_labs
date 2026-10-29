import csv

HEADERS = [
    ("name", "Имя файла"), ("path", "Путь"), ("format", "Формат"),
    ("width", "Ширина"), ("height", "Высота"), ("dpi_x", "DPI X"),
    ("dpi_y", "DPI Y"), ("bits_per_pixel", "Глубина, bpp"),
    ("bits_per_channel", "На канал, бит"), ("compression", "Сжатие"),
    ("status", "Статус"), ("details", "Описание")
]

def export_csv(path, records):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([label for _, label in HEADERS])
        for record in records:
            row = record.as_dict() if hasattr(record, "as_dict") else record
            writer.writerow(["" if row.get(key) is None else row.get(key) for key, _ in HEADERS])
