import sys

import pygame

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Animal Animation - Part 1")

# Create a blank white surface if animal.png does not exist to avoid crashing
try:
    animal = pygame.image.load("animal.png")
except (FileNotFoundError, OSError, pygame.error):
    animal = pygame.Surface((100, 100))
    animal.fill((255, 0, 0))

animal = pygame.transform.scale(animal, (100, 100))
clock = pygame.time.Clock()

def main() -> None:
    x = 0
    y = height - animal.get_height()
    speed = 5
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        x += speed
        if x + animal.get_width() >= width:
            speed = -5
        if x <= 0:
            speed = 5

        screen.fill((255, 255, 255))
        screen.blit(animal, (x, y))
        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
