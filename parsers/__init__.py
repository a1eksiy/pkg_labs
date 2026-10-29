import os
from . import bmp, png, jpeg, gif, tiff, pcx
from .common import ParseError, UnsupportedFormat

PARSERS = {
    "bmp": bmp.parse, "dib": bmp.parse,
    "png": png.parse,
    "jpg": jpeg.parse, "jpeg": jpeg.parse, "jpe": jpeg.parse,
    "gif": gif.parse,
    "tif": tiff.parse, "tiff": tiff.parse,
    "pcx": pcx.parse,
}

def parse_file(path):
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
        if sig.startswith(b"\x89PNG\r\n\x1a\n"): parser = png.parse
        elif sig.startswith(b"\xff\xd8"): parser = jpeg.parse
        elif sig[:6] in (b"GIF87a", b"GIF89a"): parser = gif.parse
        elif sig[:2] == b"BM": parser = bmp.parse
        elif sig[:2] in (b"II", b"MM"): parser = tiff.parse
        elif sig[:1] == b"\x0a": parser = pcx.parse
        else:
            ext = os.path.splitext(path)[1].lower().lstrip(".")
            if ext not in PARSERS:
                raise UnsupportedFormat("Формат не поддерживается или сигнатура не распознана")
            parser = PARSERS[ext]
        data = parser(path)
        return data
    except UnsupportedFormat as e:
        return {"format": "Неизвестен", "status": "Неподдерживаемый формат", "details": str(e)}
    except (ParseError, OSError, ValueError, OverflowError, IndexError, struct_error()) as e:
        return {"format": "Не определён", "status": "Файл повреждён" if isinstance(e, ParseError) else "Ошибка чтения", "details": str(e) or type(e).__name__}

def struct_error():
    import struct
    return struct.error
