from formatter import formatter
from objects.color import Color


@formatter(Color, str, None)
def color_to_string(color: Color) -> str:
    return color.hex
