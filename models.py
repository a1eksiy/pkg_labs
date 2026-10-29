from dataclasses import dataclass, asdict

@dataclass
class ImageRecord:
    name: str
    path: str
    format: str = "Не определён"
    width: object = None
    height: object = None
    dpi_x: object = None
    dpi_y: object = None
    bits_per_pixel: object = None
    bits_per_channel: object = None
    compression: str = "Неизвестно"
    status: str = "Не обработан"
    details: str = ""

    def as_dict(self):
        return asdict(self)
