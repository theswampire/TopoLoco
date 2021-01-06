import json
import random
from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest
from pathlib import Path
from typing import Union

import requests
from packaging.version import parse as vp
from pygame import Surface, draw, image
from pygame import mixer
from pygame.locals import KEYDOWN, K_SPACE, K_RETURN, MOUSEBUTTONDOWN, K_RCTRL, K_LCTRL, MOUSEMOTION, MOUSEBUTTONUP, \
    K_ESCAPE
from requests import Timeout, ConnectionError

import game.assets.color_palette as c
import game.datasets as ds
import game.updates as upd
from game.animations import SceneFader, Blinker
from game.assets.fonts import *
from game.assets.maps import Map
from game.assets.markers import LocationMarker
from game.assets.ui import TextInputBox, ListView, Button, LoadingCircleLoop
from game.config import *
from game.config import VERSION, __author__ as a
from game.scenes.base_scene import SceneBase
from game.utils import rel_to_root, rel_to_writable, is_custom_path, aspect_scale, multiline_text
import webbrowser

__author__ = a

__all__ = ["SceneBase", "TitleScene", "GameTypingBaseScene", "GameLocationBaseScene", "Categories"]


class GameBaseScene(SceneBase):
    def __init__(self, dataset_path: Union[str, Path]):
        super(GameBaseScene, self).__init__()

        # Data
        self.data = {}
        self.load_data(dataset_path=dataset_path)

        self.markers = []
        self.marker_render = []

        self.load_markers()

        # Game state
        self.currently_asked = ""
        self.current_category = ""

        # Map
        rel_image_path = self.data.get("image_path", None)
        image_path = Path(rel_to_root(f"resources/textures/{rel_image_path}"))
        if not image_path.exists():
            image_path = Path(rel_to_writable(f"textures/{rel_image_path}"))
        self.map = Map(rel_to_root(image_path))
        self.map.surf = aspect_scale(self.map.surf, (SCREEN_WIDTH, SCREEN_HEIGHT), True)
        self.map.rect.topleft = SCREEN_WIDTH - self.map.surf.get_width(), SCREEN_HEIGHT - self.map.surf.get_height()
        self.map.original_surf = self.map.surf

    def load_data(self, dataset_path: Union[str, Path]):
        """
        Load dataset from JSON file.
        For reference look into built-in datasets
        :param dataset_path: must point to a valid file
        :return:
        """
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Path for Dataset invalid: {dataset_path}")
        else:
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.SwitchToScene(SceneFader(fade_to=Categories(), current_scene=self, time=1.3, color=c.grey,
                                                  interpolator="CubicEaseOut"))
                    break

    def Update(self, dt):
        pass

    def Render(self, screen: Surface):
        pass

    def load_markers(self):
        """
        Creates Marker out of data
        :return:
        """
        data = self.data
        markers = []
        marker_render = []
        categories = data["categories"]
        for category in categories:
            locations = data["locations"][category]
            names = locations.keys()
            for name in names:
                position = locations[name]
                marker = LocationMarker(name=name, position=position, category=category)
                markers.append(marker)
                marker_render.append((marker.surf, marker.rect))
        self.markers = markers
        self.marker_render = marker_render

    def world_deg_to_screen_pos(self, pos: tuple):
        """
        Convert coordinates in degrees to screen coordinates
        :param pos: ° Longitude, ° Latitude, East is negative/West is positive, North is Positive/South is Negative
        :return:
        """
        # TODO
        # longitude, latitude = pos
        pass


class GameLocationBaseScene(GameBaseScene):
    def __init__(self, dataset_path: Union[str, Path]):
        super(GameLocationBaseScene, self).__init__(dataset_path=dataset_path)

        self.blop_sfx = mixer.Sound(rel_to_root("resources/audio/Blop.mp3"))
        self.blop_sfx.set_volume(0.7)

        self.select_marker()

        # rendering
        self.render_update_on_click = True

        # Question
        self.question_text, self.question_rect = question_font.render("Wo liegt: ", c.white)
        self.question_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 4 - self.question_text.get_height() / 3 * 2

        # additional surf to fix updating question
        self.question_bg = Surface((SCREEN_WIDTH - self.map.surf.get_width(), SCREEN_HEIGHT))
        self.question_bg_rect = self.question_bg.get_rect()

        self.asked_text, self.asked_rect = question_asked_font.render(self.currently_asked, c.white)
        self.asked_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 4 + self.asked_text.get_height() / 6 * 5

        self.category_text, self.category_text_rect = question_asked_font.render("", c.blue_highlight)
        self.category_text_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 4 + self.question_bg.get_height() / 15

    def ProcessInput(self, events, pressed_keys, dt):
        super(GameLocationBaseScene, self).ProcessInput(events, pressed_keys, dt)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                correct = self.check_markers(event.pos)
                if correct:
                    self.select_marker()
                    self.render_update_on_click = True

    def Update(self, dt):
        if self.render_update_on_click:
            self.asked_text, _ = question_asked_font.render(self.currently_asked, c.white)
            self.category_text, _ = question_asked_font.render(f"({self.current_category})", c.blue_highlight)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_render(screen)

        if self.render_update_on_click:
            self.on_click_render(screen)

    def oneshot_render(self, screen: Surface):
        """
        Render Method called once at the start or if self.oneshot_rendered = False
        :param screen:
        :return:
        """
        # screen.fill(c.black)
        self.map.surf.blits(self.marker_render)
        screen.blit(self.map.surf, self.map.rect)
        # print("oneshot")
        self.oneshot_rendered = True

    def on_click_render(self, screen: Surface):
        """
        Render Method called upon mouse click (or self.render_update_on_click = True)
        :param screen:
        :return:
        """
        self.question_bg.fill(c.bg_game_scene)
        self.question_bg.blit(self.question_text, self.question_rect)
        self.question_bg.blit(self.asked_text, self.asked_rect)
        self.question_bg.blit(self.category_text, self.category_text_rect)

        screen.blit(self.question_bg, self.question_bg_rect)
        self.render_update_on_click = False

    def check_markers(self, mouse_pos: tuple):
        """
        Checks all markers if mouse_pos collides with a marker and then if the marker is the correct one
        :param mouse_pos:
        :return:
        """
        x, y = mouse_pos
        x -= self.map.rect.x
        y -= self.map.rect.y
        # print(f"{x}, {y}")
        # clipboard.copy(f"{x}, {y}")
        for i, marker in enumerate(self.markers):
            if marker.is_clicked((x, y)):
                if marker.is_asked:
                    # print("Correct")
                    self.blop_sfx.play()
                    self.markers[i].is_asked = False
                    return True

        return False

    def select_marker(self):
        """
        Random marker selection
        :return:
        """
        # TODO: More specific algorithm than random choice
        i = random.randint(0, len(self.markers) - 1)
        self.markers[i].is_asked = True
        self.currently_asked = self.markers[i].name
        self.current_category = self.markers[i].category


class GameTypingBaseScene(GameBaseScene):
    def __init__(self, dataset_path: Union[str, Path]):
        super(GameTypingBaseScene, self).__init__(dataset_path=dataset_path)

        self.blop_sfx = mixer.Sound(rel_to_root("resources/audio/Blop.mp3"))
        self.blop_sfx.set_volume(0.7)
        self.wrong_sfx = mixer.Sound(rel_to_root("resources/audio/wrong.wav"))
        self.wrong_sfx.set_volume(0.4)

        # rendering
        self.must_render_update = True
        self.marker_to_render = None

        self.select_marker()

        # Question BG surface
        self.bg_q = Surface((SCREEN_WIDTH - self.map.surf.get_width(), SCREEN_HEIGHT))
        self.bg_q_rect = self.bg_q.get_rect()

        # Question Text
        self.q_text, self.q_text_rect = question_font.render("Wie heisst der Ort: ", c.white)
        self.q_text_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 4 - self.q_text.get_height() / 3 * 2

        self.inputbox = TextInputBox((SCREEN_WIDTH / 12, SCREEN_HEIGHT / 3 - 10), active=True)

        self.category_text, self.category_text_rect = question_asked_font.render("", c.blue_highlight)
        self.category_text_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 4 + self.q_text.get_height()

    def ProcessInput(self, events, pressed_keys, dt):
        super(GameTypingBaseScene, self).ProcessInput(events, pressed_keys, dt)
        ctrl_pressed = pressed_keys[K_LCTRL] or pressed_keys[K_RCTRL]
        for event in events:
            self.inputbox.handle_event(event, ctrl_pressed)

            if event.type == KEYDOWN:
                self.must_render_update = True

                if event.key == K_RETURN:
                    is_correct = self.check_input()
                    if is_correct:
                        self.inputbox.text = ""
                        self.select_marker()
                        self.blop_sfx.play()
                    else:
                        self.wrong_sfx.play()
            self.must_render_update = True

    def check_input(self) -> bool:
        input_text = self.inputbox.text
        if input_text == self.currently_asked:
            return True
        return False

    def select_marker(self) -> None:
        marker = random.choice(self.markers)
        self.currently_asked = marker.name
        self.current_category = marker.category
        self.marker_to_render = (marker.surf, marker.rect)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_render(screen=screen)

        if self.must_render_update:
            self.render_update(screen=screen)

    def Update(self, dt):
        if self.must_render_update:
            self.category_text, _ = question_asked_font.render(f"({self.current_category})", c.blue_highlight)

    def render_update(self, screen: Surface):
        self.must_render_update = False
        self.bg_q.fill(c.bg_game_scene)
        self.bg_q.blit(self.q_text, self.q_text_rect)
        self.bg_q.blit(self.category_text, self.category_text_rect)
        self.inputbox.draw(self.bg_q)
        self.map.reset_surf()
        surf, rect = self.marker_to_render
        self.map.surf.blit(surf, rect)

        screen.blit(self.bg_q, self.bg_q_rect)
        screen.blit(self.map.surf, self.map.rect)

    def oneshot_render(self, screen: Surface):
        screen.fill(c.bg_game_scene)
        screen.blit(self.map.surf, self.map.rect)
        self.oneshot_rendered = True


class TitleScene(SceneBase):
    def __init__(self):
        super(TitleScene, self).__init__()

        self.title, self.title_rect = title_font.render(text="TopoLoco", fgcolor=c.white)
        self.app_version_text, self.app_version_rect = mini_info_font.render(text=f"Version {VERSION}",
                                                                             fgcolor=c.lightblue_highlight)
        self.app_version_rect.bottomright = SCREEN_WIDTH - 20, SCREEN_HEIGHT - 15
        self.proceed_text, self.proceed_rect = question_asked_font.render(text="LEERTASTE oder ENTER",
                                                                          fgcolor=c.lightblue_highlight)
        self.proceed_rect.center = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 7 * 5
        self.logo = image.load(rel_to_root("resources/textures/TopoLoco_icon.png"))

        self.blinker = Blinker(frequency=0.3)

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_RETURN or event.key == K_SPACE:
                    self.SwitchToScene(SceneFader(fade_to=Categories(), current_scene=self, time=1, lock_input=False))
                if event.key == K_ESCAPE:
                    self.Terminate()

    def Update(self, dt):
        self.blinker.update(dt)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.title_rect.center = SCREEN_WIDTH / 2 - 60, SCREEN_HEIGHT / 2

            self.logo = aspect_scale(self.logo, (120, 100), True)
            logo_rect = self.logo.get_rect()
            logo_rect.centery = SCREEN_HEIGHT / 2 - 10
            logo_rect.left = SCREEN_WIDTH / 3 * 2 - 70

            screen.fill(c.blue_highlight)
            screen.blit(self.title, self.title_rect)
            screen.blit(self.app_version_text, self.app_version_rect)
            screen.blit(self.logo, logo_rect)
            screen.blit(self.proceed_text, self.proceed_rect)
            self.oneshot_rendered = True

        draw.rect(screen, c.blue_highlight, self.proceed_rect)
        self.proceed_text.set_alpha(self.blinker.value * 255)
        screen.blit(self.proceed_text, self.proceed_rect)


class Categories(SceneBase):
    def __init__(self):
        # TODO: About site
        super(Categories, self).__init__()
        self.loading_anim = LoadingCircleLoop()
        self.loading_anim_rect = self.loading_anim.surf.get_rect()
        self.loading_bg_surf = Surface((SCREEN_WIDTH, int(SCREEN_HEIGHT / 4 * 3 + 20)))
        self.loading_anim_rect.center = self.loading_bg_surf.get_rect().center

        self.is_loading = False
        self.level_list = []
        self.listview = None

        # Something weird happening here!!!!!!
        # ####################################
        # self.executor = ThreadPoolExecutor()
        # self.level_loading_future = self.executor.submit(self.load_and_build_listview, True)
        # ####################################
        self.level_loading_future = None
        self.load_and_build_listview(True)

        # self.builtins = []
        # self.customs = []
        # self.load_datasets()
        #
        # self.lists = self.builtins + self.customs
        # self.game_names = [x.stem for x in self.lists]

        # self.listview = ListView(self.game_names, selection=True, item_height=40, item_length=350)
        # self.listview.rect.left = SCREEN_WIDTH / 12
        # self.listview.rect.top = SCREEN_HEIGHT / 5 * 2

        marker_icon = image.load(rel_to_root("resources/textures/marker_icon.png")).convert_alpha()
        keyboard_icon = image.load(rel_to_root("resources/textures/keyboard_icon.png")).convert_alpha()

        self.button_location = Button(pos=(SCREEN_WIDTH / 8 * 3, SCREEN_HEIGHT / 5 * 2), size=(200, 50), text="Suchen",
                                      logo_surf=marker_icon, logo_margin=(10, 25, 10, 10))
        self.button_typing = Button(pos=(SCREEN_WIDTH / 8 * 3, SCREEN_HEIGHT / 5 * 2 + 70), size=(200, 50),
                                    text="Schreiben", logo_surf=keyboard_icon)

        self.title, self.title_rect = scene_title_font.render("Level Auswählen", c.white)
        self.title_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 6

        self.title_datasets, self.title_datasets_rect = category_font.render("Verfügbare Level:", c.blue_highlight)
        self.title_datasets_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 3 + 10

        self.title_modes, self.title_modes_rect = category_font.render("Modus:", c.blue_highlight)
        self.title_modes_rect.topleft = SCREEN_WIDTH / 8 * 3, SCREEN_HEIGHT / 3 + 10

        # to library
        library_icon = image.load(rel_to_root("resources/textures/library_icon.png")).convert_alpha()
        self.button_library = Button(pos=(SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 2), size=(290, 50),
                                     text="Online Bibliothek", logo_surf=library_icon, logo_margin=(12, 12, 10, 12))
        self.title_lib, self.title_lib_rect = category_font.render("Weitere Levels:", c.blue_highlight)
        self.title_lib_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 3 + 10
        self.title_updates_text, self.title_updates_rect = category_font.render("Updates:", c.blue_highlight)
        self.title_updates_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 20 * 11

        self.app_version_text, self.app_version_rect = mini_info_font.render(text=f"Version {VERSION}",
                                                                             fgcolor=c.blue_highlight)
        self.app_version_rect.bottomright = SCREEN_WIDTH - 20, SCREEN_HEIGHT - 15

        # updates
        self.loading_circle = LoadingCircleLoop(radius=30, width=10)
        self.loading_circle_rect = self.loading_circle.surf.get_rect()
        self.loading_circle_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 10 * 6
        self.updates_surf = Surface((300, 60))
        self.updates_rect = self.updates_surf.get_rect()
        self.updates_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 10 * 6
        self.is_loading_updates = True
        self.reset_update_loading = False
        self.is_downloading_update = False
        self.button_update_app = Button((SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 3), (200, 50), "Update App",
                                        base_color=c.error, text_color=c.white)
        self.no_update_text, self.no_update_rect = light_italic_font_25.render("Kein App Update verfügbar",
                                                                               c.lightblue_highlight)
        self.no_update_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 3
        self.is_downloading_text, self.is_downloading_rect = light_italic_font_25.render("Downloading Update",
                                                                                         c.lightblue_highlight)
        self.is_downloading_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 3 + 80

        # about
        self.about_title_text, self.about_title_rect = category_font.render("Mehr Infos:", c.blue_highlight)
        self.about_title_rect.topleft = SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 3 + 100
        self.button_about = Button((SCREEN_WIDTH / 3 * 2, SCREEN_HEIGHT / 5 * 3 + 150), (200, 50), "Über")

        self.must_update = False
        self.selected = None

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if (event.type == MOUSEBUTTONDOWN or event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP) and \
                    not self.is_loading:
                self.must_update, clicked_index = self.listview.handle_input(event)
                if clicked_index is not None:
                    self.selected = ds.DATASET_PATH_LIST[clicked_index]

                self.must_update = self.button_location.handle_input(event) or self.must_update
                self.must_update = self.button_typing.handle_input(event) or self.must_update
                self.must_update = self.button_library.handle_input(event) or self.must_update
                self.must_update = self.button_about.handle_input(event) or self.must_update

                if not self.is_loading_updates and upd.APP_UPDATE_AVAILABLE:
                    self.must_update = self.button_update_app.handle_input(event) or self.must_update
                    if self.button_update_app.is_clicked:
                        upd.DO_APP_UPDATE = True

                if self.button_location.is_clicked and self.selected is not None:
                    self.setup_new_location(self.selected)
                if self.button_typing.is_clicked and self.selected is not None:
                    self.setup_new_typing(self.selected)
                if self.button_library.is_clicked:
                    self.SwitchToScene(SceneFader(OnlineLibrary(), self, 0.7))
                if self.button_about.is_clicked:
                    self.SwitchToScene(SceneFader(About(), self, 0.7))

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.SwitchToScene(SceneFader(fade_to=TitleScene(), current_scene=self, time=1.2, color=c.white,
                                                  interpolator="CubicEaseOut"))
                    break

    def Update(self, dt):
        if self.level_loading_future is not None:
            if self.level_loading_future.done():
                self.level_loading_future.result()
                # self.executor.shutdown(True)
                self.level_loading_future = None
                self.is_loading = False
        if self.is_loading:
            self.loading_anim.update(dt)
        elif upd.IS_UPDATE_CHECKING or upd.STARTED_APP_UPDATE:
            self.reset_update_loading = False
            self.is_loading_updates = True
        else:
            self.is_loading_updates = False

        # if self.must_update:
        #     self.listview.update(dt)
        self.listview.update(dt)
        if self.is_loading_updates:
            self.loading_circle.update(dt)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            screen.fill(c.bg_game_scene)
            if not self.is_loading:
                self.listview.draw(screen)
                self.button_typing.draw(screen)
                self.button_location.draw(screen)
                self.button_library.draw(screen)
                self.button_about.draw(screen)

            screen.blit(self.title, self.title_rect)
            screen.blit(self.title_datasets, self.title_datasets_rect)
            screen.blit(self.title_modes, self.title_modes_rect)
            screen.blit(self.title_lib, self.title_lib_rect)
            screen.blit(self.title_updates_text, self.title_updates_rect)
            screen.blit(self.app_version_text, self.app_version_rect)
            screen.blit(self.about_title_text, self.about_title_rect)

            draw.line(screen, c.blue_highlight, start_pos=(SCREEN_WIDTH / 5 * 3, SCREEN_HEIGHT / 6 + 70),
                      end_pos=(SCREEN_WIDTH / 5 * 3, SCREEN_HEIGHT / 6 * 5), width=3)

            self.oneshot_rendered = True
        if self.is_loading:
            self.oneshot_rendered = False
            self.loading_bg_surf.fill(c.bg_game_scene)
            self.loading_anim.draw()
            self.loading_bg_surf.blit(self.loading_anim.surf, self.loading_anim_rect)
            screen.blit(self.loading_bg_surf, (0, (SCREEN_HEIGHT / 4 - 5)))
        else:
            self.listview.draw(screen)

        if self.must_update and not self.is_loading:
            # self.listview.draw(screen)
            self.button_typing.draw(screen)
            self.button_location.draw(screen)
            self.button_library.draw(screen)
            self.button_about.draw(screen)
            if upd.APP_UPDATE_AVAILABLE:
                self.button_update_app.draw(screen)
            self.must_update = False

        if self.is_loading_updates and not self.is_loading:
            self.updates_surf.fill(c.bg_game_scene)
            screen.blit(self.updates_surf, self.updates_rect)
            self.loading_circle.draw()
            screen.blit(self.loading_circle.surf, self.loading_circle_rect)
            if upd.STARTED_APP_UPDATE and not self.is_downloading_update:
                self.is_downloading_update = True
                self.is_downloading_text, _ = light_italic_font_25.render(
                    f"Downloading Update v{upd.LATEST_APP_VERSION}",
                    c.lightblue_highlight)
                screen.blit(self.is_downloading_text, self.is_downloading_rect)
        elif not self.reset_update_loading and not self.is_loading:
            self.reset_update_loading = True
            self.updates_surf.fill(c.bg_game_scene)
            screen.blit(self.updates_surf, self.updates_rect)
            if upd.APP_UPDATE_AVAILABLE:
                self.button_update_app.draw(screen)
            else:
                screen.blit(self.no_update_text, self.no_update_rect)

    def load_datasets(self):
        builtins_list = []
        custom_list = []

        # TODO: Multi-threaded loading variant with specified name instead of filename
        for b, custom in zip_longest(Path(rel_to_root("data/")).iterdir(), Path(rel_to_writable("data/")).iterdir()):
            if b is not None and b.suffix == ".json":
                builtins_list.append(b)
            if custom is not None and custom.suffix == ".json":
                custom_list.append(custom)

        self.builtins = builtins_list
        self.customs = custom_list

    def load_and_build_listview(self, build: bool = True):
        ds.load_datasets()
        dataset_info_list = ds.DATASET_INFO

        level_list = []
        for dataset in dataset_info_list:
            level_list.append(dataset["name"])

        self.level_list = level_list
        if build:
            lv = ListView(level_list, selection=True, item_height=40, item_length=350, vertical_clip_scroll=True)
            lv.rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 5 * 2
            self.listview = lv

    def setup_new_typing(self, dataset_path: Union[str, Path]):
        try:
            new_typing_scene = GameTypingBaseScene(dataset_path=dataset_path)
            self.SwitchToScene(
                next_scene=SceneFader(new_typing_scene, current_scene=self, time=0.7,
                                      interpolator="CubicEaseInOut"))
        except json.JSONDecodeError:
            self.SwitchToScene(next_scene=ErrorOccurred(Categories(), "Dataset could not be read"))
        except KeyError:
            self.SwitchToScene(ErrorOccurred(Categories(), "Dataset is misconfigured or corrupted"))

    def setup_new_location(self, dataset_path: Union[str, Path]):
        try:
            new_location_scene = GameLocationBaseScene(dataset_path=dataset_path)
            self.SwitchToScene(next_scene=SceneFader(new_location_scene, current_scene=self, time=0.7,
                                                     interpolator="CubicEaseInOut"))
        except json.JSONDecodeError:
            self.SwitchToScene(next_scene=ErrorOccurred(Categories(), "Dataset is not readable as JSON"))
        except KeyError:
            self.SwitchToScene(ErrorOccurred(Categories(), "Dataset is misconfigured or corrupted"))


class ErrorOccurred(SceneBase):
    def __init__(self, recover_scene: SceneBase = None, text: str = "Unknown"):
        super(ErrorOccurred, self).__init__()
        self.title, self.title_rect = title_font.render("An ERROR occurred", c.error)
        self.title_rect.center = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 6

        self.text_surf = Surface((SCREEN_WIDTH / 3 * 2, int(SCREEN_HEIGHT / 3)))
        self.text_surf.fill(c.error_bg)
        self.text_rect = self.text_surf.get_rect()
        self.text_rect.center = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 5 * 2

        self.ok_text, self.ok_rect = question_asked_font.render("Press ENTER", c.error)
        self.ok_rect.center = SCREEN_WIDTH / 2, SCREEN_HEIGHT / 6 * 5

        self.multiline(text)
        self.recover_scene = recover_scene

    def multiline(self, text: str):
        y = 40
        lines = text.split("\n")
        for i, line in enumerate(lines):
            txt, rect = question_font.render(line, c.error)
            rect.topleft = 0, y * (i + 1)
            self.text_surf.blit(txt, rect)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_rendered = True
            screen.fill(c.error_bg)
            screen.blit(self.text_surf, self.text_rect)
            screen.blit(self.title, self.title_rect)
            screen.blit(self.ok_text, self.ok_rect)

    def Update(self, dt):
        pass

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.SwitchToScene(
                        SceneFader(self.recover_scene, time=0.5, color=c.black, lock_input=False, current_scene=self))


class OnlineLibrary(SceneBase):
    def __init__(self):
        super(OnlineLibrary, self).__init__()
        self.loading_loop_animation = LoadingCircleLoop()
        self.loading_loop_rect = self.loading_loop_animation.surf.get_rect()
        self.loading_bg_surf = Surface((SCREEN_WIDTH, int(SCREEN_HEIGHT / 4 * 3)))
        self.loading_loop_rect.center = self.loading_bg_surf.get_rect().center

        self.is_loading = True
        self.fetch_successful = False
        self.fetch_done = False
        self.fetch_msg = None
        self.selected = None
        self.clicked_index = None

        self.executor = ThreadPoolExecutor()
        self.all_levels = {}
        self.level_keys = []
        self.level_list = []

        self.level_list_view = None
        self.fetching_future = self.executor.submit(self._fetch_lib)
        self.download_future = None
        # self.load_local_datasets_future = self.executor.submit(ds.load_datasets) # call to refresh local datasets
        self.load_local_datasets_future = None
        self.remove_future = None

        self.must_update = False
        self.must_update_details = False
        self.is_downloading = False
        self.was_successful = True
        self.download_msg = ""

        self.is_downloadable = False
        self.is_updatable = False
        self.is_uptodate = False

        # Title
        self.title_text, self.title_rect = scene_title_font.render(text="Online Bibliothek", fgcolor=c.blue_highlight)
        self.title_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 6
        self.subtitle_text, self.subtitle_rect = category_font.render("Levels:", fgcolor=c.bg_listview)
        self.subtitle_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 3 + 10

        # Details
        self.detail_surf = Surface((600, SCREEN_HEIGHT / 3 * 2 - 10))
        self.detail_rect = self.detail_surf.get_rect()
        self.detail_rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 + 10
        self.description_surf = Surface((500, 250))
        self.description_rect = self.description_surf.get_rect()
        self.description_rect.topleft = 0, 50

        self.download_button = Button((0, 0), (200, 50), "Download", base_color=c.error)
        self.download_button.rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 * 2

        self.update_button = Button((0, 0), (200, 50), "Update", base_color=c.orange)
        self.update_button.rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 * 2

        self.text_uptodate, self.rect_uptodate = light_italic_font_25.render("Up to date", c.bg_listview)
        self.rect_uptodate.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 * 2 + 20

        self.error_text, self.error_rect = light_italic_font_25.render("Unknown", c.error)
        self.error_rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 * 2 + 60

        self.downloading_anim = LoadingCircleLoop(radius=30, width=10)
        self.downloading_anim_rect = self.downloading_anim.surf.get_rect()
        self.downloading_anim_rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 * 2

        self.button_remove = Button((0, 0), (200, 50), "Entfernen", base_color=c.orange, hover_color=c.error,
                                    pressed_color=c.error_bg)
        self.button_remove.rect.topright = SCREEN_WIDTH / 12 * 11 + 16, SCREEN_HEIGHT / 3 * 2

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.SwitchToScene(SceneFader(fade_to=Categories(), current_scene=self, time=0.7, lock_input=True))

            if event.type == MOUSEBUTTONDOWN or event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP:
                if self.level_list_view is not None:
                    self.must_update, clicked_index = self.level_list_view.handle_input(event)
                    if clicked_index is not None:
                        self.selected = self.all_levels[self.level_keys[clicked_index]]
                        self.must_update_details = True
                        self.clicked_index = clicked_index

                if self.is_downloadable:
                    self.must_update_details = self.download_button.handle_input(event) or self.must_update_details
                    if self.download_button.is_clicked and self.selected is not None:
                        self.download_future = self.executor.submit(self._download_selected)
                        self.is_downloading = True
                if self.is_updatable:
                    self.must_update_details = self.update_button.handle_input(event) or self.must_update_details
                    if self.update_button.is_clicked and self.selected is not None:
                        self.download_future = self.executor.submit(self._download_selected)
                        self.is_downloading = True

                if self.is_updatable or self.is_uptodate:
                    self.must_update_details = self.button_remove.handle_input(event) or self.must_update_details
                    if self.button_remove.is_clicked and self.selected is not None:
                        self.remove_future = self.executor.submit(self._remove_selected)
                        self.is_downloading = True

    def Update(self, dt):
        if self.is_loading:
            self.loading_loop_animation.update(dt=dt)
        elif self.fetch_done:
            success, msg = self.fetching_future.result()
            self.must_update = True
            self.fetch_done = False

            self.fetch_successful = success
            if not success:
                print(msg)
                self.fetch_msg = msg
        if self.must_update:
            self.level_list_view.update(dt)

        if self.load_local_datasets_future is not None:
            if self.load_local_datasets_future.done():
                self.load_local_datasets_future.result()
                self.load_local_datasets_future = None
                self.must_update_details = True
                self.is_downloading = False
        if self.download_future is not None:
            if self.download_future.done():
                self.was_successful, self.download_msg = self.download_future.result()
                self.selected = self.all_levels[self.level_keys[self.clicked_index]]
                self.download_future = None
                self.must_update_details = True
                self.is_downloading = False
        if self.remove_future is not None:
            if self.remove_future.done():
                self.was_successful, self.download_msg = self.remove_future.result()
                self.selected = self.all_levels[self.level_keys[self.clicked_index]]
                self.remove_future = None
                self.must_update_details = True
                self.is_downloading = False

        if self.selected is not None:
            state = self.selected.get("state", "downloadable")
            if state == "updatable":
                self.is_updatable = True
                self.is_uptodate = False
                self.is_downloadable = False
            elif state == "downloadable":
                self.is_downloadable = True
                self.is_uptodate = False
                self.is_updatable = False
            elif state == "uptodate":
                self.is_downloadable = False
                self.is_updatable = False
                self.is_uptodate = True

        if self.is_downloading:
            self.downloading_anim.update(dt)
            self.must_update_details = True

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_rendered = True
            screen.fill(c.lightblue_highlight)
            screen.blit(self.title_text, self.title_rect)
            screen.blit(self.subtitle_text, self.subtitle_rect)

        if self.is_loading:
            self.oneshot_rendered = False
            self.loading_bg_surf.fill(c.lightblue_highlight)
            self.loading_loop_animation.draw()
            self.loading_bg_surf.blit(self.loading_loop_animation.surf, self.loading_loop_rect)
            screen.blit(self.loading_bg_surf, (0, (SCREEN_HEIGHT / 4)))
        if self.must_update:
            self.level_list_view.draw(screen)

        if self.must_update_details:
            self.must_update_details = False
            self.detail_surf.fill(c.lightblue_highlight)
            self.description_surf.fill(c.lightblue_highlight)

            name = multiline_text(self.selected["name"], color=c.blue_highlight, font=question_asked_font,
                                  max_length=480)
            description = multiline_text(self.selected.get("description", ""), font=text_input_font,
                                         color=c.bg_listview, max_length=480)
            self.detail_surf.blits(name, False)
            self.description_surf.blits(description, False)

            self.detail_surf.blit(self.description_surf, (0, question_asked_font.size * len(name) + 40))
            screen.blit(self.detail_surf, self.detail_rect)

            if self.is_downloading:
                self.downloading_anim.draw()
                screen.blit(self.downloading_anim.surf, self.downloading_anim_rect)
            elif self.is_downloadable:
                self.download_button.draw(screen)
            elif self.is_updatable:
                self.update_button.draw(screen)
                self.button_remove.draw(screen)
            elif self.is_uptodate:
                screen.blit(self.text_uptodate, self.rect_uptodate)
                self.button_remove.draw(screen)

            if not self.was_successful:
                self.error_text, _ = light_italic_font_25.render(self.download_msg, fgcolor=c.error)
                screen.blit(self.error_text, self.error_rect)

    def SwitchToScene(self, next_scene):
        self.executor.shutdown(wait=False)
        super(OnlineLibrary, self).SwitchToScene(next_scene)

    def _fetch_lib(self, build_listview: bool = True):
        try:
            # import time
            # time.sleep(5)
            response = requests.get(UPDATE_URL)
            if not 200 <= response.status_code < 300:
                return False, "Server unreachable or not ready"

            data = response.json()

            all_levels = data["datasets"]
            level_list = []
            for key in all_levels.keys():
                level_list.append(all_levels[key]["name"])

            ds.load_datasets()

            for dataset in ds.DATASET_INFO:
                filename = dataset["filename"]
                key = Path(filename).stem
                path = Path(dataset.get("path", None))
                if path is None:
                    path = Path(rel_to_writable(f"data/{filename}"))
                try:
                    level = all_levels[key]
                    local_version = vp(dataset["version"])
                    latest_version = vp(level["version"])
                    if local_version < latest_version:
                        state = "updatable"
                    elif local_version >= latest_version:
                        state = "uptodate"
                    else:
                        state = "downloadable"

                    all_levels[key]["state"] = state
                    all_levels[key]["path"] = path
                    all_levels[key]["filename"] = filename

                except KeyError as e:
                    print(f"error: {e}")
                    # dataset not locally existing, so continuing
                    continue

            self.all_levels = all_levels
            self.level_list = level_list
            self.level_keys = list(all_levels.keys())

            if build_listview:
                lv = ListView(level_list, selection=True, bg_color=c.lightblue_highlight, base_color=c.blue_highlight,
                              pressed_color=c.bg_listview, hover_color=c.bg_button_pressed,
                              item_length=550, item_height=50, vertical_clip_scroll=True)
                lv.rect.left = SCREEN_WIDTH / 12
                lv.rect.top = SCREEN_HEIGHT / 5 * 2
                self.level_list_view = lv

            self.is_loading = False
            self.fetch_done = True

            return True, ""

        except (Timeout, ConnectionError) as e:
            print(e)
            return False, "Connection to server timed out or a connection error occurred"

        except (KeyError, ValueError) as e:
            print(e)
            return False, "Couldn't read update data"

    def _download_selected(self):
        url = DATASETS_DOWNLOAD_URL + self.selected["filename"]
        path = self.selected.get("path", Path(rel_to_writable(f"data/{self.selected['filename']}")))
        custom = is_custom_path(path=path)
        success, msg = upd.download_to_dir(url=url, path=path)
        if not success:
            return success, msg

        image_filename = Path(self.selected["image_path"])

        url = DATASETS_DOWNLOAD_URL + image_filename.name
        if custom:
            path = Path(rel_to_writable(f"textures/{image_filename}"))
        else:
            path = Path(rel_to_root(f"resources/textures/{image_filename}"))

        if not (Path(rel_to_root(f"resources/textures/{image_filename}")).exists() or
                Path(rel_to_writable(f"textures/{image_filename}")).exists()):
            success, msg = upd.download_to_dir(url, path)
            if not success:
                return success, msg

        return self._fetch_lib(build_listview=False)

    def _remove_selected(self):
        try:
            dataset_info = ds.DATASET_INFO

            path = Path(self.selected["path"])
            path.unlink()

            image_filename = self.selected["image_path"]

            used = False
            for dataset in dataset_info:
                if dataset["path"] == path:
                    continue
                other_imgp = dataset["image_path"]
                if image_filename == other_imgp:
                    used = True
                    break
            if not used:
                image_path = Path(rel_to_writable(f"textures/{image_filename}"))
                if image_path.exists():
                    image_path.unlink()

                image_path = Path(rel_to_root(f"resources/textures/{image_filename}"))
                if image_path.exists():
                    image_path.unlink()

            return self._fetch_lib(build_listview=False)
        except PermissionError:
            return False, "Not enough permissions to remove selected level"
        except FileNotFoundError as e:
            print(f"File not Found error: {e}")
            return False, f"File not found Error"


class About(SceneBase):
    def __init__(self):
        super(About, self).__init__()

        self.title_text, self.title_rect = scene_title_font.render("About", c.blue_highlight)
        self.title_rect.topleft = SCREEN_WIDTH / 12, SCREEN_HEIGHT / 6

        # Project host
        homepage_icon = image.load(rel_to_root("resources/textures/homepage_icon.png")).convert_alpha()
        self.github_logo = image.load(rel_to_root("resources/textures/GitHub-Mark-Light-64px.png")).convert_alpha()
        self.button_github = Button((SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 5 * 2), (160, 50), "GitHub",
                                    logo_surf=self.github_logo, base_color=c.blue_highlight,
                                    pressed_color=c.bg_listview, hover_color=c.bg_button_pressed,
                                    logo_margin=(12, 12, 10, 10))

        self.text_checkout, self.rect_checkout = category_font.render("Check this project out:", c.bg_listview)
        self.rect_checkout.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 3 + 10

        self.button_homepage = Button((SCREEN_WIDTH / 7 * 4 + 180, SCREEN_HEIGHT / 5 * 2), (210, 50), "Homepage",
                                      base_color=c.blue_highlight,
                                      pressed_color=c.bg_listview, hover_color=c.bg_button_pressed,
                                      logo_margin=(10, 13, 10, 10), logo_surf=homepage_icon)

        # Contact
        self.title_contact_text, self.title_contact_rect = category_font.render("Kontakt:", c.bg_listview)
        self.title_contact_rect.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 20 * 11

        self.text_email, self.rect_email = text_input_font.render(CONTACT_EMAIL, c.blue_highlight)
        self.rect_email.topleft = SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 20 * 11 + 40

        self.mail_icon = image.load(rel_to_root("resources/textures/mail_icon.png")).convert_alpha()
        self.button_email = Button((SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 20 * 11 + 80), (170, 50), text="E-Mail",
                                   base_color=c.blue_highlight, logo_surf=self.mail_icon, logo_margin=(12, 20, 10, 10),
                                   pressed_color=c.bg_listview, hover_color=c.bg_button_pressed)
        self.button_contact = Button((SCREEN_WIDTH / 7 * 4, SCREEN_HEIGHT / 20 * 11 + 145), (290, 50),
                                     "Kontakt Formular", base_color=c.blue_highlight, logo_surf=homepage_icon,
                                     pressed_color=c.bg_listview, hover_color=c.bg_button_pressed,
                                     logo_margin=(10, 13, 10, 10))

        # Information
        self.info_texts = multiline_text(f"""TopoLoco - erstellt mit PyGame

Falls du irgendwelche Fehler findest oder einen Vorschlag hast: 
Melde es mir, sodass ich mich dahintersetzen kann!

Version: v{VERSION}, Python 3.8.6
Autor: Kai Siegfried
""",
                                         font=text_input_font, color=c.bg_listview, max_length=480)
        self.info_text = Surface((510, 380))

        self.must_update = False
        self.link_click_cooldown = 2

    def ProcessInput(self, events, pressed_keys, dt):
        for event in events:
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.SwitchToScene(SceneFader(fade_to=Categories(), current_scene=self, time=0.7,
                                                  interpolator="CubicEaseOut"))
                    break
            if event.type == MOUSEBUTTONDOWN or event.type == MOUSEMOTION or event.type == MOUSEBUTTONUP:
                self.must_update = self.button_github.handle_input(event) or self.must_update
                self.must_update = self.button_homepage.handle_input(event) or self.must_update
                self.must_update = self.button_email.handle_input(event) or self.must_update
                self.must_update = self.button_contact.handle_input(event) or self.must_update

                if self.button_github.is_clicked and self.link_click_cooldown >= 2:
                    self.link_click_cooldown = 0
                    self.goto_github()

                if self.button_homepage.is_clicked and self.link_click_cooldown >= 2:
                    self.goto_homepage()
                    self.link_click_cooldown = 0

                if self.button_email.is_clicked and self.link_click_cooldown >= 2:
                    self.mail_to()
                    self.link_click_cooldown = 0

                if self.button_contact.is_clicked and self.link_click_cooldown >= 2:
                    self.goto_homepage_info()
                    self.link_click_cooldown = 0

    def Update(self, dt):
        self.link_click_cooldown += dt

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_render(screen)
        if self.must_update:
            self.button_github.draw(screen)
            self.button_homepage.draw(screen)
            self.button_email.draw(screen)
            self.button_contact.draw(screen)

    def oneshot_render(self, screen: Surface):
        self.oneshot_rendered = True
        screen.fill(c.lightblue_highlight)
        screen.blit(self.title_text, self.title_rect)
        self.button_github.draw(screen)
        self.button_homepage.draw(screen)
        screen.blit(self.text_checkout, self.rect_checkout)
        screen.blit(self.title_contact_text, self.title_contact_rect)
        self.button_email.draw(screen)
        self.button_contact.draw(screen)
        screen.blit(self.text_email, self.rect_email)

        self.info_text.fill(c.lightblue_highlight)
        self.info_text.blits(self.info_texts, False)
        screen.blit(self.info_text, (SCREEN_WIDTH / 12, SCREEN_HEIGHT / 3 + 10))
        draw.line(screen, c.bg_listview, start_pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 6 + 70),
                  end_pos=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 6 * 5), width=3)

    @staticmethod
    def goto_github():
        webbrowser.open(GITHUB_LINK)

    @staticmethod
    def goto_homepage():
        webbrowser.open(HOMEPAGE_LINK)

    @staticmethod
    def mail_to():
        webbrowser.open(MAILTO)

    @staticmethod
    def goto_homepage_info():
        webbrowser.open(HOMEPAGE_INFO_LINK)
