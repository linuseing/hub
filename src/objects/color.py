from colorsys import rgb_to_hsv, hsv_to_rgb

def RGB_to_hex(RGB):
    """[255,255,255] -> '#FFFFFF' """
    RGB = [int(x) for x in RGB]
    return "#" + "".join(
        ["0{0:x}".format(v) if v < 16 else "{0:x}".format(v) for v in RGB]
    )


def scale(color):
    return list(map(lambda x: x / 255, color))


def hex_to_rgb(value):
    """ '#FFFFFF' -> [255,255,255]"""
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def convert_to_rgb(_in):
    if type(_in) is list:
        return _in
    elif type(_in) is str:
        if _in.startswith("#"):
            return list(hex_to_rgb(_in))


class Color:
    def __init__(self, init=None):
        self._rgb: [int, int, int] = [0, 0, 0]
        self._hsv = [0, 0, 0]

        if init:
            self.rgb = convert_to_rgb(init)

    def __repr__(self):
        return f"[{self.r},{self.g},{self.b}]"

    def __str__(self):
        return f"[{self.r},{self.g},{self.b}]"

    def __iter__(self):
        yield "r", self.r
        yield "g", self.g
        yield "b", self.b

    @classmethod
    def from_string(cls, _in: str, delimiter=",", strip=1):
        print("test")
        if type(_in) is str:
            _str = _in[strip:-strip].split(delimiter)
            return cls(_str)
        elif type(_in) is list:
            print(_in)
            i = cls()
            i.rgb = _in
            return i

    @property
    def hsv(self):
        return self._hsv

    @hsv.setter
    def hsv(self, value):
        rgb = hsv_to_rgb(*value)
        self._rgb = list(map(lambda x: int(x * 255), rgb))
        self._hsv = value

    @property
    def hue(self):
        return self._hsv[0]

    @hue.setter
    def hue(self, value):
        self._hsv[0] = value
        self._rgb = hsv_to_rgb(*self._hsv)

    @property
    def saturation(self):
        return self._hsv[1]

    @saturation.setter
    def saturation(self, value):
        self._hsv[1] = value
        self._rgb = hsv_to_rgb(*self._hsv)

    @property
    def brightness(self):
        return self._hsv[2]

    @brightness.setter
    def brightness(self, value):
        self._hsv[2] = value
        self._rgb = hsv_to_rgb(*self._hsv)

    @property
    def rgb(self):
        return self._rgb

    @rgb.setter
    def rgb(self, value):
        self._rgb = value
        self._hsv = rgb_to_hsv(*scale(value))

    @property
    def r(self):
        return self._rgb[0]

    @r.setter
    def r(self, value):
        self._rgb[0] = value
        self._hsv = rgb_to_hsv(*scale(self._rgb))

    @property
    def g(self):
        return self._rgb[1]

    @g.setter
    def g(self, value):
        self._rgb[1] = value
        self._hsv = rgb_to_hsv(*scale(self._rgb))

    @property
    def b(self):
        return self._rgb[2]

    @b.setter
    def b(self, value):
        self._rgb[2] = value
        self._hsv = rgb_to_hsv(*scale(self._rgb))

    @property
    def hex(self):
        return RGB_to_hex(self._rgb)

    @hex.setter
    def hex(self, value):
        self.rgb = hex_to_rgb(value)

    @property
    def value(self):
        return self._rgb

    @value.setter
    def value(self, value):
        self.rgb = convert_to_rgb(value)

    def to_json(self):
        return self.hex


class Colors(enumerate):
    BLACK = Color([0, 0, 0])
    RED = Color([255, 0, 0])
    GREEN = Color([0, 255, 0])
    BLUE = Color([0, 0, 255])
    WHITE = Color([255, 255, 255])
