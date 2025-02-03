import pygame
import random
from pygame import mixer
import numpy as np
from enum import Enum
from collections import deque
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_SIZE = 600
CELL_SIZE = 20
GRID_CELLS = GRID_SIZE // CELL_SIZE
GAME_DURATION = 100  # seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_GREEN = (57, 255, 20)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (255, 0, 255)  # Fruit color
YELLOW = (255, 255, 0)

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    def __init__(self, x, y, color, is_ai=False):
        self.body = [(x, y)]
        self.direction = Direction.RIGHT
        self.color = color
        self.score = 0
        self.is_ai = is_ai
        self.memory = deque(maxlen=50) if is_ai else None
        self.stuck_counter = 0 if is_ai else None

    def move(self, fruit_pos=None, other_snake=None):
        current = self.body[0]
        direction = self.direction.value
        new_head = (current[0] + direction[0], current[1] + direction[1])

        # Handle wall collision
        if new_head[0] < 0 or new_head[0] >= GRID_CELLS or \
           new_head[1] < 0 or new_head[1] >= GRID_CELLS:
            # Choose random new direction
            available_directions = list(Direction)
            available_directions.remove(self.direction)
            self.direction = random.choice(available_directions)
            direction = self.direction.value
            new_head = (current[0] + direction[0], current[1] + direction[1])

        self.body.insert(0, new_head)
        if self.is_ai:
            self.memory.append(new_head)

        # Remove tail unless eating fruit
        if new_head != fruit_pos:
            self.body.pop()

        return new_head == fruit_pos

    def ai_move(self, fruit_pos, other_snake):
        if not self.is_ai:
            return False

        # Get current position
        head = self.body[0]
        
        # Calculate distances
        distances = []
        for direction in Direction:
            next_pos = (head[0] + direction.value[0], 
                       head[1] + direction.value[1])
            
            # Check if move is valid
            if self.is_valid_move(next_pos, other_snake):
                # Calculate metrics
                fruit_distance = abs(next_pos[0] - fruit_pos[0]) + \
                               abs(next_pos[1] - fruit_pos[1])
                other_snake_distance = min(abs(next_pos[0] - x) + abs(next_pos[1] - y) 
                                        for x, y in other_snake.body)
                
                # Check if position is in recent memory
                memory_penalty = 5 if next_pos in self.memory else 0
                
                # Calculate score for this move
                score = (-fruit_distance * 2 +  # Want to get closer to fruit
                        other_snake_distance * 3 +  # Want to stay away from other snake
                        -memory_penalty)  # Avoid recently visited positions
                
                distances.append((direction, score))

        if distances:
            # Choose direction with highest score
            self.direction = max(distances, key=lambda x: x[1])[0]
            
            # Increment stuck counter if not moving towards fruit
            if len(self.memory) >= 10:
                unique_positions = len(set(self.memory))
                if unique_positions < 5:  # Snake might be stuck
                    self.stuck_counter += 1
                    if self.stuck_counter > 5:
                        # Choose random direction to escape
                        self.direction = random.choice(list(Direction))
                        self.stuck_counter = 0
                        self.memory.clear()
                else:
                    self.stuck_counter = 0

        return self.move(fruit_pos, other_snake)

    def is_valid_move(self, pos, other_snake):
        # Check boundaries
        if pos[0] < 0 or pos[0] >= GRID_CELLS or \
           pos[1] < 0 or pos[1] >= GRID_CELLS:
            return False
        
        # Check self collision
        if pos in self.body:
            return False
            
        # Check other snake collision
        if pos in other_snake.body:
            return False
            
        return True

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Battle!")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.reset_game()

    def reset_game(self):
        # Initialize snakes at opposite corners
        self.player_snake = Snake(5, 5, RED)
        self.ai_snake = Snake(GRID_CELLS-5, GRID_CELLS-5, BLUE, is_ai=True)
        self.place_fruit()
        self.game_state = "START"
        self.start_time = None
        self.elapsed_time = 0

    def place_fruit(self):
        while True:
            self.fruit_pos = (random.randint(0, GRID_CELLS-1),
                            random.randint(0, GRID_CELLS-1))
            if self.fruit_pos not in self.player_snake.body and \
               self.fruit_pos not in self.ai_snake.body:
                break

    def draw_snake(self, snake):
        # Draw body
        for segment in snake.body:
            x = self.grid_offset_x + segment[0] * CELL_SIZE
            y = self.grid_offset_y + segment[1] * CELL_SIZE
            pygame.draw.rect(self.screen, snake.color,
                           (x, y, CELL_SIZE, CELL_SIZE))

        # Draw head with eyes
        head = snake.body[0]
        head_x = self.grid_offset_x + head[0] * CELL_SIZE
        head_y = self.grid_offset_y + head[1] * CELL_SIZE
        
        # Draw slightly larger head
        pygame.draw.rect(self.screen, snake.color,
                        (head_x, head_y, CELL_SIZE, CELL_SIZE))
        
        # Draw eyes
        eye_radius = CELL_SIZE // 6
        # Left eye
        pygame.draw.circle(self.screen, WHITE,
                         (head_x + CELL_SIZE//3, head_y + CELL_SIZE//3),
                         eye_radius)
        # Right eye
        pygame.draw.circle(self.screen, WHITE,
                         (head_x + 2*CELL_SIZE//3, head_y + CELL_SIZE//3),
                         eye_radius)
        
        # Draw pupils
        pupil_radius = eye_radius // 2
        # Left pupil
        pygame.draw.circle(self.screen, BLACK,
                         (head_x + CELL_SIZE//3, head_y + CELL_SIZE//3),
                         pupil_radius)
        # Right pupil
        pygame.draw.circle(self.screen, BLACK,
                         (head_x + 2*CELL_SIZE//3, head_y + CELL_SIZE//3),
                         pupil_radius)

    def draw_start_screen(self):
        self.screen.fill(BLACK)
        
        # Create animated title
        title_font = pygame.font.Font(None, 80)
        time_val = pygame.time.get_ticks() / 1000
        title_scale = 1.0 + 0.1 * np.sin(time_val * 2)
        title = title_font.render("SNAKE BATTLE!", True, YELLOW)
        title = pygame.transform.scale(title, 
            (int(title.get_width() * title_scale), 
             int(title.get_height() * title_scale)))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
        self.screen.blit(title, title_rect)

        # Create animated play button
        button_color = NEON_GREEN
        button_rect = pygame.Rect(0, 0, 200, 60)
        button_rect.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
        
        # Add glow effect
        glow_size = 10 * (1 + 0.2 * np.sin(time_val * 4))
        glow_rect = button_rect.inflate(glow_size, glow_size)
        pygame.draw.rect(self.screen, (0, 150, 0), glow_rect, border_radius=15)
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
        
        # Add button text
        play_font = pygame.font.Font(None, 50)
        play_text = play_font.render("PLAY!", True, BLACK)
        text_rect = play_text.get_rect(center=button_rect.center)
        self.screen.blit(play_text, text_rect)
        
        # Draw decorative snakes
        self.draw_decorative_snake((200, 600), RED)
        self.draw_decorative_snake((800, 600), BLUE)
        
        return button_rect

    def draw_decorative_snake(self, pos, color):
        time_val = pygame.time.get_ticks() / 1000
        segments = []
        
        # Create wavy motion
        for i in range(5):
            x = pos[0] + np.sin(time_val * 2 + i * 0.5) * 20
            y = pos[1] + np.cos(time_val * 2 + i * 0.5) * 20
            segments.append((int(x), int(y)))
        
        # Draw body segments
        for i in range(len(segments)-1):
            start = segments[i]
            end = segments[i+1]
            pygame.draw.line(self.screen, color, start, end, 5)
            pygame.draw.circle(self.screen, color, start, 5)
        
        # Draw head
        pygame.draw.circle(self.screen, color, segments[0], 10)
        
        # Draw eyes
        eye_offset = 3
        pygame.draw.circle(self.screen, WHITE, 
                         (segments[0][0] - eye_offset, segments[0][1] - eye_offset), 2)
        pygame.draw.circle(self.screen, WHITE, 
                         (segments[0][0] + eye_offset, segments[0][1] - eye_offset), 2)

    def draw_game(self):
        self.screen.fill(BLACK)
        
        # Draw grid
        self.grid_offset_x = (WINDOW_WIDTH - GRID_SIZE) // 2
        self.grid_offset_y = (WINDOW_HEIGHT - GRID_SIZE) // 2
        
        # Draw grid lines
        for x in range(GRID_CELLS + 1):
            pygame.draw.line(self.screen, NEON_GREEN,
                           (self.grid_offset_x + x * CELL_SIZE, self.grid_offset_y),
                           (self.grid_offset_x + x * CELL_SIZE, self.grid_offset_y + GRID_SIZE))
        for y in range(GRID_CELLS + 1):
            pygame.draw.line(self.screen, NEON_GREEN,
                           (self.grid_offset_x, self.grid_offset_y + y * CELL_SIZE),
                           (self.grid_offset_x + GRID_SIZE, self.grid_offset_y + y * CELL_SIZE))
        
        # Draw fruit
        fruit_x = self.grid_offset_x + self.fruit_pos[0] * CELL_SIZE
        fruit_y = self.grid_offset_y + self.fruit_pos[1] * CELL_SIZE
        pygame.draw.rect(self.screen, PURPLE,
                        (fruit_x, fruit_y, CELL_SIZE, CELL_SIZE))
        
        # Draw snakes
        self.draw_snake(self.player_snake)
        self.draw_snake(self.ai_snake)
        
        # Draw scores
        score_text = f"Player: {self.player_snake.score}  AI: {self.ai_snake.score}"
        score_surface = self.font.render(score_text, True, WHITE)
        self.screen.blit(score_surface, (20, 20))
        
        # Draw timer
        time_left = max(0, GAME_DURATION - self.elapsed_time)
        timer_text = f"Time: {int(time_left)}s"
        timer_surface = self.font.render(timer_text, True, WHITE)
        self.screen.blit(timer_surface, (WINDOW_WIDTH - 150, 20))

    def run(self):
        running = True
        while running:
            if self.game_state == "START":
                play_button = self.draw_start_screen()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if play_button.collidepoint(event.pos):
                            self.game_state = "PLAYING"
                            self.start_time = time.time()
            
            elif self.game_state == "PLAYING":
                current_time = time.time()
                self.elapsed_time = current_time - self.start_time
                
                if self.elapsed_time >= GAME_DURATION:
                    self.game_state = "GAME_OVER"
                    continue
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT and \
                           self.player_snake.direction != Direction.RIGHT:
                            self.player_snake.direction = Direction.LEFT
                        elif event.key == pygame.K_RIGHT and \
                             self.player_snake.direction != Direction.LEFT:
                            self.player_snake.direction = Direction.RIGHT
                        elif event.key == pygame.K_UP and \
                             self.player_snake.direction != Direction.DOWN:
                            self.player_snake.direction = Direction.UP
                        elif event.key == pygame.K_DOWN and \
                             self.player_snake.direction != Direction.UP:
                            self.player_snake.direction = Direction.DOWN
                
                # Move snakes
                if self.player_snake.move(self.fruit_pos, self.ai_snake):
                    self.player_snake.score += 1
                    self.place_fruit()
                
                if self.ai_snake.ai_move(self.fruit_pos, self.player_snake):
                    self.ai_snake.score += 1
                    self.place_fruit()

                player_head = self.player_snake.body[0]
                ai_head = self.ai_snake.body[0]

                # Check if player snake collides with AI snake's body
                if player_head in self.ai_snake.body[1:]:
                    self.player_snake.score = max(0, self.player_snake.score - 1)

                # Check if AI snake collides with player snake's body
                if ai_head in self.player_snake.body[1:]:
                    self.ai_snake.score = max(0, self.ai_snake.score - 1)

                # Draw game state
                self.draw_game()

            elif self.game_state == "GAME_OVER":
                self.screen.fill(BLACK)
                
                # Determine winner
                winner_text = "GAME OVER!"
                if self.player_snake.score > self.ai_snake.score:
                    result_text = "You Won! 😎"
                    winner_color = RED
                elif self.ai_snake.score > self.player_snake.score:
                    result_text = "You lost 🥺"
                    winner_color = BLUE
                else:
                    result_text = "It's a Tie!"
                    winner_color = YELLOW

                # Create animated game over text
                game_over_font = pygame.font.Font(None, 74)
                time_val = pygame.time.get_ticks() / 1000
                scale = 1.0 + 0.1 * np.sin(time_val * 2)
                
                game_over = game_over_font.render(winner_text, True, YELLOW)
                game_over = pygame.transform.scale(game_over, 
                    (int(game_over.get_width() * scale), 
                     int(game_over.get_height() * scale)))
                game_over_rect = game_over.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
                
                # Create result text
                result = game_over_font.render(result_text, True, winner_color)
                result_rect = result.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))

                # Display final scores
                score_text = f"Final Scores - Player: {self.player_snake.score}  AI: {self.ai_snake.score}"
                score_surface = self.font.render(score_text, True, WHITE)
                score_rect = score_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100))

                # Create play again button
                button_color = NEON_GREEN
                button_rect = pygame.Rect(0, 0, 250, 60)
                button_rect.center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 200)
                
                # Add glow effect to button
                glow_size = 10 * (1 + 0.2 * np.sin(time_val * 4))
                glow_rect = button_rect.inflate(glow_size, glow_size)
                pygame.draw.rect(self.screen, (0, 150, 0), glow_rect, border_radius=15)
                pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
                
                # Add button text
                play_again_text = self.font.render("Play Again!", True, BLACK)
                text_rect = play_again_text.get_rect(center=button_rect.center)

                # Draw everything
                self.screen.blit(game_over, game_over_rect)
                self.screen.blit(result, result_rect)
                self.screen.blit(score_surface, score_rect)
                self.screen.blit(play_again_text, text_rect)

                # Draw decorative snakes
                self.draw_decorative_snake((200, 600), RED)
                self.draw_decorative_snake((800, 600), BLUE)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        if button_rect.collidepoint(event.pos):
                            self.reset_game()

            pygame.display.flip()
            self.clock.tick(10)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()