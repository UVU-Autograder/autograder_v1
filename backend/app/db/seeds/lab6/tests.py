import os

import pytest
from pygame_test_helpers import (
    FakeRect,
    check_ast_no_rect,
    check_ast_uses_rect,
    execute_with_mock_pygame,
)


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
        pytest.fail(f"unexpected blit position type: {type(position_arg)!r}")
