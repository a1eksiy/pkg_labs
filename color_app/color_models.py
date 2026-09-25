D65 = (0.95047, 1.0, 1.08883)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _srgb_to_linear(value):
    if value <= 0.04045:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(value):
    value = max(value, 0.0)
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * (value ** (1.0 / 2.4)) - 0.055


def cmyk_to_hsv(c, m, y, k):
    r = (1.0 - c) * (1.0 - k)
    g = (1.0 - m) * (1.0 - k)
    b = (1.0 - y) * (1.0 - k)

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


def hsv_to_cmyk(h, s, v):
    h = h % 360.0
    c = v * s
    hp = h / 60.0
    x = c * (1.0 - abs(hp % 2.0 - 1.0))

    if hp < 1:
        r, g, b = c, x, 0.0
    elif hp < 2:
        r, g, b = x, c, 0.0
    elif hp < 3:
        r, g, b = 0.0, c, x
    elif hp < 4:
        r, g, b = 0.0, x, c
    elif hp < 5:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x

    m = v - c
    r += m
    g += m
    b += m

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


def _cmyk_to_xyz(c, m, y, k):
    r = _srgb_to_linear((1.0 - c) * (1.0 - k))
    g = _srgb_to_linear((1.0 - m) * (1.0 - k))
    b = _srgb_to_linear((1.0 - y) * (1.0 - k))

    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )


def _hsv_to_xyz(h, s, v):
    h = h % 360.0
    c = v * s
    hp = h / 60.0
    x = c * (1.0 - abs(hp % 2.0 - 1.0))

    if hp < 1:
        r, g, b = c, x, 0.0
    elif hp < 2:
        r, g, b = x, c, 0.0
    elif hp < 3:
        r, g, b = 0.0, c, x
    elif hp < 4:
        r, g, b = 0.0, x, c
    elif hp < 5:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x

    m = v - c
    r = _srgb_to_linear(r + m)
    g = _srgb_to_linear(g + m)
    b = _srgb_to_linear(b + m)

    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )


def _lab_f(value):
    delta = 6.0 / 29.0
    if value > delta ** 3:
        return value ** (1.0 / 3.0)
    return value / (3.0 * delta ** 2) + 4.0 / 29.0


def _lab_f_inv(value):
    delta = 6.0 / 29.0
    if value > delta:
        return value ** 3
    return 3.0 * delta ** 2 * (value - 4.0 / 29.0)


def xyz_to_lab(x, y, z):
    xn, yn, zn = D65
    fx = _lab_f(x / xn)
    fy = _lab_f(y / yn)
    fz = _lab_f(z / zn)
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
    return xyz_to_lab(*_cmyk_to_xyz(c, m, y, k))


def hsv_to_lab(h, s, v):
    return xyz_to_lab(*_hsv_to_xyz(h, s, v))


def lab_to_cmyk(l, a, b):
    x, y, z = lab_to_xyz(l, a, b)

    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    clipped = (
        r < -1e-9 or r > 1.0 + 1e-9 or
        g < -1e-9 or g > 1.0 + 1e-9 or
        b < -1e-9 or b > 1.0 + 1e-9
    )

    r = clamp(_linear_to_srgb(r))
    g = clamp(_linear_to_srgb(g))
    b = clamp(_linear_to_srgb(b))

    k = 1.0 - max(r, g, b)
    if k >= 1.0 - 1e-12:
        return 0.0, 0.0, 0.0, 1.0, clipped

    d = 1.0 - k
    return (
        (1.0 - r - k) / d,
        (1.0 - g - k) / d,
        (1.0 - b - k) / d,
        k,
        clipped,
    )


def lab_to_hsv(l, a, b):
    x, y, z = lab_to_xyz(l, a, b)

    r = 3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b = 0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    clipped = (
        r < -1e-9 or r > 1.0 + 1e-9 or
        g < -1e-9 or g > 1.0 + 1e-9 or
        b < -1e-9 or b > 1.0 + 1e-9
    )

    r = clamp(_linear_to_srgb(r))
    g = clamp(_linear_to_srgb(g))
    b = clamp(_linear_to_srgb(b))

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
    return h, s, mx, clipped
