import os
from .common import ParseError, UnsupportedFormat, exact, result, check_range

TYPE_SIZE = {1:1,2:1,3:2,4:4,5:8,6:1,7:1,8:2,9:4,10:8,11:4,12:8}
COMPRESSION = {1:"без сжатия",2:"CCITT RLE",3:"CCITT Group 3",4:"CCITT Group 4",5:"LZW",6:"JPEG (старый TIFF)",7:"JPEG",8:"Deflate",32773:"PackBits",32946:"Deflate"}

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = exact(f, 8)
        if head[:2] == b"II":
            endian = "little"
        elif head[:2] == b"MM":
            endian = "big"
        else:
            raise UnsupportedFormat("Порядок байтов TIFF не распознан")
        if int.from_bytes(head[2:4], endian) != 42:
            raise UnsupportedFormat("Неклассический TIFF/BigTIFF не поддерживается")
        first_ifd = int.from_bytes(head[4:8], endian)
        if first_ifd < 8 or first_ifd + 2 > size:
            raise ParseError("Некорректное смещение IFD")
        pages = []
        visited = set()
        offset = first_ifd
        while offset and len(pages) < 256:
            if offset in visited:
                raise ParseError("Циклическая цепочка IFD")
            visited.add(offset)
            check_range(offset, 2, size)
            f.seek(offset)
            count = int.from_bytes(exact(f, 2), endian)
            if count > 4096:
                raise ParseError("Слишком много TIFF-тегов в IFD")
            check_range(offset + 2, count * 12 + 4, size)
            tags = {}
            for _ in range(count):
                entry = exact(f, 12)
                tag = int.from_bytes(entry[:2], endian)
                typ = int.from_bytes(entry[2:4], endian)
                n = int.from_bytes(entry[4:8], endian)
                raw = entry[8:12]
                if typ not in TYPE_SIZE or n > 10_000_000:
                    continue
                total = TYPE_SIZE[typ] * n
                if total <= 4:
                    val = raw[:total]
                else:
                    ptr = int.from_bytes(raw, endian)
                    check_range(ptr, total, size)
                    here = f.tell()
                    f.seek(ptr)
                    val = exact(f, total)
                    f.seek(here)
                tags[tag] = _values(val, typ, n, endian)
            next_offset = int.from_bytes(exact(f, 4), endian)
            pages.append(tags)
            offset = next_offset
        if not pages:
            raise ParseError("IFD не найден")
        t = pages[0]
        width = _first(t, 256)
        height = _first(t, 257)
        if not width or not height:
            raise ParseError("В TIFF отсутствуют корректные размеры")
        bps = t.get(258, [1])
        samples = _first(t, 277, 1)
        bpp = sum(bps[:samples]) if bps else None
        xr = _rational(t.get(282))
        yr = _rational(t.get(283))
        unit = _first(t, 296, 2)
        if unit == 3:
            xr = xr * 2.54 if xr else None
            yr = yr * 2.54 if yr else None
        elif unit != 2:
            xr = yr = None
        comp = _first(t, 259, 1)
        photo = _first(t, 262)
        extra = []
        if 273 in t or 324 in t: extra.append("полосы/тайлы описаны")
        extra.append(f"страниц={len(pages)}" + ("+" if offset else ""))
        extra.append(f"photometric={photo}" if photo is not None else "photometric неизвестен")
        return result("TIFF", width, height, round(xr,3) if xr else None, round(yr,3) if yr else None, bpp=bpp, bpc=(bps[0] if len(set(bps)) == 1 else None), compression=COMPRESSION.get(comp, f"код {comp}"), details="; ".join(extra))

def _values(raw, typ, count, endian):
    if typ in (2, 7):
        return [raw.rstrip(b"\0").decode("latin1", "replace")]
    sizes = TYPE_SIZE[typ]
    vals = []
    for i in range(count):
        chunk = raw[i*sizes:(i+1)*sizes]
        if typ in (5, 10):
            a = int.from_bytes(chunk[:4], endian, signed=(typ == 10))
            b = int.from_bytes(chunk[4:8], endian, signed=(typ == 10))
            vals.append((a, b))
        else:
            vals.append(int.from_bytes(chunk, endian, signed=typ in (6,8,9)))
    return vals

def _first(tags, tag, default=None):
    values = tags.get(tag)
    return values[0] if values else default

def _rational(values):
    if not values:
        return None
    value = values[0]
    if isinstance(value, tuple) and value[1]:
        return value[0] / value[1]
    return None
