import os
from .common import ParseError, UnsupportedFormat, exact, u16, result

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        h = exact(f, 128)
        if h[0] != 0x0A or h[2] not in (0, 1) or h[3] not in (1, 2, 4, 8):
            raise UnsupportedFormat("Заголовок PCX не распознан")
        xmin, ymin, xmax, ymax = (u16(h[i:i+2]) for i in (4, 6, 8, 10))
        width, height = xmax - xmin + 1, ymax - ymin + 1
        if width <= 0 or height <= 0:
            raise ParseError("Некорректные координаты PCX")
        planes = h[65]
        bytes_per_line = u16(h[66:68])
        if planes < 1 or bytes_per_line < 1:
            raise ParseError("Некорректные параметры PCX")
        dx, dy = u16(h[12:14]), u16(h[14:16])
        bpp = h[3] * planes
        return result("PCX", width, height, dpi_x=dx or None, dpi_y=dy or None, bpp=bpp, bpc=h[3], compression="RLE" if h[2] == 1 else "без сжатия", details=f"planes={planes}; bytes_per_line={bytes_per_line}; палитра={h[16:48].hex()[:24]}…")
