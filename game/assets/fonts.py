import pygame
from pygame.freetype import Font

from game.utils import rel_to_root

__all__ = ["title_font", "question_font", "question_asked_font", "fps_counter", "category_font", "text_input_font",
           "scene_title_font", "mini_info_font", "light_italic_font_25"]

# pygame.font.init()
pygame.freetype.init()

# Fonts
title_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Black.ttf"), 90)
scene_title_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Bold.ttf"), 50)

question_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Medium.ttf"), 30)
question_asked_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-MediumItalic.ttf"), 30)

fps_counter = Font(rel_to_root("resources/fonts/Roboto/Roboto-Thin.ttf"), 15)

category_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Light.ttf"), 30)
text_input_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Regular.ttf"), 30)
light_italic_font_25 = Font(rel_to_root("resources/fonts/Roboto/Roboto-LightItalic.ttf"), 25)
regular_font_15 = Font(rel_to_root("resources/fonts/Roboto/Roboto-Regular.ttf"), 20)

mini_info_font = Font(rel_to_root("resources/fonts/Roboto/Roboto-Light.ttf"), 15)
