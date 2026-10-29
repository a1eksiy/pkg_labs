import os

class ParseError(Exception):
    pass

class UnsupportedFormat(Exception):
    pass

def exact(f, size):
    data = f.read(size)
    if len(data) != size:
        raise ParseError("Неожиданный конец файла")
    return data

def u16(data, endian="little"):
    return int.from_bytes(data, endian)

def u32(data, endian="little"):
    return int.from_bytes(data, endian)

def result(fmt, width=None, height=None, dpi_x=None, dpi_y=None, bpp=None, bpc=None, compression="Неизвестно", details=""):
    return {
        "format": fmt, "width": width, "height": height,
        "dpi_x": dpi_x, "dpi_y": dpi_y, "bits_per_pixel": bpp,
        "bits_per_channel": bpc, "compression": compression,
        "status": "Метаданные прочитаны", "details": details
    }

def check_range(offset, length, file_size):
    if offset < 0 or length < 0 or offset + length > file_size:
        raise ParseError("Смещение или размер выходит за границы файла")
