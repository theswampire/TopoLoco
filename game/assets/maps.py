from pygame import image
from pygame.sprite import Sprite

__all__ = ["Map"]


class Map(Sprite):
    def __init__(self, image_path):
        """
        :param image_path: form 'resources/textures/maps/filename.png'
        """
        super(Map, self).__init__()
        self.surf = image.load(image_path).convert_alpha()
        # self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect = self.surf.get_rect()
        self.original_surf = self.surf.copy()

    def reset_surf(self):
        self.surf = self.original_surf.copy()
