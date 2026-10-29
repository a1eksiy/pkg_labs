import os
from .common import ParseError, UnsupportedFormat, exact, u16, result, check_range

def parse(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        sig = exact(f, 6)
        if sig not in (b"GIF87a", b"GIF89a"):
            raise UnsupportedFormat("Сигнатура GIF отсутствует")
        width, height = u16(exact(f, 2)), u16(exact(f, 2))
        packed, bg, aspect = exact(f, 3)
        global_table = bool(packed & 0x80)
        table_size = 2 ** ((packed & 7) + 1) if global_table else 0
        if global_table:
            check_range(f.tell(), table_size * 3, size)
            exact(f, table_size * 3)
        frames = 0
        saw_trailer = False
        while f.tell() < size:
            introducer = exact(f, 1)[0]
            if introducer == 0x3B:
                saw_trailer = True
                break
            if introducer == 0x21:
                exact(f, 1)
                while True:
                    n = exact(f, 1)[0]
                    if n == 0:
                        break
                    check_range(f.tell(), n, size)
                    exact(f, n)
            elif introducer == 0x2C:
                exact(f, 8)
                packed_img = exact(f, 1)[0]
                if packed_img & 0x80:
                    ncolors = 2 ** ((packed_img & 7) + 1)
                    check_range(f.tell(), ncolors * 3, size)
                    exact(f, ncolors * 3)
                exact(f, 1)
                while True:
                    n = exact(f, 1)[0]
                    if n == 0:
                        break
                    check_range(f.tell(), n, size)
                    exact(f, n)
                frames += 1
            else:
                raise ParseError(f"Неизвестный блок GIF: 0x{introducer:02X}")
        if not saw_trailer:
            raise ParseError("Отсутствует завершающий байт GIF 0x3B")
        bpp = (packed & 7) + 1 if global_table else None
        return result("GIF", width, height, bpp=bpp, compression="LZW", details=f"версия={sig.decode()}; глобальная палитра={table_size or 'нет'}; кадров={frames}")
