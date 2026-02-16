import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

pygame.init()

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

# Google Snake Colors
WHITE = (255, 255, 255)
RED = (231, 71, 29)      # Apple Red
BLUE1 = (66, 133, 244)   # Google Blue (Head)
BLUE2 = (100, 160, 255)  # Lighter Blue (Body)
BLACK = (0, 0, 0)
BG_GREEN_LIGHT = (170, 215, 81) # Google Light Green
BG_GREEN_DARK = (162, 209, 73)  # Google Dark Green

BLOCK_SIZE = 20
SPEED = 40

class SnakeGameAI:

    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        # init display
        self.display = None # Managed externally if needed, or we just draw to a surface
        self.reset()

    def reset(self):
        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(int(self.w/2), int(self.h/2))
        self.snake = [self.head,
                      Point(self.head.x-BLOCK_SIZE, self.head.y),
                      Point(self.head.x-(2*BLOCK_SIZE), self.head.y)]
        
        # For smooth animation
        self.prev_snake = list(self.snake)
        self.prev_head = self.head

        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0

    def _place_food(self):
        x = random.randint(0, (self.w-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
        self.food = Point(int(x), int(y))
        if self.food in self.snake:
            self._place_food()

    def play_step(self, action):
        self.frame_iteration += 1
        # 1. collect user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        # 2. move
        self._move(action) # update the head
        self.snake.insert(0, self.head)
        
        # 3. check if game over
        reward = 0
        game_over = False
        if self.is_collision() or self.frame_iteration > 50*len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # 4. place new food or just move
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            self.snake.pop()
            
            # REWARD SHAPING: Guide it to food to prevent looping
            # Calculate distance to food
            head = self.snake[0]
            food = self.food
            # dist_current = ((head.x - food.x)**2 + (head.y - food.y)**2)**0.5
            
            # We need previous distance, but we don't store it easily without modifying state.
            # Instead, let's just punish existence slightly more to force urgency.
            reward = -0.05 # Increased penalty from -0.01 to -0.05
        
        return reward, game_over, self.score

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head
        # hits boundary
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            return True
        # hits itself
        if pt in self.snake[1:]:
            return True

        return False

    def _move(self, action):
        # Save previous state before updating
        self.prev_snake = list(self.snake)
        self.prev_head = self.head

        # [straight, right, left]

        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx] # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx] # right turn
        else: # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx] # left turn

        self.direction = new_dir

        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE

        self.head = Point(int(x), int(y))

    def draw(self, surface, x_offset, y_offset, width, height, interpolation=0.0):
        # Create a subsurface or just draw with offsets
        # Scaling might be needed if the display area is smaller than self.w/self.h
        
        scale_x = width / self.w
        scale_y = height / self.h
        
        # Draw Background (Checkered)
        rows = int(self.h / BLOCK_SIZE)
        cols = int(self.w / BLOCK_SIZE)
        
        for r in range(rows):
            for c in range(cols):
                color = BG_GREEN_LIGHT if (r + c) % 2 == 0 else BG_GREEN_DARK
                rect = pygame.Rect(
                    x_offset + c * BLOCK_SIZE * scale_x,
                    y_offset + r * BLOCK_SIZE * scale_y,
                    BLOCK_SIZE * scale_x + 1, # +1 to avoid gaps due to rounding
                    BLOCK_SIZE * scale_y + 1
                )
                pygame.draw.rect(surface, color, rect)

        # Draw Snake with Interpolation
        # To handle growth (snake len > prev_snake len), we treat the new tail as just popping in at the end
        # or just ignore interpolation for the very last segment if lengths differ.
        
        # Helper for interpolation
        def lerp(p1, p2, t):
            return p1 + (p2 - p1) * t

        for i, pt in enumerate(self.snake):
            color = BLUE1 if i == 0 else BLUE2
            
            # Determine current position to draw
            curr_x = pt.x
            curr_y = pt.y
            
            # If we have a previous position for this index, interpolate
            if i < len(self.prev_snake):
                prev_pt = self.prev_snake[i]
                
                # Special case: Wrapping (not applicable here as walls kill) or Respawn
                # If distance is too big, don't interpolate (e.g. after death reset)
                dist = ((curr_x - prev_pt.x)**2 + (curr_y - prev_pt.y)**2)**0.5
                if dist < BLOCK_SIZE * 2: 
                    draw_x = lerp(prev_pt.x, curr_x, interpolation)
                    draw_y = lerp(prev_pt.y, curr_y, interpolation)
                else:
                    draw_x = curr_x
                    draw_y = curr_y
            else:
                # New segment (just ate), no prev position, maybe spawn from previous tail?
                # For simplicity, just draw at current
                draw_x = curr_x
                draw_y = curr_y

            rect = pygame.Rect(
                x_offset + draw_x * scale_x, 
                y_offset + draw_y * scale_y, 
                BLOCK_SIZE * scale_x, 
                BLOCK_SIZE * scale_y
            )
            
            # Round corners for body
            pygame.draw.rect(surface, color, rect, border_radius=int(4*scale_x))
            
            # Eyes for head
            if i == 0:
                eye_radius = 2 * scale_x
                # Simplified eyes logic (static relative to head center for now, could rotate based on dir)
                pygame.draw.circle(surface, WHITE, (rect.centerx - 4*scale_x, rect.centery - 4*scale_y), eye_radius)
                pygame.draw.circle(surface, WHITE, (rect.centerx + 4*scale_x, rect.centery - 4*scale_y), eye_radius)

        # Draw Food (Pulse animation?)
        # Simple pulse using time
        import time
        pulse = (np.sin(time.time() * 10) + 1) / 2 # 0 to 1
        pulse_size = (BLOCK_SIZE * scale_x) * (0.8 + 0.2 * pulse)
        
        center_x = x_offset + self.food.x * scale_x + (BLOCK_SIZE * scale_x) / 2
        center_y = y_offset + self.food.y * scale_y + (BLOCK_SIZE * scale_y) / 2
        
        rect = pygame.Rect(0, 0, pulse_size, pulse_size)
        rect.center = (center_x, center_y)
        
        pygame.draw.rect(surface, RED, rect, border_radius=int(pulse_size/2))
