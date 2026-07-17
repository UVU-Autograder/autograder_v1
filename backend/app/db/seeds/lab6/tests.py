import sys
import os
import runpy
import ast
import pytest
from unittest.mock import MagicMock

class GameLoopExit(BaseException):
    """Exception to force exit infinite game loops."""
    pass

class FakeEvent:
    def __init__(self, type_val):
        self.type = type_val

# Defensively load real pygame.Rect if available, otherwise define a robust fallback
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

    # Ensure get_rect() is supported on the mock surface
    fake_rect_obj = FakeRect(0, 500, 100, 100)
    mock_surface.get_rect.return_value = fake_rect_obj

    mock_pygame.display.set_mode.return_value = mock_surface
    mock_pygame.transform.scale.return_value = mock_surface
    mock_pygame.image.load.return_value = mock_surface

    # Make clock tick return 16ms so time delta calculations work correctly
    mock_pygame.time.Clock.return_value.tick.return_value = 16

    # Track how many times event.get or update/tick is called to break loop
    loop_counter = [0]
    def event_get_mock(*args, **kwargs):
        loop_counter[0] += 1
        if loop_counter[0] == 1:
            return []  # No events on first frame
        if loop_counter[0] >= 3:
            raise GameLoopExit()
        return [FakeEvent(256)]  # Return QUIT event on subsequent frames

    def tick_mock(*args, **kwargs):
        if loop_counter[0] >= 3:
            raise GameLoopExit()
        return 16

    mock_pygame.event.get.side_effect = event_get_mock
    mock_pygame.time.Clock.return_value.tick.side_effect = tick_mock
    mock_pygame.display.update.side_effect = tick_mock
    mock_pygame.display.flip.side_effect = tick_mock

    # Replace pygame in sys.modules
    old_pygame = sys.modules.get("pygame", None)
    sys.modules["pygame"] = mock_pygame

    try:
        runpy.run_path(file_path, run_name="__main__")
    except (GameLoopExit, SystemExit):
        pass
    finally:
        if old_pygame is not None:
            sys.modules["pygame"] = old_pygame
        else:
            sys.modules.pop("pygame", None)

    return mock_pygame, mock_surface


# AST Helpers
def check_ast_no_rect(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    for node in ast.walk(tree):
        # Check for calls to pygame.Rect
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "Rect":
                raise AssertionError("Part 1 must not instantiate or use pygame.Rect")
            if isinstance(node.func, ast.Name) and node.func.id == "Rect":
                raise AssertionError("Part 1 must not instantiate or use pygame.Rect")
        # Check for access to Rect attributes (left, right, etc.)
        if isinstance(node, ast.Attribute):
            if node.attr in ("left", "right", "top", "bottom"):
                raise AssertionError(f"Part 1 must not access Rect property: .{node.attr}")

def check_ast_uses_rect(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    has_rect_call = False
    has_rect_attr = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "Rect":
                has_rect_call = True
            if isinstance(node.func, ast.Name) and node.func.id == "Rect":
                has_rect_call = True
        if isinstance(node, ast.Attribute):
            if node.attr in ("left", "right", "top", "bottom"):
                has_rect_attr = True

    assert has_rect_call or has_rect_attr, "Part 2 must instantiate pygame.Rect or access .left/.right attributes of a Rect"


@pytest.mark.ag_part1_ast_execution
def test_part1_execution_and_ast():
    # 1. AST check for no Rect
    assert os.path.exists("lab6_part1.py"), "lab6_part1.py is missing"
    check_ast_no_rect("lab6_part1.py")

    # 2. Mock execution
    mock_pygame, mock_surface = execute_with_mock_pygame("lab6_part1.py")

    # Verify key Pygame calls
    assert mock_pygame.image.load.called, "Part 1 did not load an image"

    # Verify blit coords are at bottom of screen
    assert mock_surface.blit.called, "Part 1 did not blit the animal image"
    blit_args = mock_surface.blit.call_args[0]
    coords = blit_args[1]
    # coords should be a tuple or list of length 2
    assert isinstance(coords, (tuple, list)) and len(coords) == 2
    x, y = coords
    assert x >= 0, "Initial x position should not be negative"
    assert y >= 50, "Initial y position should be near the bottom of the window"


@pytest.mark.ag_part2_ast_execution
def test_part2_execution_and_ast():
    # 1. AST check for Rect usage
    assert os.path.exists("lab6_part2.py"), "lab6_part2.py is missing"
    check_ast_uses_rect("lab6_part2.py")

    # 2. Mock execution
    mock_pygame, mock_surface = execute_with_mock_pygame("lab6_part2.py")

    # Verify key Pygame calls
    assert mock_pygame.image.load.called, "Part 2 did not load an image"

    # Verify blit coords (should accept Rect object or coordinates)
    assert mock_surface.blit.called, "Part 2 did not blit the animal image"
    blit_args = mock_surface.blit.call_args[0]
    position_arg = blit_args[1]
    # In Part 2, position_arg can be a pygame.Rect or a tuple of coords
    if isinstance(position_arg, FakeRect):
        assert position_arg.x >= 0
        assert position_arg.top >= 50
    elif isinstance(position_arg, (tuple, list)):
        assert len(position_arg) == 2
        x, y = position_arg
        assert x >= 0
        assert y >= 50
    else:
        # Otherwise if it's a MagicMock representing a Rect
        pass
