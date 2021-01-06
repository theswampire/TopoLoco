from pygame import Color, draw, Surface
from pygame.locals import RLEACCEL
from pygame.sprite import Sprite

import game.assets.color_palette as c
from game.utils import invert_color

__all__ = ["LocationMarker"]


class LocationMarker(Sprite):
    def __init__(self, position: tuple, name: str, category: str, color: Color = c.lightblue_highlight):
        super(LocationMarker, self).__init__()

        self.color = color
        inv_color = invert_color(color)

        size = 18

        self.surf = Surface((size, size))
        self.surf.fill(inv_color)
        self.rect = draw.circle(surface=self.surf, color=color, center=(size/2, size/2), radius=size/2)
        self.rect.center = position

        self.surf.set_colorkey(inv_color, RLEACCEL)

        self.name = name
        self.category = category
        self.is_asked = False

    def is_clicked(self, mouse_pos: tuple):
        return self.rect.collidepoint(mouse_pos)
