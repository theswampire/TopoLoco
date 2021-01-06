# -*- encoding: utf-8 -*-
import pygame
from pygame.locals import KEYDOWN, QUIT, K_LALT, K_RALT, K_F4

import game.updates as upd
from game.assets.fonts import fps_counter
from game.config import *
from game.scenes import SceneBase, TitleScene
from game.utils import rel_to_root


def main(starting_scene: SceneBase):
    pygame.init()

    update_check_executor, thread = upd.start_update_check()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TopoLoco")
    icon = pygame.image.load(rel_to_root("resources/textures/TopoLoco_icon_32x32.png"))
    pygame.display.set_icon(icon)

    game_clock = pygame.time.Clock()
    game_clock.tick(FPS)
    dt = 0

    fps_text, fps_rect = fps_counter.render("0", (255, 255, 255), (0, 0, 0))

    active_scene = starting_scene

    # MAIN GAME LOOP
    while active_scene is not None:
        active_scene.screen = screen
        pressed_keys = pygame.key.get_pressed()

        upd.check_update(thread, update_check_executor)

        # Event filtering
        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == QUIT:
                quit_attempt = True
            elif event.type == KEYDOWN:
                alt_pressed = pressed_keys[K_LALT] or pressed_keys[K_RALT]

                if event.key == K_F4 and alt_pressed:
                    quit_attempt = True

            if quit_attempt:
                active_scene.Terminate()
            else:
                filtered_events.append(event)

        # Scenes
        active_scene.ProcessInput(filtered_events, pressed_keys, dt)
        active_scene.Update(dt)
        active_scene.Render(screen)

        active_scene = active_scene.next

        # flip, fps
        if SHOW_FPS:
            screen.blit(fps_text, fps_rect)
        pygame.display.flip()
        dt = game_clock.tick(FPS) * 0.001
        if SHOW_FPS:
            fps_text, fps_rect = fps_counter.render(str(round(game_clock.get_fps())), (255, 255, 255), (0, 0, 0))


def launch():
    main(TitleScene())


if __name__ == '__main__':
    main(TitleScene())
