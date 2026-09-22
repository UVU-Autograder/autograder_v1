# Pygame Assignment Grading Guidelines

This guide details the system architecture and policy constraints for testing and grading student **Pygame** assignments (such as `lab6` in CS 1410). 

---

## 1. Headless Execution in Judge0

Because student submissions are executed inside network-isolated, headless Judge0 microVMs (via Kata Containers), **no display server (X11/Wayland) or physical monitor is available**. 

If a student's code attempts to initialize a Pygame window directly (e.g. calling `pygame.display.set_mode()`), it will crash with an SDL video initialization error.

### The Solution: Dummy Video Driver

To allow Pygame code to execute programmatically without a GUI display, we must force SDL to use its dummy video driver. This is accomplished by setting the `SDL_VIDEODRIVER` environment variable to `dummy` in the grading executor or in the assignment's `pytest` setup.

#### Headless Pytest Setup Example
In the assignment's instructor-owned `conftest.py` or the test file itself:

```python
import os
import pytest

# Force SDL to run headlessly BEFORE importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"  # Do the same for audio/sounds

import pygame

@pytest.fixture(scope="session", autouse=True)
def init_pygame():
    pygame.init()
    yield
    pygame.quit()
```

---

## 2. Testable Logic vs. Manual Inspection

Pygame assignments are graded by dividing requirements into **Automated Pytest Checks** (logic, coordinates, structures) and **Manual Rubric Items** (visual correctness, animation flow).

### A. Programmatic Checks (Pytest)
We write automated tests to assert correctness of math and object state:
*   **Coordinate Boundaries:** Verify that moving visual objects stop at the window borders (e.g., if window width is 800, coordinates do not exceed `800 - sprite_width`).
*   **Velocity Math:** Verify that delta-based position additions (e.g. `x += velocity_x`) calculate correctly.
*   **UML / Inheritance:** Verify that student classes subclass `pygame.sprite.Sprite` or expected base classes.
*   **Event handlers:** Simulate event loops by passing mock pygame events directly to the student's handler methods.

#### Event Mocking Example
```python
class MockEvent:
    def __init__(self, event_type, key):
        self.type = event_type
        self.key = key

def test_character_moves_right():
    from student_code import Character
    char = Character(x=100, y=100)
    
    # Simulate right-arrow key down event
    right_event = MockEvent(pygame.KEYDOWN, pygame.K_RIGHT)
    char.handle_event(right_event)
    char.update()
    
    assert char.rect.x > 100
```

### B. Visual Rubric Items (Manual Grading)
Aspects that are visually subjective or complex to test headlessly are assigned to manual rubric items:
*   **Sprite Assets:** Confirming that custom PNG images are loaded and rendering in correct aspect ratios.
*   **Animation aesthetics:** Checking that frame-transitions look smooth.
*   **UI Layout:** Confirming that text labels, menus, and color palettes align with mockup specifications.

---

## 3. Rubric Setup in `config_json`

When configuring a Pygame assignment in the wizard, structure the scoring items explicitly:

```json
{
  "scoring_items": [
    {
      "key": "sprite_inheritance",
      "label": "Sprite Class Structure (Auto)",
      "points": 20,
      "item_type": "pytest",
      "pytest_marker": "ag_sprite_inheritance"
    },
    {
      "key": "movement_logic",
      "label": "Boundary Movement Mechanics (Auto)",
      "points": 40,
      "item_type": "pytest",
      "pytest_marker": "ag_movement_logic"
    },
    {
      "key": "visual_animation",
      "label": "Smooth Walk Animation & Sprite Rendering (Manual)",
      "points": 40,
      "item_type": "manual"
    }
  ]
}
```
