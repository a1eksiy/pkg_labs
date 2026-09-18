import math

D65 = (0.95047, 1.0, 1.08883)

def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))

def cmyk_to_rgb(c, m, y, k):
    return (
        255.0 * (1.0 - c) * (1.0 - k),
        255.0 * (1.0 - m) * (1.0 - k),
        255.0 * (1.0 - y) * (1.0 - k),
    )

def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1.0 - max(r, g, b)
    if k >= 1.0 - 1e-12:
        return 0.0, 0.0, 0.0, 1.0
    d = 1.0 - k
    return (
        (1.0 - r - k) / d,
        (1.0 - g - k) / d,
        (1.0 - b - k) / d,
        k,
    )

def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == r:
        h = (60.0 * ((g - b) / d)) % 360.0
    elif mx == g:
        h = 60.0 * ((b - r) / d + 2.0)
    else:
        h = 60.0 * ((r - g) / d + 4.0)
    s = 0.0 if mx == 0 else d / mx
    return h, s, mx

def hsv_to_rgb(h, s, v):
    h = h % 360.0
    c = v * s
    hp = h / 60.0
    x = c * (1.0 - abs(hp % 2.0 - 1.0))
    if hp < 1:
        rp, gp, bp = c, x, 0
    elif hp < 2:
        rp, gp, bp = x, c, 0
    elif hp < 3:
        rp, gp, bp = 0, c, x
    elif hp < 4:
        rp, gp, bp = 0, x, c
    elif hp < 5:
        rp, gp, bp = x, 0, c
    else:
        rp, gp, bp = c, 0, x
    m = v - c
    return (
        255.0 * (rp + m),
        255.0 * (gp + m),
        255.0 * (bp + m),
    )

def _srgb_to_linear(c):
    c = c / 255.0
    if c <= 0.04045:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4

def _linear_to_srgb(c):
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (max(c, 0.0) ** (1.0 / 2.4)) - 0.055

def rgb_to_xyz(r, g, b):
    r, g, b = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )

def xyz_to_rgb(x, y, z):
    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z
    raw = (r, g, b)
    clipped = tuple(clamp(_linear_to_srgb(v)) for v in raw)
    clipped_rgb = tuple(v * 255.0 for v in clipped)
    clipped_needed = any(v < -1e-9 or v > 1.0 + 1e-9 for v in raw)
    return clipped_rgb, clipped_needed

def _lab_f(t):
    delta = 6.0 / 29.0
    if t > delta ** 3:
        return t ** (1.0 / 3.0)
    return t / (3.0 * delta ** 2) + 4.0 / 29.0

def _lab_f_inv(t):
    delta = 6.0 / 29.0
    if t > delta:
        return t ** 3
    return 3.0 * delta ** 2 * (t - 4.0 / 29.0)

def xyz_to_lab(x, y, z):
    xn, yn, zn = D65
    fx, fy, fz = _lab_f(x / xn), _lab_f(y / yn), _lab_f(z / zn)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)

def lab_to_xyz(l, a, b):
    xn, yn, zn = D65
    fy = (l + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    return (
        xn * _lab_f_inv(fx),
        yn * _lab_f_inv(fy),
        zn * _lab_f_inv(fz),
    )

def cmyk_to_lab(c, m, y, k):
    return xyz_to_lab(*rgb_to_xyz(*cmyk_to_rgb(c, m, y, k)))

def lab_to_cmyk(l, a, b):
    rgb, clipped = xyz_to_rgb(*lab_to_xyz(l, a, b))
    return (*rgb_to_cmyk(*rgb), clipped)

def cmyk_to_hsv(c, m, y, k):
    return rgb_to_hsv(*cmyk_to_rgb(c, m, y, k))

def hsv_to_cmyk(h, s, v):
    return rgb_to_cmyk(*hsv_to_rgb(h, s, v))

def lab_to_hsv(l, a, b):
    rgb, clipped = xyz_to_rgb(*lab_to_xyz(l, a, b))
    return (*rgb_to_hsv(*rgb), clipped)

def hsv_to_lab(h, s, v):
    return xyz_to_lab(*rgb_to_xyz(*hsv_to_rgb(h, s, v)))
