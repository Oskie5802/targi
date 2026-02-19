import pygame
import random
import time
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

SPEED = 40

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = 1.0 # 1.0 to 0.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        self.size *= 0.95

    def draw(self, surface, x_offset, y_offset, scale):
        if self.life > 0:
            alpha = int(self.life * 255)
            s = pygame.Surface((int(self.size * scale * 2), int(self.size * scale * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size * scale), int(self.size * scale)), int(self.size * scale))
            surface.blit(s, (x_offset + self.x * scale - self.size * scale, y_offset + self.y * scale - self.size * scale))

class SnakeGameAI:

    def __init__(self, w=17, h=17):
        self.w = w
        self.h = h
        # init display
        self.display = None # Managed externally if needed, or we just draw to a surface
        self.particles = []
        self.reset()
        self.BLOCK_SIZE = 1 # Logic block size is 1 unit

    def reset(self):
        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(int(self.w/2), int(self.h/2))
        self.snake = [self.head,
                      Point(self.head.x-1, self.head.y),
                      Point(self.head.x-2, self.head.y)]
        
        # For smooth animation
        self.prev_snake = list(self.snake)
        self.prev_head = self.head

        # Visual feedback for reset (Death)
        # self.last_score = getattr(self, 'score', 0)
        # self.death_timer = 30 if self.last_score > 0 else 0
        # Removing death timer from reset to allow manual control

        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0
        self.particles = [] # Clear particles on reset
        
    def crash(self):
        """Triggers the visual crash effect without resetting the game state fully"""
        self.last_score = getattr(self, 'score', 0)
        self.death_timer = 30 # Set death timer for red flash

    def _place_food(self):
        x = random.randint(0, self.w-1)
        y = random.randint(0, self.h-1)
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
        if self.is_collision() or self.frame_iteration > 100*len(self.snake): # Increased timeout for larger grid relative to snake size
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # 4. place new food or just move
        if self.head == self.food:
            self.score += 1
            reward = 10
            # Add particles (visual only, position doesn't matter for logic here, handled in draw)
            for _ in range(10):
                self.particles.append(Particle(self.head.x + 0.5, self.head.y + 0.5, RED))
            self._place_food()
        else:
            self.snake.pop()
            
            # REWARD SHAPING: Guide it to food to prevent looping
            # Calculate distance to food
            # head = self.snake[0]
            # food = self.food
            # dist_current = ((head.x - food.x)**2 + (head.y - food.y)**2)**0.5
            
            # We need previous distance, but we don't store it easily without modifying state.
            # Instead, let's just punish existence slightly more to force urgency.
            reward = -0.01 
        
        return reward, game_over, self.score

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head
        # hits boundary
        if pt.x >= self.w or pt.x < 0 or pt.y >= self.h or pt.y < 0:
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
            x += 1
        elif self.direction == Direction.LEFT:
            x -= 1
        elif self.direction == Direction.DOWN:
            y += 1
        elif self.direction == Direction.UP:
            y -= 1

        self.head = Point(int(x), int(y))

    def draw(self, surface, x_offset, y_offset, width, height, interpolation=0.0):
        # Update particles first (logic in draw is weird but keeps it simple for visual only)
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Decrement death timer but clamp it so it doesn't go below 0
        # However, if we are "paused" in crash state, we might want to manually control this or just let it run.
        # If main loop pauses logic updates, draw is still called.
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            self.death_timer -= 1

        # Calculate block size based on drawing area
        # We want to fit w*h grid into width*height area
        block_w = width / self.w
        block_h = height / self.h
        
        # Use smaller dimension to keep aspect ratio square
        block_size = min(block_w, block_h)
        
        # Center the board
        board_w = self.w * block_size
        board_h = self.h * block_size
        start_x = x_offset + (width - board_w) / 2
        start_y = y_offset + (height - board_h) / 2
        
        # Draw Background (Checkered)
        # Fill the background area first (optional, for safety)
        full_rect = pygame.Rect(start_x, start_y, board_w, board_h)
        pygame.draw.rect(surface, BG_GREEN_DARK, full_rect) # Default dark green

        for r in range(self.h):
            for c in range(self.w):
                color = BG_GREEN_LIGHT if (r + c) % 2 == 0 else BG_GREEN_DARK
                rect = pygame.Rect(
                    start_x + c * block_size,
                    start_y + r * block_size,
                    block_size + 1, # +1 to avoid gaps due to rounding
                    block_size + 1
                )
                pygame.draw.rect(surface, color, rect)
                
        # Draw Snake with Interpolation (Rail Logic)
        snake_points = []
        
        # 1. Calculate Visual Head
        if len(self.snake) > 1:
            prev_head = self.snake[1]
            curr_head = self.snake[0]
            
            # Lerp
            vh_x = prev_head.x + (curr_head.x - prev_head.x) * interpolation
            vh_y = prev_head.y + (curr_head.y - prev_head.y) * interpolation
            
            visual_head = (vh_x, vh_y)
        else:
            visual_head = (self.snake[0].x, self.snake[0].y)
            
        snake_points.append(visual_head)
        
        # 2. Add Static Body Points
        is_growing = len(self.snake) > len(self.prev_snake)
        for pt in self.snake[1:-1]:
             snake_points.append((pt.x, pt.y))
             
        # 3. Calculate Visual Tail
        if is_growing:
            snake_points.append((self.snake[-1].x, self.snake[-1].y))
        else:
            if len(self.prev_snake) > 0:
                prev_tail = self.prev_snake[-1]
                curr_tail = self.snake[-1]
                vt_x = prev_tail.x + (curr_tail.x - prev_tail.x) * interpolation
                vt_y = prev_tail.y + (curr_tail.y - prev_tail.y) * interpolation
                snake_points.append((vt_x, vt_y))
            else:
                 snake_points.append((self.snake[-1].x, self.snake[-1].y))

        # Convert to Screen Coordinates
        screen_points = []
        for pt in snake_points:
            sx = start_x + pt[0] * block_size + block_size / 2
            sy = start_y + pt[1] * block_size + block_size / 2
            screen_points.append((sx, sy))
            
        # Draw the Path
        snake_color = BLUE1 
        body_width = int(block_size * 0.9) 
        
        if len(screen_points) >= 2:
            for i in range(len(screen_points) - 1):
                p1 = screen_points[i]
                p2 = screen_points[i+1]
                pygame.draw.line(surface, snake_color, p1, p2, body_width)
                pygame.draw.circle(surface, snake_color, p1, body_width // 2)
            pygame.draw.circle(surface, snake_color, screen_points[-1], body_width // 2)
        else:
            for p in screen_points:
                 pygame.draw.circle(surface, snake_color, p, body_width // 2)

        # 3. Draw Eyes on Head
        if len(screen_points) > 1:
            head_center = screen_points[0]
            next_pt = screen_points[1] if len(screen_points) > 1 else head_center
            
            dx = next_pt[0] - head_center[0]
            dy = next_pt[1] - head_center[1]
            dist = (dx**2 + dy**2)**0.5
            
            if dist < 0.1:
                dx, dy = 1, 0 
            else:
                dx, dy = dx / dist, dy / dist
                dx = -dx
                dy = -dy
            
            px, py = -dy, dx
            
            head_radius = body_width // 2
            eye_radius = head_radius * 0.35
            pupil_radius = eye_radius * 0.5
            eye_offset_dist = head_radius * 0.4
            
            eye1_pos = (head_center[0] + px * eye_offset_dist, head_center[1] + py * eye_offset_dist)
            eye2_pos = (head_center[0] - px * eye_offset_dist, head_center[1] - py * eye_offset_dist)
            
            forward_offset = head_radius * 0.2
            eye1_pos = (eye1_pos[0] + dx * forward_offset, eye1_pos[1] + dy * forward_offset)
            eye2_pos = (eye2_pos[0] + dx * forward_offset, eye2_pos[1] + dy * forward_offset)
            
            pygame.draw.circle(surface, WHITE, eye1_pos, eye_radius)
            pygame.draw.circle(surface, WHITE, eye2_pos, eye_radius)
            
            pupil_offset = eye_radius * 0.3
            pupil1_pos = (eye1_pos[0] + dx * pupil_offset, eye1_pos[1] + dy * pupil_offset)
            pupil2_pos = (eye2_pos[0] + dx * pupil_offset, eye2_pos[1] + dy * pupil_offset)
            
            pygame.draw.circle(surface, BLACK, pupil1_pos, pupil_radius)
            pygame.draw.circle(surface, BLACK, pupil2_pos, pupil_radius)

        # Draw Apple
        pulse = (np.sin(time.time() * 5) + 1) / 2 
        pulse_scale = 0.9 + 0.1 * pulse 
        
        apple_size = block_size * pulse_scale
        center_x = start_x + self.food.x * block_size + block_size / 2
        center_y = start_y + self.food.y * block_size + block_size / 2
        
        pygame.draw.circle(surface, RED, (center_x, center_y), apple_size / 2)
        
        leaf_rect = pygame.Rect(center_x - 2, center_y - apple_size/2 - 4, 4, 6) # Simplified leaf
        pygame.draw.ellipse(surface, (50, 200, 50), leaf_rect)

        # Draw Particles
        for p in self.particles:
            screen_px = start_x + p.x * block_size
            screen_py = start_y + p.y * block_size
            
            if p.life > 0:
                alpha = int(p.life * 255)
                # Smaller particles relative to block
                s = pygame.Surface((int(p.size * block_size * 0.2), int(p.size * block_size * 0.2)), pygame.SRCALPHA) 
                pygame.draw.circle(s, (*p.color, alpha), (int(p.size * block_size * 0.1), int(p.size * block_size * 0.1)), int(p.size * block_size * 0.05))
                surface.blit(s, (screen_px, screen_py))

        # Death Overlay
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            alpha = int((self.death_timer / 30) * 100)
            overlay.fill((255, 0, 0, alpha))
            surface.blit(overlay, (x_offset, y_offset))
            
            font = pygame.font.SysFont('Arial', int(block_size * 2), bold=True)
            text = font.render(f"!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(x_offset + width/2, y_offset + height/2))
            surface.blit(text, text_rect)
