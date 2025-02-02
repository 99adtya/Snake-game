import pygame
import random
import numpy as np
from enum import Enum
from pathlib import Path
import os

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Snake:
    def __init__(self, x, y, color, name):
        self.body = [(x, y)]
        self.direction = random.choice(list(Direction))
        self.color = color
        self.name = name
        self.is_alive = True
        self.score = 0
        self.previous_positions = []  # Store previous positions to detect loops
        self.stuck_counter = 0
        self.head_sprite = self.create_head_sprite(color)
        self.speed_boost = 1.0  # New: Speed boost multiplier
        self.boost_timer = 0  # New: Timer for speed boost duration
        
    def create_head_sprite(self, color):
        sprite = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(sprite, color, (15, 15), 15)
        
        # Draw eyes
        eye_color = (255, 255, 255)
        pygame.draw.circle(sprite, eye_color, (8, 10), 4)
        pygame.draw.circle(sprite, eye_color, (22, 10), 4)
        
        # Draw pupils
        pupil_color = (0, 0, 0)
        pygame.draw.circle(sprite, pupil_color, (8, 10), 2)
        pygame.draw.circle(sprite, pupil_color, (22, 10), 2)
        
        # Draw smile
        pygame.draw.arc(sprite, (0, 0, 0), (8, 8, 14, 14), 0, np.pi, 2)
        
        return sprite

    def get_head(self):
        return self.body[0]

    def calculate_safe_moves(self, other_snake, food_pos, power_ups, grid_size=20):  # Modified to include power-ups
        head_x, head_y = self.get_head()
        food_x, food_y = food_pos
        safe_moves = []
        
        for direction in Direction:
            next_x, next_y = self.get_next_position(direction)
            if self.is_safe_move(next_x, next_y, other_snake, grid_size):
                distance_to_food = abs(next_x - food_x) + abs(next_y - food_y)
                distance_to_other = min(abs(next_x - x) + abs(next_y - y) 
                                     for x, y in other_snake.body)
                open_space = self.count_open_space(next_x, next_y, other_snake, grid_size)
                
                # New: Consider power-ups in move scoring
                power_up_bonus = 0
                for power_up in power_ups:
                    if (next_x, next_y) == power_up.position:
                        power_up_bonus = 50  # High bonus for power-ups
                
                move_score = (
                    -distance_to_food  # Prefer moves closer to food
                    + distance_to_other * 2  # Prefer moves away from other snake
                    + open_space * 3  # Prefer moves with more open space
                    + power_up_bonus  # New: Consider power-ups
                )
                
                safe_moves.append((direction, move_score))
        
        return safe_moves

    def count_open_space(self, x, y, other_snake, grid_size):
        visited = set()
        stack = [(x, y)]
        
        while stack:
            curr_x, curr_y = stack.pop()
            if (curr_x, curr_y) not in visited:
                visited.add((curr_x, curr_y))
                
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    next_x, next_y = curr_x + dx, curr_y + dy
                    if self.is_safe_move(next_x, next_y, other_snake, grid_size):
                        stack.append((next_x, next_y))
        
        return len(visited)

    def move(self, food_pos, other_snake, power_ups=[]):  # Modified to include power-ups
        # Update speed boost timer
        if self.boost_timer > 0:
            self.boost_timer -= 1
            if self.boost_timer == 0:
                self.speed_boost = 1.0

        safe_moves = self.calculate_safe_moves(other_snake, food_pos, power_ups)
        
        if not safe_moves:
            self.is_alive = False
            return
            
        current_pos = self.get_head()
        self.previous_positions.append(current_pos)
        if len(self.previous_positions) > 20:
            self.previous_positions.pop(0)
            
        if len(self.previous_positions) == 20:
            if len(set(self.previous_positions)) < 5:
                self.stuck_counter += 1
                if self.stuck_counter > 3:
                    self.direction = random.choice(safe_moves)[0]
                    self.stuck_counter = 0
                    self.previous_positions.clear()
                    
        self.direction = max(safe_moves, key=lambda x: x[1])[0]
        
        next_x, next_y = self.get_next_position(self.direction)
        self.body.insert(0, (next_x, next_y))
        
        ate_something = False
        if (next_x, next_y) == food_pos:
            self.score += 1
            ate_something = True
        else:
            self.body.pop()
            
        return ate_something

    def get_next_position(self, direction):
        head_x, head_y = self.get_head()
        
        if direction == Direction.UP:
            return head_x, head_y - 1
        elif direction == Direction.DOWN:
            return head_x, head_y + 1
        elif direction == Direction.LEFT:
            return head_x - 1, head_y
        else:  # RIGHT
            return head_x + 1, head_y

    def is_safe_move(self, x, y, other_snake, grid_size=20):
        if x < 0 or x >= grid_size or y < 0 or y >= grid_size:
            return False
        if (x, y) in self.body:
            return False
        if (x, y) in other_snake.body:
            return False
        return True

class PowerUp:  # New: Power-up class
    def __init__(self, position, power_type):
        self.position = position
        self.type = power_type
        self.duration = 200  # Duration in frames
        self.spawn_time = pygame.time.get_ticks()
        
    def is_expired(self):
        return pygame.time.get_ticks() - self.spawn_time > self.duration

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.width = 1024
        self.height = 800
        self.grid_size = 600
        self.cell_size = self.grid_size // 20
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Snake Battle!')

        self.BACKGROUND_COLOR = (20, 20, 40)
        self.GRID_COLOR = (60, 60, 100)
        self.FOOD_COLOR = (255, 0, 255)
        
        self.rainbow_colors = self.generate_rainbow_colors()
        self.color_index = 0
        self.color_timer = 0
        
        # New: Power-up settings
        self.power_ups = []
        self.power_up_spawn_timer = 0
        self.power_up_types = ['speed', 'shield', 'double_score']
        
        self.load_sounds()
        self.game_state = "START"
        self.setup_new_game()

    def load_sounds(self):
        self.sounds = {}
        sound_files = {
            'eat': 'eat.wav',
            'collision': 'collision.wav',
            'game_over': 'game_over.wav',
            'start_game': 'start_game.wav',
            'power_up': 'power_up.wav'  # New: Power-up sound
        }
        
        if not os.path.exists('sounds'):
            os.makedirs('sounds')
            print("Created 'sounds' directory. Please add sound files:")
            for sound_name, filename in sound_files.items():
                print(f"- {filename}")
        
        for sound_name, filename in sound_files.items():
            path = os.path.join('sounds', filename)
            if os.path.exists(path):
                self.sounds[sound_name] = pygame.mixer.Sound(path)
            else:
                print(f"Missing sound file: {filename}")

    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def generate_rainbow_colors(self):
        colors = []
        for i in range(360):
            hue = i
            saturation = 0.3
            value = 0.95
            
            h = hue / 360
            s = saturation
            v = value
            
            i = int(h * 6)
            f = h * 6 - i
            p = v * (1 - s)
            q = v * (1 - f * s)
            t = v * (1 - (1 - f) * s)
            
            i %= 6
            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            else:
                r, g, b = v, p, q
            
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        
        return colors

    def setup_new_game(self):
        self.grid_offset_x = (self.width - self.grid_size) // 2
        self.grid_offset_y = (self.height - self.grid_size) // 2
        
        self.snake1 = Snake(5, 5, (255, 0, 0), "Red Snake")
        self.snake2 = Snake(15, 15, (0, 0, 255), "Blue Snake")
        self.place_new_food()
        self.power_ups.clear()  # Clear any existing power-ups
        self.clock = pygame.time.Clock()
        self.game_speed = 10  # Base game speed (frames per second)

    def place_new_food(self):
        while True:
            self.food_pos = (random.randint(0, 19), random.randint(0, 19))
            if (self.food_pos not in self.snake1.body and 
                self.food_pos not in self.snake2.body):
                break

    def spawn_power_up(self):
        while True:
            pos = (random.randint(0, 19), random.randint(0, 19))
            if (pos not in self.snake1.body and 
                pos not in self.snake2.body and 
                pos != self.food_pos):
                power_type = random.choice(self.power_up_types)
                self.power_ups.append(PowerUp(pos, power_type))
                break

    def draw_start_screen(self):
        self.screen.fill((20, 20, 50))
        
        title_font = pygame.font.Font(None, 100)
        time_val = pygame.time.get_ticks() / 1000
        title_scale = 1.0 + 0.1 * np.sin(time_val * 2)
        title = title_font.render("SNAKE BATTLE!", True, (255, 255, 0))
        title = pygame.transform.scale(title, 
            (int(title.get_width() * title_scale), 
             int(title.get_height() * title_scale)))
        title_rect = title.get_rect(center=(self.width//2, self.height//3))
        self.screen.blit(title, title_rect)

        play_button = self.create_button("PLAY!", (self.width//2, self.height//2))
        
        self.draw_decorative_snake((200, 600), (255, 0, 0))
        self.draw_decorative_snake((800, 600), (0, 0, 255))
        
        return play_button

    def create_button(self, text, center_pos):
        button_color = (0, 255, 0)
        button_rect = pygame.Rect(0, 0, 200, 60)
        button_rect.center = center_pos
        
        time_val = pygame.time.get_ticks() / 1000
        glow_size = 10 * (1 + 0.2 * np.sin(time_val * 4))
        glow_rect = button_rect.inflate(glow_size, glow_size)
        pygame.draw.rect(self.screen, (0, 150, 0), glow_rect, border_radius=15)
        pygame.draw.rect(self.screen, button_color, button_rect, border_radius=10)
        
        font = pygame.font.Font(None, 50)
        text = font.render(text, True, (0, 0, 0))
        text_rect = text.get_rect(center=button_rect.center)
        self.screen.blit(text, text_rect)
        
        return button_rect

    def draw_decorative_snake(self, pos, color):
        time_val = pygame.time.get_ticks() / 1000
        segments = []
        
        for i in range(5):
            x = pos[0] + np.sin(time_val * 2 + i * 0.5) * 20
            y = pos[1] + np.cos(time_val * 2 + i * 0.5) * 20
            segments.append((int(x), int(y)))
            
        for i in range(len(segments)-1):
            start = segments[i]
            end = segments[i+1]
            segment_color = tuple(int(c * (1 - i/5)) for c in color)
            pygame.draw.line(self.screen, segment_color, start, end, 5)
            pygame.draw.circle(self.screen, segment_color, start, 5)
        
        head_pos = segments[0]
        pygame.draw.circle(self.screen, color, head_pos, 10)
        
        eye_offset = 3
        pygame.draw.circle(self.screen, (255, 255, 255), 
                         (head_pos[0] - eye_offset, head_pos[1] - eye_offset), 2)
        pygame.draw.circle(self.screen, (255,