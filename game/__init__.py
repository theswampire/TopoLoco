import pygame
from typing import Union, Sequence
import game.utils as utils
import game.assets.color_palette as c
from game.assets.fonts import *


def update_notif(screen: pygame.Surface, pos: Union[pygame.Rect, Sequence[int]]):
    surf = pygame.Surface((150, 80))
    if utils.app_update_available:
        text, _ = utils.text_input_font.render("App Update available!!", c.error)
        surf.blit(text, (0, 0))
    if utils.data_updatable:
        text, rect = text_input_font.render("Dataset Update available!", c.error)
        if utils.app_update_available:
            rect.top = 30
        surf.blit(text, rect)

    surf.set_colorkey(c.black)
    screen.blit(surf, pos)
