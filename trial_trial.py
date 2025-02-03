import pygame
import random
from pygame import mixer
import numpy as np
from enum import Enum
from collections import deque
import time

# Initialize Pygame
pygame.init()
mixer.init()
eating_sound = mixer.Sound('eat.wav')

# Constants
GAME_DURATION = 100  # seconds
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_GREEN = (57, 255, 20)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (255, 0, 255)
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

        if new_head[0] < 0 or new_head[0] >= self.game_cells or \
           new_head[1] < 0 or new_head[1] >= self.game_cells:
            available_directions = list(Direction)
            available_directions.remove(self.direction)
            self.direction = random.choice(available_directions)
            direction = self.direction.value
            new_head = (current[0] + direction[0], current[1] + direction[1])

        self.body.insert(0, new_head)
        if self.is_ai:
            self.memory.append(new_head)

        if new_head != fruit_pos:
            self.body.pop()

        return new_head == fruit_pos

    def ai_move(self, fruit_pos, other_snake):
        # [Previous AI move logic remains the same]
        pass

    def is_valid_move(self, pos, other_snake):
        # [Previous validation logic remains the same]
        pass

class Game:
    def __init__(self):
        # Initialize display
        pygame.display.init()
        
        # Get the device's display info
        info = pygame.display.Info()
        self.WINDOW_WIDTH = info.current_w
        self.WINDOW_HEIGHT = info.current_h
        
        # Set up display with fallback resolution if full screen fails
        try:
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT), 
                                                pygame.FULLSCREEN)
        except pygame.error:
            self.WINDOW_WIDTH = 800
            self.WINDOW_HEIGHT = 600
            self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        
        pygame.display.set_caption("Snake Battle!")
        
        # Calculate grid size based on screen dimensions
        self.GRID_SIZE = min(self.WINDOW_WIDTH, self.WINDOW_HEIGHT) * 0.8
        self.CELL_SIZE = self.GRID_SIZE // 30
        self.GRID_CELLS = int(self.GRID_SIZE // self.CELL_SIZE)
        
        # Initialize game objects
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, int(self.WINDOW_HEIGHT * 0.05))
        self.touch_start = None
        self.min_swipe_distance = 30
        
        # Initialize game state
        self.reset_game()

    def reset_game(self):
        # Initialize snakes with the correct grid size
        self.player_snake = Snake(5, 5, RED)
        self.player_snake.game_cells = self.GRID_CELLS
        
        self.ai_snake = Snake(self.GRID_CELLS-5, self.GRID_CELLS-5, BLUE, is_ai=True)
        self.ai_snake.game_cells = self.GRID_CELLS
        
        self.place_fruit()
        self.game_state = "START"
        self.start_time = None
        self.elapsed_time = 0

    def place_fruit(self):
        while True:
            self.fruit_pos = (random.randint(0, self.GRID_CELLS-1),
                            random.randint(0, self.GRID_CELLS-1))
            if self.fruit_pos not in self.player_snake.body and \
               self.fruit_pos not in self.ai_snake.body:
                break

    def handle_touch_events(self, event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * self.WINDOW_WIDTH
            y = event.y * self.WINDOW_HEIGHT
            self.touch_start = (x, y)
        
        elif event.type == pygame.FINGERUP and self.touch_start is not None:
            end_x = event.x * self.WINDOW_WIDTH
            end_y = event.y * self.WINDOW_HEIGHT
            
            dx = end_x - self.touch_start[0]
            dy = end_y - self.touch_start[1]
            
            if abs(dx) > self.min_swipe_distance or abs(dy) > self.min_swipe_distance:
                if abs(dx) > abs(dy):
                    if dx > 0 and self.player_snake.direction != Direction.LEFT:
                        self.player_snake.direction = Direction.RIGHT
                    elif dx < 0 and self.player_snake.direction != Direction.RIGHT:
                        self.player_snake.direction = Direction.LEFT
                else:
                    if dy > 0 and self.player_snake.direction != Direction.UP:
                        self.player_snake.direction = Direction.DOWN
                    elif dy < 0 and self.player_snake.direction != Direction.DOWN:
                        self.player_snake.direction = Direction.UP
            
            self.touch_start = None

    def draw_snake(self, snake):
        for segment in snake.body:
            x = self.grid_offset_x + segment[0] * self.CELL_SIZE
            y = self.grid_offset_y + segment[1] * self.CELL_SIZE
            pygame.draw.rect(self.screen, snake.color,
                           (x, y, self.CELL_SIZE, self.CELL_SIZE))
        
        head = snake.body[0]
        head_x = self.grid_offset_x + head[0] * self.CELL_SIZE
        head_y = self.grid_offset_y + head[1] * self.CELL_SIZE
        
        pygame.draw.rect(self.screen, snake.color,
                        (head_x, head_y, self.CELL_SIZE, self.CELL_SIZE))
        
        eye_radius = self.CELL_SIZE // 6
        pygame.draw.circle(self.screen, WHITE,
                         (head_x + self.CELL_SIZE//3, head_y + self.CELL_SIZE//3),
                         eye_radius)
        pygame.draw.circle(self.screen, WHITE,
                         (head_x + 2*self.CELL_SIZE//3, head_y + self.CELL_SIZE//3),
                         eye_radius)
        
        pupil_radius = eye_radius // 2
        pygame.draw.circle(self.screen, BLACK,
                         (head_x + self.CELL_SIZE//3, head_y + self.CELL_SIZE//3),
                         pupil_radius)
        pygame.draw.circle(self.screen, BLACK,
                         (head_x + 2*self.CELL_SIZE//3, head_y + self.CELL_SIZE//3),
                         pupil_radius)

    def draw_game(self):
        self.screen.fill(BLACK)
        
        # Calculate grid position
        self.grid_offset_x = (self.WINDOW_WIDTH - self.GRID_SIZE) // 2
        self.grid_offset_y = (self.WINDOW_HEIGHT - self.GRID_SIZE) // 2
        
        # Draw grid
        grid_color = (30, 30, 30)
        for x in range(self.GRID_CELLS + 1):
            pygame.draw.line(self.screen, grid_color,
                           (self.grid_offset_x + x * self.CELL_SIZE, self.grid_offset_y),
                           (self.grid_offset_x + x * self.CELL_SIZE, self.grid_offset_y + self.GRID_SIZE),
                           2)
        for y in range(self.GRID_CELLS + 1):
            pygame.draw.line(self.screen, grid_color,
                           (self.grid_offset_x, self.grid_offset_y + y * self.CELL_SIZE),
                           (self.grid_offset_x + self.GRID_SIZE, self.grid_offset_y + y * self.CELL_SIZE),
                           2)
        
        # Draw fruit
        fruit_x = self.grid_offset_x + self.fruit_pos[0] * self.CELL_SIZE
        fruit_y = self.grid_offset_y + self.fruit_pos[1] * self.CELL_SIZE
        pygame.draw.rect(self.screen, PURPLE,
                        (fruit_x, fruit_y, self.CELL_SIZE, self.CELL_SIZE))
        
        # Draw snakes
        self.draw_snake(self.player_snake)
        self.draw_snake(self.ai_snake)
        
        # Draw UI
        score_text = f"You: {self.player_snake.score}  AI: {self.ai_snake.score}"
        score_surface = self.font.render(score_text, True, WHITE)
        score_rect = score_surface.get_rect(top=20, centerx=self.WINDOW_WIDTH//2)
        self.screen.blit(score_surface, score_rect)
        
        time_left = max(0, GAME_DURATION - self.elapsed_time)
        timer_text = f"Time: {int(time_left)}s"
        timer_surface = self.font.render(timer_text, True, WHITE)
        timer_rect = timer_surface.get_rect(bottom=self.WINDOW_HEIGHT-20, 
                                          centerx=self.WINDOW_WIDTH//2)
        self.screen.blit(timer_surface, timer_rect)

    def draw_start_screen(self):
        self.screen.fill(BLACK)
        
        title_font = pygame.font.Font(None, int(self.WINDOW_HEIGHT * 0.1))
        time_val = pygame.time.get_ticks() / 1000
        title_scale = 1.0 + 0.1 * np.sin(time_val * 2)
        title = title_font.render("SNAKE BATTLE!", True, YELLOW)
        title = pygame.transform.scale(title, 
            (int(title.get_width() * title_scale), 
             int(title.get_height() * title_scale)))
        title_rect = title.get_rect(center=(self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//3))
        self.screen.blit(title, title_rect)
        
        button_width = self.WINDOW_WIDTH * 0.4
        button_height = self.WINDOW_HEIGHT * 0.15
        button_rect = pygame.Rect(0, 0, button_width, button_height)
        button_rect.center = (self.WINDOW_WIDTH//2, self.WINDOW_HEIGHT//2)
        
        pygame.draw.rect(self.screen, NEON_GREEN, button_rect, border_radius=20)
        
        play_text = self.font.render("TAP TO PLAY!", True, BLACK)
        text_rect = play_text.get_rect(center=button_rect.center)
        self.screen.blit(play_text, text_rect)
        
        return button_rect

    def run(self):
        running = True
        while running:
            if self.game_state == "START":
                play_button = self.draw_start_screen()
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.FINGERUP:
                        touch_x = event.x * self.WINDOW_WIDTH
                        touch_y = event.y * self.WINDOW_HEIGHT
                        if play_button.collidepoint(touch_x, touch_y):
                            self.game_state = "PLAYING"
                            self.start_time = time.time()
                    elif event.type == pygame.MOUSEBUTTONUP:  # Fallback for testing
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
                    elif event.type in (pygame.FINGERDOWN, pygame.FINGERUP):
                        self.handle_touch_events(event)
                    # Fallback keyboard controls for testing
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT and self.player_snake.direction != Direction.RIGHT:
                            self.player_snake.direction = Direction.LEFT
                        elif event.key == pygame.K_RIGHT and self.player_snake.direction != Direction.LEFT:
                            self.player_snake.direction = Direction.RIGHT
                        elif event.key == pygame.K_UP and self.player_snake.direction != Direction.DOWN:
                            self.player_snake.direction = Direction.UP
                        elif event.key == pygame.K_DOWN and self.player_snake.direction != Direction.UP:
                            self.player_snake.direction = Direction.DOWN
                
                if self.player_snake.move(self.fruit_pos, self.ai_snake):
                    self.player_snake.score += 1
                    eating_sound.play()
                    self.place_fruit()
                
                if self.ai_snake.ai_move(self.fruit_pos, self.player_snake):
                    self.ai_snake.score += 1
                    eating_sound.play()
                    self.place_fruit()
                
                self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(30)  # Increased FPS for smoother motion

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()