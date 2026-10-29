import os
from .common import ParseError, UnsupportedFormat, exact, u16, u32, result, check_range

BI = {0: "BI_RGB (без сжатия)", 1: "BI_RLE8", 2: "BI_RLE4", 3: "BI_BITFIELDS", 4: "BI_JPEG", 5: "BI_PNG", 6: "BI_ALPHABITFIELDS"}

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if exact(f, 2) != b"BM":
            raise UnsupportedFormat("Сигнатура BMP отсутствует")
        file_size = u32(exact(f, 4))
        exact(f, 4)
        pixel_offset = u32(exact(f, 4))
        dib_size = u32(exact(f, 4))
        if dib_size < 12 or 12 < dib_size < 40:
            raise ParseError("Неподдерживаемый или некорректный DIB-заголовок")
        check_range(14, dib_size, size)
        if dib_size == 12:
            width, height = u16(exact(f, 2)), u16(exact(f, 2))
            planes, bpp = u16(exact(f, 2)), u16(exact(f, 2))
            compression = 0
            colors_used = 0
        else:
            width, height = int.from_bytes(exact(f, 4), "little", signed=True), int.from_bytes(exact(f, 4), "little", signed=True)
            planes, bpp = u16(exact(f, 2)), u16(exact(f, 2))
            compression = u32(exact(f, 4))
            exact(f, 4)
            exact(f, 4)
            exact(f, 4)
            colors_used = u32(exact(f, 4))
            exact(f, 4)
        if width <= 0 or height == 0 or planes != 1 or bpp not in (1, 2, 4, 8, 16, 24, 32):
            raise ParseError("Некорректные размеры или параметры BMP")
        height = abs(height)
        if pixel_offset > size:
            raise ParseError("Смещение пиксельных данных за пределами файла")
        if file_size and file_size > size:
            raise ParseError("Размер BMP в заголовке превышает размер файла")
        palette_count = colors_used or (1 << bpp if bpp <= 8 else 0)
        palette_entry = 3 if dib_size == 12 else 4
        palette_offset = 14 + dib_size
        if palette_count:
            check_range(palette_offset, palette_count * palette_entry, size)
        if compression not in BI:
            comp = f"Неизвестный код {compression}"
        else:
            comp = BI[compression]
        return result("BMP", width, height, bpp=bpp, compression=comp, details=f"DIB={dib_size}; смещение пикселей={pixel_offset}; палитра={palette_count} записей")
