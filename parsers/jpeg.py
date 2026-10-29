import os
from fractions import Fraction
from .common import ParseError, UnsupportedFormat, exact, u16, u32, result, check_range

SOF = {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if exact(f, 2) != b"\xff\xd8":
            raise UnsupportedFormat("Сигнатура JPEG отсутствует")
        width = height = bpc = components = None
        dpi_x = dpi_y = None
        eoi = False
        progressive = False
        while f.tell() < size:
            b = exact(f, 1)[0]
            while b != 0xFF:
                b = exact(f, 1)[0]
            while True:
                marker = exact(f, 1)[0]
                if marker != 0xFF:
                    break
            if marker == 0xD9:
                eoi = True
                break
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                continue
            length = u16(exact(f, 2), "big")
            if length < 2:
                raise ParseError("Некорректная длина сегмента JPEG")
            data_len = length - 2
            check_range(f.tell(), data_len, size)
            data = exact(f, data_len)
            if marker in SOF:
                if len(data) < 6:
                    raise ParseError("Укороченный SOF")
                bpc = data[0]
                height, width = u16(data[1:3], "big"), u16(data[3:5], "big")
                components = data[5]
                progressive = marker in (0xC2,0xC6,0xCA,0xCE)
            elif marker == 0xE0 and data.startswith(b"JFIF\x00") and len(data) >= 12:
                units = data[7]
                xden, yden = u16(data[8:10], "big"), u16(data[10:12], "big")
                if units == 1:
                    dpi_x, dpi_y = xden or None, yden or None
                elif units == 2:
                    dpi_x, dpi_y = round(xden * 2.54, 3) if xden else None, round(yden * 2.54, 3) if yden else None
            elif marker == 0xE1 and data.startswith(b"Exif\x00\x00"):
                exif = _parse_exif(data[6:])
                dpi_x = dpi_x or exif[0]
                dpi_y = dpi_y or exif[1]
            if marker == 0xDA:
                while f.tell() < size:
                    byte = exact(f, 1)[0]
                    if byte == 0xFF:
                        nxt = exact(f, 1)[0]
                        while nxt == 0xFF:
                            nxt = exact(f, 1)[0]
                        if nxt == 0xD9:
                            eoi = True
                            break
                        if nxt == 0x00 or 0xD0 <= nxt <= 0xD7:
                            continue
                        f.seek(-2, 1)
                        break
                if eoi:
                    break
        if width is None or height is None:
            raise ParseError("SOF с размерами JPEG не найден")
        if not eoi:
            raise ParseError("Отсутствует маркер EOI (FF D9)")
        return result("JPEG", width, height, dpi_x, dpi_y, bpp=bpc * components if bpc and components else None, bpc=bpc, compression="DCT; " + ("progressive" if progressive else "baseline/other"), details=f"компонентов={components}")

def _parse_exif(data):
    try:
        if len(data) < 8:
            return (None, None)
        endian_tag = data[:2]
        endian = "little" if endian_tag == b"II" else "big" if endian_tag == b"MM" else None
        if not endian or int.from_bytes(data[2:4], endian) != 42:
            return (None, None)
        off = int.from_bytes(data[4:8], endian)
        if off + 2 > len(data):
            return (None, None)
        count = int.from_bytes(data[off:off+2], endian)
        x = y = unit = None
        for i in range(min(count, 512)):
            p = off + 2 + i * 12
            if p + 12 > len(data):
                break
            tag = int.from_bytes(data[p:p+2], endian)
            typ = int.from_bytes(data[p+2:p+4], endian)
            n = int.from_bytes(data[p+4:p+8], endian)
            val = data[p+8:p+12]
            if tag == 0x0128:
                unit = int.from_bytes(val[:2], endian)
            if tag in (0x011A, 0x011B) and typ == 5 and n:
                ptr = int.from_bytes(val, endian)
                if ptr + 8 <= len(data):
                    num = int.from_bytes(data[ptr:ptr+4], endian)
                    den = int.from_bytes(data[ptr+4:ptr+8], endian)
                    if den:
                        value = num / den
                        if tag == 0x011A: x = value
                        else: y = value
        if unit == 3:
            x = x * 2.54 if x else None
            y = y * 2.54 if y else None
        if unit not in (2, 3):
            return (None, None)
        return (round(x, 3) if x else None, round(y, 3) if y else None)
    except (IndexError, ValueError, OverflowError):
        return (None, None)
