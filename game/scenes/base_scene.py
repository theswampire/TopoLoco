from pygame import Surface


class SceneBase:
    def __init__(self):
        """
        Initialization of the Base Class for a Scene
        """
        self.next = self
        self.fader = None
        self.oneshot_rendered = False
        self.full_render = False

    def ProcessInput(self, events, pressed_keys, dt):
        """
        Input/Event Processor
        :param events: list of pygame events, probably filtered
        :param pressed_keys: list of pressed keys
        :param dt: Delta Time Passed between current and previous frame
        :return:
        """
        raise NotImplementedError

    def Update(self, dt):
        """
        Method to update scene, such as change text etc
        :param dt: Delta Time Passed between current and previous frame
        :return:
        """
        raise NotImplementedError

    def Render(self, screen: Surface):
        """
        Method to render the updated scene onto screen
        :param screen: pygame.Surface to draw/blit on
        :return:
        """
        raise NotImplementedError

    def SwitchToScene(self, next_scene):
        """
        Method to Change Scene
        :param next_scene: Subclass of SceneBase to switch to
        :return:
        """
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)
