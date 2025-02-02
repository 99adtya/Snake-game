import pygame
import random
import numpy as np
from enum import Enum

# Define directions as enum for clarity
class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Snake:
    def __init__(self, x, y, color, name):
        """Initialize a snake with starting position, color and name"""
        self.body = [(x, y)]  # Snake body, list of positions
        self.direction = random.choice(list(Direction))  # Random starting direction
        self.color = color
        self.name = name
        self.is_alive = True
        self.score = 0

    def get_head(self):
        """Return the position of snake's head"""
        return self.body[0]

    def move(self, food_pos, other_snake):
        """
        AI movement logic for the snake.
        Decides direction based on food position and collision avoidance.
        """
        head_x, head_y = self.get_head()
        food_x, food_y = food_pos

        # Calculate possible moves
        possible_moves = []
        for direction in Direction:
            next_x, next_y = self.get_next_position(direction)
            
            # Check if move is safe (no collisions)
            if self.is_safe_move(next_x, next_y, other_snake):
                # Calculate distance to food for this move
                distance = abs(next_x - food_x) + abs(next_y - food_y)
                possible_moves.append((direction, distance))

        if possible_moves:
            # Choose the move that gets us closest to food
            self.direction = min(possible_moves, key=lambda x: x[1])[0]
        else:
            self.is_alive = False
            return

        # Move snake in chosen direction
        next_x, next_y = self.get_next_position(self.direction)
        self.body.insert(0, (next_x, next_y))
        
        # Remove tail unless we're eating food
        if (next_x, next_y) != food_pos:
            self.body.pop()
        else:
            self.score += 1

    def get_next_position(self, direction):
        """Calculate next position based on direction"""
        head_x, head_y = self.get_head()
        
        if direction == Direction.UP:
            return head_x, head_y - 1
        elif direction == Direction.DOWN:
            return head_x, head_y + 1
        elif direction == Direction.LEFT:
            return head_x - 1, head_y
        else:  # RIGHT
            return head_x + 1, head_y

    def is_safe_move(self, x, y, other_snake):
        """Check if moving to (x,y) is safe"""
        # Check wall collision
        if x < 0 or x >= 20 or y < 0 or y >= 20:
            return False
        
        # Check self collision
        if (x, y) in self.body:
            return False
            
        # Check other snake collision
        if (x, y) in other_snake.body:
            return False
            
        return True

class Game:
    def __init__(self):
        """Initialize the game"""
        pygame.init()
        self.width = 800
        self.height = 800
        self.cell_size = 40
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Game')

        # Define colors
        self.BACKGROUND_COLOR = (0, 0, 0)  # Black background
        self.GRID_COLOR = (0, 255, 0)  # Neon green grid
        self.FOOD_COLOR = (255, 0, 255)  # Changed food to magenta for better visibility

        # Create two snakes
        self.snake1 = Snake(5, 5, (255, 0, 0), "Red Snake")  # Red snake
        self.snake2 = Snake(15, 15, (0, 0, 255), "Blue Snake")  # Blue snake
        
        self.place_new_food()
        self.clock = pygame.time.Clock()

    def place_new_food(self):
        """Place food at random position not occupied by snakes"""
        while True:
            self.food_pos = (random.randint(0, 19), random.randint(0, 19))
            if (self.food_pos not in self.snake1.body and 
                self.food_pos not in self.snake2.body):
                break

    def update(self):
        """Update game state"""
        if self.snake1.is_alive:
            self.snake1.move(self.food_pos, self.snake2)
            
        if self.snake2.is_alive:
            self.snake2.move(self.food_pos, self.snake1)

        # Check if food was eaten
        for snake in [self.snake1, self.snake2]:
            if snake.get_head() == self.food_pos:
                self.place_new_food()

    def draw_grid(self):
        """Draw the grid lines"""
        # Draw vertical lines
        for x in range(0, self.width, self.cell_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (x, 0), (x, self.height), 1)
        
        # Draw horizontal lines
        for y in range(0, self.height, self.cell_size):
            pygame.draw.line(self.screen, self.GRID_COLOR, (0, y), (self.width, y), 1)

    def draw(self):
        """Draw the game state"""
        self.screen.fill(self.BACKGROUND_COLOR)  # Black background
        
        # Draw grid
        self.draw_grid()
        
        # Draw food
        food_rect = pygame.Rect(
            self.food_pos[0] * self.cell_size,
            self.food_pos[1] * self.cell_size,
            self.cell_size,
            self.cell_size
        )
        pygame.draw.rect(self.screen, self.FOOD_COLOR, food_rect)

        # Draw snakes
        for snake in [self.snake1, self.snake2]:
            for segment in snake.body:
                segment_rect = pygame.Rect(
                    segment[0] * self.cell_size,
                    segment[1] * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )
                pygame.draw.rect(self.screen, snake.color, segment_rect)

        # Draw scores with black outline for better visibility
        font = pygame.font.Font(None, 36)
        def draw_text_with_outline(text, color, pos):
            # Draw outline (black)
            outline_color = (0, 0, 0)
            for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                text_surface = font.render(text, True, outline_color)
                self.screen.blit(text_surface, (pos[0]+dx, pos[1]+dy))
            # Draw main text
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, pos)

        draw_text_with_outline(f"{self.snake1.name}: {self.snake1.score}", self.snake1.color, (10, 10))
        draw_text_with_outline(f"{self.snake2.name}: {self.snake2.score}", self.snake2.color, (10, 50))

        pygame.display.flip()

    def run(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.update()
            self.draw()
            self.clock.tick(10)  # Control game speed

            # Check game over conditions
            if not (self.snake1.is_alive or self.snake2.is_alive):
                running = False

        # Display winner
        winner = None
        if self.snake1.score > self.snake2.score:
            winner = self.snake1
        elif self.snake2.score > self.snake1.score:
            winner = self.snake2
        
        if winner:
            self.screen.fill(self.BACKGROUND_COLOR)
            font = pygame.font.Font(None, 74)
            text = font.render(f"{winner.name} Wins!", True, winner.color)
            text_rect = text.get_rect(center=(self.width/2, self.height/2))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(2000)  # Show winner for 2 seconds

        pygame.quit()

# Start the game
if __name__ == "__main__":
    game = Game()
    game.run()