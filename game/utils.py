import os
import re
import sys
from pathlib import Path
from typing import Union

import pygame

__all__ = ["aspect_scale", "writeable_path", "root_path", "rel_to_root", "rel_to_writable", "temp_path",
           "is_custom_path", "multiline_text", "invert_color", "absolute_path"]


def aspect_scale(img, box, smooth: bool = False):
    """ Scales 'img' to fit into box bx/by.
     This method will retain the original image's aspect ratio """
    bx, by = box
    ix, iy = img.get_size()
    if ix > iy:
        # fit to width
        scale_factor = bx / float(ix)
        sy = scale_factor * iy
        if sy > by:
            scale_factor = by / float(iy)
            sx = scale_factor * ix
            sy = by
        else:
            sx = bx
    else:
        # fit to height
        scale_factor = by / float(iy)
        sx = scale_factor * ix
        if sx > bx:
            scale_factor = bx / float(ix)
            sx = bx
            sy = scale_factor * iy
        else:
            sy = by

    if smooth:
        return pygame.transform.smoothscale(img, (int(sx), int(sy)))
    else:
        return pygame.transform.scale(img, (int(sx), int(sy)))


def invert_color(color: pygame.Color):
    return 255 - color.r, 255 - color.g, 255 - color.b


def multiline_text(text: str, font, color: pygame.Color, margin: int = 10, max_length: int = None):
    if max_length is not None:
        formatted_string = ""

        words_with_nl = [word for word in re.split(r' |(\n)', text) if word is not None and word != ""]

        length = 0
        *_, space_length, _ = font.get_metrics(" ")[0]  # horizontal advance x coordinate

        for i, word in enumerate(words_with_nl):
            word_length = 0
            for metric in font.get_metrics(word):
                if metric is not None:
                    _, charadvance, *_ = metric  # max_x
                    word_length += charadvance

            if word == "\n":
                formatted_string += "\n"
                length = 0
            elif length + word_length + space_length > max_length:
                formatted_string += "\n" + word + " "
                length = 0
            else:
                formatted_string += word + " "
                length += word_length + space_length

        text = formatted_string

    size = font.size
    lines = text.split("\n")

    surfs = []
    for i, line in enumerate(lines):
        txt, rect = font.render(line, color)
        rect.topleft = 0, size * i + (i * margin)
        surfs.append((txt, rect))
    return surfs


writeable_path = Path(os.environ["LOCALAPPDATA"]).joinpath(Path("TopoLoco"))
writeable_path.joinpath(Path("data")).mkdir(exist_ok=True, parents=True)
writeable_path.joinpath(Path("textures/maps")).mkdir(exist_ok=True, parents=True)

temp_path = Path(os.environ["TEMP"])

root_path = Path(sys.modules["__main__"].__file__).parent
if not root_path.exists():
    raise FileNotFoundError


def rel_to_root(path):
    relpath = Path(path)
    return str(root_path.joinpath(relpath))


def rel_to_writable(path):
    rel_path = Path(path)
    return str(writeable_path.joinpath(rel_path))


def is_custom_path(path: Union[str, Path]):
    if type(path) is str:
        path = Path(path)
    for i, part in enumerate(writeable_path.parts):
        if path.parts[i] != part:
            return False
    return True


def absolute_path(relative: Union[str, Path]) -> Path:
    if type(relative) is str:
        relative = Path(relative)

    return Path(rel_to_writable(relative) if is_custom_path(relative) else rel_to_root(relative))
