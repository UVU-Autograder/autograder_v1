# Module 8: Lab 6 - Moving an Animal Image Left and Right

## Learning Objectives

In this lab, you will:

- Load and display an image of an animal using Pygame
    
- Animate the animal moving left and right across the Pygame window
    
- Reverse direction when the animal reaches the window edges
    
- Practice two different ways to manage position:
    
    - Using raw `(x, y)` coordinate variables
        
    - Using a `pygame.Rect` object
        

## Part 1: Using `(x, y)` Variables (50 points)

In this part, download an image of an animal (e.g., a cat, dog, or bird). Make sure the image is small—for example, around 100×100 pixels.

- Display the image near the bottom-left corner of the window.
    
- Move it smoothly from left to right.
    
- When it reaches the right edge, reverse direction and move it right to left, continuing to bounce between edges.
    
- Use only the `(x, y)` coordinates of the top-left corner to control position.
    

Save your file as `lab6_part1.py`

## Part 2: Using `pygame.Rect` (50 points)

Repeat the same animation as in Part 1, but this time:

- Use a `pygame.Rect` object to manage the image’s position.
    
- Use `.left` and `.right` to detect collisions with window edges.
    

Save your file as `lab6_part2.py`

## What to Submit

Upload your completed lab as a **zipped folder** to Canvas. Your submission should include:

- Both `.py` files (`lab6_part1.py` and `lab6_part2.py`)
    
- The animal image you used in both parts