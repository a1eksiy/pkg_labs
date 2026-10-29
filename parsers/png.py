import os, zlib
from .common import ParseError, UnsupportedFormat, exact, u32, result, check_range

SIG = b"\x89PNG\r\n\x1a\n"
COLOR = {0: "grayscale", 2: "RGB", 3: "indexed", 4: "grayscale+alpha", 6: "RGBA"}

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if exact(f, 8) != SIG:
            raise UnsupportedFormat("Сигнатура PNG отсутствует")
        width = height = depth = ctype = None
        saw_iend = False
        chunks = 0
        details = []
        while f.tell() + 12 <= size:
            start = f.tell()
            length = u32(exact(f, 4), "big")
            kind = exact(f, 4)
            check_range(f.tell(), length + 4, size)
            if kind == b"IHDR":
                if length != 13 or width is not None:
                    raise ParseError("Некорректный IHDR")
                data = exact(f, length)
                actual = zlib.crc32(kind + data) & 0xffffffff
            else:
                actual = zlib.crc32(kind)
                remaining = length
                while remaining:
                    part = exact(f, min(65536, remaining))
                    actual = zlib.crc32(part, actual)
                    remaining -= len(part)
                data = b""
            crc = u32(exact(f, 4), "big")
            actual &= 0xffffffff
            if actual != crc:
                raise ParseError(f"Неверный CRC чанка {kind.decode('latin1')}")
            chunks += 1
            if kind == b"IHDR":
                width, height = u32(data[:4], "big"), u32(data[4:8], "big")
                depth, ctype = data[8], data[9]
                if not width or not height or ctype not in COLOR:
                    raise ParseError("Недопустимые параметры IHDR")
                if data[10] != 0 or data[11] != 0 or data[12] not in (0, 1):
                    raise ParseError("Недопустимые методы PNG")
                details.append(f"цвет={COLOR[ctype]}; фильтрация={data[11]}; чередование={data[12]}")
            if kind == b"IEND":
                if length != 0:
                    raise ParseError("Некорректный IEND")
                saw_iend = True
                break
        if width is None:
            raise ParseError("Чанк IHDR не найден")
        if not saw_iend:
            raise ParseError("Отсутствует завершающий чанк IEND")
        channel_count = {0:1, 2:3, 3:1, 4:2, 6:4}[ctype]
        return result("PNG", width, height, bpp=depth * channel_count, bpc=depth, compression="Deflate (zlib)", details="; ".join(details) + f"; проверено чанков={chunks}")
