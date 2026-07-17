import pygame
import sys

pygame.init()
width = 600
height = 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Animal Animation - Part 2")

try:
    animal = pygame.image.load("animal.png")
except Exception:
    animal = pygame.Surface((100, 100))
    animal.fill((255, 0, 0))

animal = pygame.transform.scale(animal, (100, 100))
clock = pygame.time.Clock()

def main() -> None:
    # Use pygame.Rect to position
    rect = pygame.Rect(0, height - animal.get_height(), 100, 100)
    speed = 5
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        rect.x += speed
        if rect.right >= width:
            speed = -5
        if rect.left <= 0:
            speed = 5

        screen.fill((255, 255, 255))
        screen.blit(animal, rect)
        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
