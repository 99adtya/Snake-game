import pygame
import random
import numpy as np
from enum import Enum

class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Snake:
    def __init__(self, x, y, color, name):
        """Initialize a snake with starting position, color and name"""
        self.body = [(x, y)]
        self.direction = random.choice(list(Direction))
        self.color = color
        self.name = name
        self.is_alive = True
        self.score = 0
        self.last_positions = []  # Store last few positions to detect being stuck

    def get_head(self):
        """Return the position of snake's head"""
        return self.body[0]

    def move(self, food_pos, other_snake):
        """
        Enhanced AI movement logic for the snake with better pathfinding
        and escape mechanisms
        """
        if not self.is_alive:
            return

        head_x, head_y = self.get_head()
        food_x, food_y = food_pos

        # Store current position for stuck detection
        self.last_positions.append((head_x, head_y))
        if len(self.last_positions) > 4:  # Keep only last 4 positions
            self.last_positions.pop(0)

        # Check if snake is stuck (oscillating between same positions)
        is_stuck = len(self.last_positions) >= 4 and len(set(self.last_positions)) <= 2

        # Calculate possible moves with additional scoring factors
        possible_moves = []
        for direction in Direction:
            next_x, next_y = self.get_next_position(direction)
            
            if self.is_safe_move(next_x, next_y, other_snake):
                # Calculate various scoring factors
                distance_to_food = abs(next_x - food_x) + abs(next_y - food_y)
                distance_to_center = abs(next_x - 10) + abs(next_y - 10)  # Distance to center of board
                space_score = self.evaluate_space(next_x, next_y, other_snake)
                
                # If stuck, prioritize moves that break the pattern
                if is_stuck:
                    if (next_x, next_y) not in self.last_positions:
                        space_score += 100  # Heavily favor new positions when stuck
                
                # Combined score (lower is better)
                score = distance_to_food + (distance_to_center * 0.5) - (space_score * 2)
                possible_moves.append((direction, score))

        if possible_moves:
            # Choose the move with the best (lowest) score
            self.direction = min(possible_moves, key=lambda x: x[1])[0]
        else:
            # If no moves available, try emergency escape
            emergency_moves = self.find_emergency_escape(other_snake)
            if emergency_moves:
                self.direction = random.choice(emergency_moves)
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

    def evaluate_space(self, x, y, other_snake):
        """
        Evaluate amount of free space in each direction from a position.
        Returns a score based on available space.
        """
        space_count = 0
        checked = set()
        to_check = [(x, y)]
        
        # Flood fill to count accessible spaces
        while to_check and len(checked) < 20:  # Limit check to avoid too much computation
            curr_x, curr_y = to_check.pop(0)
            if (curr_x, curr_y) in checked:
                continue
                
            checked.add((curr_x, curr_y))
            
            # Check all adjacent squares
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_x, next_y = curr_x + dx, curr_y + dy
                if (next_x, next_y) not in checked and self.is_safe_move(next_x, next_y, other_snake):
                    to_check.append((next_x, next_y))
                    space_count += 1
                    
        return space_count

    def find_emergency_escape(self, other_snake):
        """Find any possible safe move when snake is trapped"""
        emergency_moves = []
        head_x, head_y = self.get_head()
        
        for direction in Direction:
            next_x, next_y = self.get_next_position(direction)
            if 0 <= next_x < 20 and 0 <= next_y < 20:  # Just check board boundaries
                if (next_x, next_y) not in self.body[:-1]:  # Allow moving into tail
                    if (next_x, next_y) not in other_snake.body:
                        emergency_moves.append(direction)
                        
        return emergency_moves

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
        
        # Check self collision (except tail which will move)
        if (x, y) in self.body[:-1]:
            return False
            
        # Check other snake collision
        if (x, y) in other_snake.body:
            return False
            
        return True