from typing import Union

import easing_functions
import pygame
from pygame import Surface, RLEACCEL
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP

import game.assets.color_palette as c
from game.animations import Blinker
from game.assets.fonts import text_input_font
from game.utils import invert_color, aspect_scale

__all__ = ["TextInputBox", "ListView", "ListItem", "Button", "Notification", "LoadingCircleLoop"]


class TextInputBox:
    def __init__(self, pos: tuple, text="", cap: int = None, active: bool = False):
        self.color = c.bg_title_scene
        self.text = text
        self.text_surf, self.text_rect = text_input_font.render(text, c.white)

        self.rect = self.text_rect.copy()
        self.rect.width = max(200, self.text_surf.get_width() + 10)
        self.rect.height = self.text_surf.get_height() + 6
        self.rect.topleft = pos

        self.active = active
        self.pos = pos
        self.cap = cap
        self.oneshot_rendered = False
        self.orig_state = active

    def handle_event(self, event, ctrl_pressed: bool):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False

            # lightblue = active color, bgtitle = inactive
        self.color = c.lightblue_highlight if self.active else c.bg_title_scene

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    if ctrl_pressed:
                        self.text = ""
                    else:
                        self.text = self.text[:-1]
                elif len(self.text) <= self.cap if self.cap else True:
                    self.text += event.unicode

    def draw(self, screen: pygame.Surface):
        if not self.oneshot_rendered:
            self.color = c.lightblue_highlight if self.orig_state else c.bg_title_scene
            self.oneshot_rendered = True

        # Re-render the text
        self.text_surf, self.text_rect = text_input_font.render(self.text, c.white)
        self.rect.width = max(200, self.text_surf.get_width() + 10)
        self.rect.topleft = self.pos

        x, y = self.rect.topleft
        self.text_rect.bottomleft = x + 5, y + 32

        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text_surf, self.text_rect)


class ListItem:
    def __init__(self, height: int, width: int, text: Union[str, None] = "", rect: Union[None, pygame.Rect] = None,
                 base_color: pygame.Color = c.bg_listview, hover_color: pygame.Color = c.bg_listview_hovered,
                 pressed_color: pygame.Color = c.bg_button_pressed):
        self.text = text if text is not None else ""
        self.rect = rect

        self.base_color = base_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color

        self.text_surf, self.text_rect = text_input_font.render(text, c.white)

        self.surf = pygame.Surface((width, height))
        self.surf.fill(self.base_color)

        self.text_rect.centery = self.surf.get_height() / 2
        self.text_rect.left = 6

        self.max_scroll_offset = self.text_surf.get_width() - width
        self.blinker = Blinker(0.3, interpolator="SineEaseOut")
        self.time_passed = 0

        self.color = c.bg_listview

        self.is_hovered = False
        self.is_clicked = False
        self.draw()

        self.scroll_offset = 0
        self.scroll_forward = True
        self.scroll_speed = 300
        self.is_scrollable = self.text_surf.get_width() > width

    def draw(self):
        self.color = self.hover_color if self.is_hovered else self.base_color
        self.color = self.pressed_color if self.is_clicked else self.color

        self.surf.fill(self.color)
        self.text_surf, _ = text_input_font.render(self.text, c.white)
        self.surf.blit(self.text_surf, self.text_rect)

    def scroll(self, dt):
        if self.is_scrollable:
            self.blinker.update(dt)
            self.text_rect.left = -(self.max_scroll_offset + 80) * self.blinker.value


class ListView:
    def __init__(self, listview_list: list, item_height: int = 36, item_length: int = 250, height: int = 400,
                 item_margin: int = 10, selection: bool = False, selected_index: Union[int, None] = None,
                 bg_color: pygame.Color = c.bg_game_scene, base_color: pygame.Color = c.bg_listview,
                 hover_color: pygame.Color = c.bg_listview_hovered, pressed_color: pygame.Color = c.bg_button_pressed,
                 vertical_clip_scroll: bool = True):
        self.list = listview_list

        self.item_height = item_height
        self.item_length = item_length
        self.height = height
        self.item_margin = item_margin

        self.bg_color = bg_color
        self.base_color = base_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color

        self.selection = selection
        self.selected_index = selected_index

        self.full_height = len(self.list) * (item_height + item_margin)

        self.surf = pygame.Surface((item_length, min(self.full_height, height)))
        self.rect = self.surf.get_rect()
        self.full_surf = pygame.Surface((item_length, self.full_height))
        self.full_rect = self.full_surf.get_rect()

        self.item_rect_template = pygame.Rect(0, 0, item_length, item_height)

        self.items = []
        self.render_list = []

        self.scroll_offset = 0
        self.max_scroll_offset = self.full_height - height
        self.vertical_scroll = vertical_clip_scroll

        self.build_list()

    def handle_input(self, event):
        items = self.items
        render_list = self.render_list

        must_update = False
        clicked_index = None
        can_scroll = self.full_height > self.height

        if self.vertical_scroll:
            must_update = True

        x, y = event.pos
        x -= self.rect.x
        y -= self.rect.y - self.scroll_offset

        for i, item in enumerate(items):
            item_must_update = False
            if event.type == MOUSEMOTION:
                # hover
                if item.rect.collidepoint((x, y)) and self.rect.collidepoint(event.pos):
                    if not item.is_hovered:
                        item.is_hovered = True
                        must_update = True
                        item_must_update = True
                # un-hover
                if item.is_hovered and not item.rect.collidepoint((x, y)):
                    item.text_rect.left = 6
                    item.blinker.time_passed = 0
                    item.is_hovered = False
                    must_update = True
                    item_must_update = True

            if event.type == MOUSEBUTTONDOWN:
                # 1 for left click
                if event.button == 1:
                    if item.rect.collidepoint((x, y)) and self.rect.collidepoint(event.pos):
                        clicked_index = i
                        item.is_clicked = True
                        item_must_update = True
                        self.selected_index = i
                    must_update = True

                # 4 for scroll up
                if event.button == 4 and can_scroll:
                    self.scroll_offset -= 15
                    # clamp
                    if self.scroll_offset < 0:
                        self.scroll_offset = 0
                    must_update = True

                # 5 for scroll down
                if event.button == 5 and can_scroll:
                    self.scroll_offset += 15
                    # clamp
                    if self.scroll_offset > self.max_scroll_offset:
                        self.scroll_offset = self.max_scroll_offset
                    must_update = True

            if event.type == MOUSEBUTTONUP and event.button == 1 and item.is_clicked:
                if not self.selection:
                    item.is_clicked = False
                    item_must_update = True
                    must_update = True
                else:
                    if self.selected_index != i:
                        item.is_clicked = False
                        item_must_update = True
                        must_update = True

            if item_must_update:
                item.draw()
                items[i] = item
                render_list[i] = item.surf, item.rect

        self.render_list = render_list
        self.items = items

        return must_update, clicked_index

    def build_list(self):
        height = self.item_height
        width = self.item_length
        margin = self.item_margin
        rect_template = self.item_rect_template.copy()

        items = []
        render_list = []
        for i, text in enumerate(self.list):
            rect = rect_template.copy()
            rect.top += i * (margin + height)

            item = ListItem(width=width, height=height, text=text, rect=rect, base_color=self.base_color,
                            hover_color=self.hover_color, pressed_color=self.pressed_color)

            items.append(item)
            render_list.append((item.surf, item.rect))

        self.items = items
        self.render_list = render_list

        self.full_surf.fill(self.bg_color)
        self.full_surf.blits(render_list, False)  # noqa
        self.full_rect.top = -self.scroll_offset

        self.surf.blit(self.full_surf, self.full_rect)

    def update(self, dt):
        # self.surf.fill(pygame.Color(255, 74, 74))
        must_update = False
        if self.vertical_scroll:
            item_must_update = False
            for i, item in enumerate(self.items):
                if item.is_hovered:
                    item_must_update = True
                    item.scroll(dt)
                if item_must_update:
                    item.draw()
                    self.items[i] = item
                    self.render_list[i] = item.surf, item.rect

        self.full_surf.fill(self.bg_color)
        self.full_surf.blits(self.render_list, False)
        self.full_rect.top = -self.scroll_offset
        self.surf.blit(self.full_surf, self.full_rect)
        return must_update

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surf, self.rect)


class Button:
    def __init__(self, pos: tuple, size: tuple, text="", base_color: pygame.Color = c.bg_listview,
                 hover_color: pygame.Color = c.bg_listview_hovered, pressed_color: pygame.Color = c.bg_button_pressed,
                 text_color: pygame.Color = c.white, logo_surf: Surface = None, logo_margin: tuple = None):
        """
        A button
        :param pos:
        :param size:
        :param text:
        :param base_color:
        :param hover_color:
        :param pressed_color:
        :param text_color:
        :param logo_surf:
        :param logo_margin: top right bottom left
        """
        self.size = size
        self.text = text
        self.surf = pygame.Surface(size)
        self.rect = self.surf.get_rect()
        self.logo_surf = logo_surf
        if logo_margin is not None:
            self.logo_margin = logo_margin
        else:
            self.logo_margin = (10, 10, 10, 10)  # top right bottom left

        self.base_color = base_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.text_color = text_color

        self.color = self.base_color

        self.text_surf, self.text_rect = text_input_font.render(text, self.text_color)
        if logo_surf is not None:
            x, y = size
            top, right, bottom, left = self.logo_margin
            x -= right + left
            y -= top + bottom
            self.logo_surf = aspect_scale(logo_surf, (x, y), smooth=True)

            self.text_rect.left = self.logo_surf.get_width() + right + left
            self.text_rect.centery = self.rect.centery
        else:
            self.text_rect.center = self.rect.center
        self.rect.topleft = pos

        self.must_update = False
        self.is_hovered = False
        self.is_clicked = False

    def handle_input(self, event) -> bool:
        collides = self.rect.collidepoint(event.pos)

        if event.type == MOUSEMOTION:
            if collides and not self.is_hovered:
                self.is_hovered = True
                self.must_update = True
            elif not collides and self.is_hovered:
                self.is_hovered = False
                self.must_update = True

        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            if collides and not self.is_clicked:
                self.is_clicked = True
                self.must_update = True
            elif not collides and self.is_clicked:
                self.is_clicked = False
                self.must_update = True

        elif event.type == MOUSEBUTTONUP and event.button == 1 and self.is_clicked:
            self.color = c.bg_listview
            self.is_clicked = False
            self.must_update = True

        return self.must_update

    def draw(self, screen: pygame.Surface):
        self.color = self.hover_color if self.is_hovered else self.base_color
        self.color = self.pressed_color if self.is_clicked else self.color

        self.surf.fill(self.color)
        if self.logo_surf is not None:
            self.surf.blit(self.logo_surf, (self.logo_margin[3], self.logo_margin[0]))
        self.surf.blit(self.text_surf, self.text_rect)

        screen.blit(self.surf, self.rect)


class Notification:
    def __init__(self, title: str, message: str, sound: bool = False):
        self.title_text = title
        self.message_text = message
        self.has_sound = sound

        #


class LoadingCircleLoop:
    def __init__(self, radius: int = 120, width: int = 40, duration: float = 1, color: pygame.Color = c.blue_highlight):
        self.radius = radius
        self.duration = duration
        self.width = width
        self.size = 2 * self.radius
        self.color = color
        self.bg_color = invert_color(color)

        self.surf = Surface((self.size, self.size))
        self.surf.set_colorkey(self.bg_color, RLEACCEL)

        self.time_passed = 0
        self.forward = True

        self.interpolator = easing_functions.QuadEaseOut(start=self.width / 3 * 2, end=self.radius,
                                                         duration=self.duration)

    def update(self, dt):
        if self.time_passed > self.duration:
            self.forward = False
        elif self.time_passed < 0:
            self.forward = True

        if self.forward:
            self.time_passed += dt
        else:
            self.time_passed -= dt

        self.radius = self.interpolator.ease(self.time_passed)

    def draw(self):
        self.surf.fill(self.bg_color)

        pygame.draw.circle(self.surf, self.color, center=(self.size / 2, self.size / 2), radius=self.radius,
                           width=self.width)
