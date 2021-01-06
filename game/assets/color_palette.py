from pygame import Color

__all__ = ["bg_title_scene", "bg_game_scene", "white", "blue_highlight", "lightblue_highlight", "bg_listview",
           "bg_listview_hovered", "bg_button_pressed"]

# standard colors
white = Color((255, 255, 255))
black = Color((0, 0, 0))
grey = Color((25, 25, 25))
green = Color((75, 255, 99))
orange = Color((255, 183, 75))

# Background colors
bg_title_scene = Color((57, 76, 98)),
bg_game_scene = Color((17, 36, 58))

# highlight
blue_highlight = Color(75, 158, 255)
lightblue_highlight = Color(171, 210, 255)

# list_view
bg_listview = Color(45, 95, 153)
bg_listview_hovered = Color(112, 178, 255)

# button
bg_button_pressed = Color(45, 95, 255)

# error
error_bg = Color(58, 17, 33)
error = Color(255, 75, 75)
