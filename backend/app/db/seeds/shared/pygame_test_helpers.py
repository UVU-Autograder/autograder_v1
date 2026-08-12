import ast
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock


class GameLoopExit(BaseException):
    """Stop an otherwise infinite game loop during headless test execution."""


class FakeEvent:
    def __init__(self, type_val):
        self.type = type_val


try:
    import pygame

    FakeRect = pygame.Rect
except ImportError:

    class FakeRect:
        def __init__(self, left, top, width=0, height=0):
            self.left = left
            self.top = top
            self.width = width
            self.height = height
            self.x = left
            self.y = top

        @property
        def right(self):
            return self.x + self.width

        @right.setter
        def right(self, val):
            self.x = val - self.width

        @property
        def bottom(self):
            return self.y + self.height

        @bottom.setter
        def bottom(self, val):
            self.y = val - self.height


def execute_with_mock_pygame(file_path):
    mock_pygame = MagicMock()
    mock_pygame.QUIT = 256
    mock_pygame.event.Event = FakeEvent
    mock_pygame.Rect = FakeRect

    mock_surface = MagicMock()
    mock_surface.get_width.return_value = 100
    mock_surface.get_height.return_value = 100
    mock_surface.convert.return_value = mock_surface
    mock_surface.convert_alpha.return_value = mock_surface
    mock_surface.get_rect.return_value = FakeRect(0, 500, 100, 100)

    mock_pygame.display.set_mode.return_value = mock_surface
    mock_pygame.transform.scale.return_value = mock_surface
    mock_pygame.image.load.return_value = mock_surface
    mock_pygame.time.Clock.return_value.tick.return_value = 16

    loop_counter = 0

    def event_get_mock(*args, **kwargs):
        nonlocal loop_counter
        loop_counter += 1
        if loop_counter == 1:
            return []
        if loop_counter >= 3:
            raise GameLoopExit()
        return [FakeEvent(256)]

    def tick_mock(*args, **kwargs):
        if loop_counter >= 3:
            raise GameLoopExit()
        return 16

    mock_pygame.event.get.side_effect = event_get_mock
    mock_pygame.time.Clock.return_value.tick.side_effect = tick_mock
    mock_pygame.display.update.side_effect = tick_mock
    mock_pygame.display.flip.side_effect = tick_mock

    old_pygame = sys.modules.get("pygame")
    sys.modules["pygame"] = mock_pygame
    try:
        runpy.run_path(file_path, run_name="__main__")
    except (GameLoopExit, SystemExit):
        pass
    finally:
        if old_pygame is None:
            sys.modules.pop("pygame", None)
        else:
            sys.modules["pygame"] = old_pygame

    return mock_pygame, mock_surface


def _is_rect_call(node):
    return isinstance(node, ast.Call) and (
        (isinstance(node.func, ast.Name) and node.func.id == "Rect")
        or (isinstance(node.func, ast.Attribute) and node.func.attr == "Rect")
    )


def check_ast_no_rect(file_path):
    tree = ast.parse(Path(file_path).read_text(encoding="utf-8"), filename=file_path)
    if any(_is_rect_call(node) for node in ast.walk(tree)):
        raise AssertionError("Part 1 must not instantiate or use pygame.Rect")


def check_ast_uses_rect(file_path):
    tree = ast.parse(Path(file_path).read_text(encoding="utf-8"), filename=file_path)
    assert any(_is_rect_call(node) for node in ast.walk(tree)), (
        "Part 2 must instantiate pygame.Rect"
    )
