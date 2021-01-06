from typing import Union

import easing_functions
from pygame import Surface, Color

from game.config import *
from game.scenes.base_scene import SceneBase

__all__ = ["SceneFader", "Blinker"]


class SceneFader(SceneBase):
    def __init__(self, fade_to: SceneBase, current_scene: SceneBase, time: float,
                 color: Color = None, lock_input: bool = True, freeze_scenes: bool = False,
                 interpolator: str = "CubicEaseOut"):
        """
        Used to fade two scenes or fade to a color and then fade to a scene. This implementation is actually a scene
        itself.
        Usage: Call current_scene.SwitchToScene(fader_instance) to fade between to scenes
        :param fade_to: Scene to fade to
        :param current_scene: Current scene to fade from
        :param time: Duration of fade, in seconds
        :param color: If None direct scene fade, else fading color
        :param lock_input: Whether to allow user input on both scenes during fade
        :param interpolator: Name of
        """
        super(SceneFader, self).__init__()
        self.next_scene = fade_to
        self.current_scene = current_scene
        self.color = color
        self.time = time
        self.time_passed = 0
        self.lock_input = lock_input
        self.freeze_scenes = freeze_scenes

        self.direct_fade = color is None
        self.half_done = False
        self.forward = True
        self.oneshot_rendered = False

        self.interpolator = getattr(easing_functions, interpolator)(start=0, end=255,
                                                                    duration=time)

        self.alpha = 0

        self.prev_surf, self.next_surf = Surface((SCREEN_WIDTH, SCREEN_HEIGHT)), Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if not self.direct_fade:
            self.color_surf = Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.color_surf.fill(color)

    def ProcessInput(self, events, pressed_keys, dt):
        if not self.lock_input:
            self.current_scene.ProcessInput(events, pressed_keys, dt)
            self.next_scene.ProcessInput(events, pressed_keys, dt)

    def Update(self, dt):
        if not self.freeze_scenes:
            self.current_scene.Update(dt)
            self.next_scene.Update(dt)

        if not self.direct_fade:
            if self.time_passed >= self.time / 2:
                self.forward = False
                self.half_done = True

            if self.forward:
                self.time_passed += dt
            else:
                self.time_passed -= dt

            if self.time_passed <= 0 and not self.forward:
                self.SwitchToScene(self.next_scene)

        else:
            self.time_passed += dt
            if self.time_passed >= self.time:
                self.SwitchToScene(self.next_scene)

        self.alpha = self.interpolator.ease(self.time_passed)

    def Render(self, screen: Surface):
        if not self.oneshot_rendered:
            self.oneshot_rendered = True
            self.prev_surf.blit(screen, (0, 0))
            if self.freeze_scenes:
                self.current_scene.Render(self.prev_surf)
                self.next_scene.Render(self.next_surf)

        if not self.freeze_scenes:
            self.current_scene.Render(self.prev_surf)
            self.next_scene.Render(self.next_surf)

        if self.direct_fade:
            screen.blit(self.prev_surf, (0, 0))
            self.next_surf.set_alpha(self.alpha)
            screen.blit(self.next_surf, (0, 0))
        else:
            if self.half_done:
                screen.blit(self.next_surf, (0, 0))
            else:
                screen.blit(self.prev_surf, (0, 0))

            self.color_surf.set_alpha(self.alpha)
            screen.blit(self.color_surf, (0, 0))


class Blinker:
    def __init__(self, frequency: Union[int, float], interpolator: str = "CubicEaseOut"):
        self.frequency = frequency
        self.period = 1 / frequency

        self.interpolator = getattr(easing_functions, interpolator)(start=0, end=1, duration=self.period)

        self.value = 0
        self.forward = True

        self.time_passed = 0

    def update(self, dt):
        if self.time_passed > self.period / 2:
            self.forward = False
        elif self.time_passed < 0:
            self.forward = True

        if self.forward:
            self.time_passed += dt
        else:
            self.time_passed -= dt

        self.value = self.interpolator.ease(self.time_passed)
