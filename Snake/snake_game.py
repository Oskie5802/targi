import pygame
import random
<<<<<<< HEAD
=======
import time
>>>>>>> 828a40c (update 02-19 22:45)
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

<<<<<<< HEAD
    def __init__(self, w=640, h=480):
=======
    def __init__(self, w=17, h=17):
>>>>>>> 828a40c (update 02-19 22:45)
        self.w = w
        self.h = h
        # init display
        self.display = None # Managed externally if needed, or we just draw to a surface
        self.particles = []
        self.reset()
<<<<<<< HEAD
=======
        self.BLOCK_SIZE = 1 # Logic block size is 1 unit
>>>>>>> 828a40c (update 02-19 22:45)

    def reset(self):
        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(int(self.w/2), int(self.h/2))
        self.snake = [self.head,
<<<<<<< HEAD
                      Point(self.head.x-BLOCK_SIZE, self.head.y),
                      Point(self.head.x-(2*BLOCK_SIZE), self.head.y)]
=======
                      Point(self.head.x-1, self.head.y),
                      Point(self.head.x-2, self.head.y)]
>>>>>>> 828a40c (update 02-19 22:45)
        
        # For smooth animation
        self.prev_snake = list(self.snake)
        self.prev_head = self.head

        # Visual feedback for reset (Death)
        self.last_score = getattr(self, 'score', 0)
        self.death_timer = 30 if self.last_score > 0 else 0

        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0
        self.particles = [] # Clear particles on reset

    def _place_food(self):
<<<<<<< HEAD
        x = random.randint(0, (self.w-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
=======
        x = random.randint(0, self.w-1)
        y = random.randint(0, self.h-1)
>>>>>>> 828a40c (update 02-19 22:45)
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
<<<<<<< HEAD
        if self.is_collision() or self.frame_iteration > 50*len(self.snake):
=======
        if self.is_collision() or self.frame_iteration > 100*len(self.snake): # Increased timeout for larger grid relative to snake size
>>>>>>> 828a40c (update 02-19 22:45)
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # 4. place new food or just move
        if self.head == self.food:
            self.score += 1
            reward = 10
<<<<<<< HEAD
            # Add particles
            for _ in range(10):
                self.particles.append(Particle(self.head.x + BLOCK_SIZE/2, self.head.y + BLOCK_SIZE/2, RED))
=======
            # Add particles (visual only, position doesn't matter for logic here, handled in draw)
            for _ in range(10):
                self.particles.append(Particle(self.head.x + 0.5, self.head.y + 0.5, RED))
>>>>>>> 828a40c (update 02-19 22:45)
            self._place_food()
        else:
            self.snake.pop()
            
            # REWARD SHAPING: Guide it to food to prevent looping
            # Calculate distance to food
<<<<<<< HEAD
            head = self.snake[0]
            food = self.food
=======
            # head = self.snake[0]
            # food = self.food
>>>>>>> 828a40c (update 02-19 22:45)
            # dist_current = ((head.x - food.x)**2 + (head.y - food.y)**2)**0.5
            
            # We need previous distance, but we don't store it easily without modifying state.
            # Instead, let's just punish existence slightly more to force urgency.
<<<<<<< HEAD
            reward = -0.05 # Increased penalty from -0.01 to -0.05
=======
            reward = -0.01 
>>>>>>> 828a40c (update 02-19 22:45)
        
        return reward, game_over, self.score

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head
        # hits boundary
<<<<<<< HEAD
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
=======
        if pt.x >= self.w or pt.x < 0 or pt.y >= self.h or pt.y < 0:
>>>>>>> 828a40c (update 02-19 22:45)
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
<<<<<<< HEAD
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE
=======
            x += 1
        elif self.direction == Direction.LEFT:
            x -= 1
        elif self.direction == Direction.DOWN:
            y += 1
        elif self.direction == Direction.UP:
            y -= 1
>>>>>>> 828a40c (update 02-19 22:45)

        self.head = Point(int(x), int(y))

    def draw(self, surface, x_offset, y_offset, width, height, interpolation=0.0):
        # Update particles first (logic in draw is weird but keeps it simple for visual only)
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            self.death_timer -= 1

<<<<<<< HEAD
        # Determine scaling to maintain aspect ratio (square fields)
        scale = min(width / self.w, height / self.h)
        
        # Calculate new dimensions for the game board
        game_w = self.w * scale
        game_h = self.h * scale
        
        # Center the game board within the available area
        start_x = x_offset + (width - game_w) / 2
        start_y = y_offset + (height - game_h) / 2
        
        # Use uniform scaling
        scale_x = scale
        scale_y = scale
        
        # Draw Background (Checkered)
        rows = int(self.h / BLOCK_SIZE)
        cols = int(self.w / BLOCK_SIZE)
        
        # Fill the background area first (optional, for safety)
        full_rect = pygame.Rect(start_x, start_y, game_w, game_h)
        pygame.draw.rect(surface, BG_GREEN_DARK, full_rect) # Default dark green

        for r in range(rows):
            for c in range(cols):
                color = BG_GREEN_LIGHT if (r + c) % 2 == 0 else BG_GREEN_DARK
                rect = pygame.Rect(
                    start_x + c * BLOCK_SIZE * scale_x,
                    start_y + r * BLOCK_SIZE * scale_y,
                    BLOCK_SIZE * scale_x + 1, # +1 to avoid gaps due to rounding
                    BLOCK_SIZE * scale_y + 1
                )
                pygame.draw.rect(surface, color, rect)
                
                # Add subtle inner border for "square" look
                border_color = (0, 0, 0, 20) # Transparent black
                s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(s, border_color, s.get_rect(), 1)
                surface.blit(s, rect)

        # Draw Snake with Interpolation (Rail Logic)
        # We calculate the visual head and tail positions, and connect them through static body segments.
        
        snake_points = []
        
        # 1. Calculate Visual Head
        # Head moves from snake[1] (prev_head) to snake[0] (curr_head)
        # Note: In our logic, snake[0] is the new head. snake[1] is the old head.
=======
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
>>>>>>> 828a40c (update 02-19 22:45)
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
        
<<<<<<< HEAD
        # 2. Add Static Body Points (All points between head and tail)
        # These are snake[1] to snake[-2] inclusive
        
        # We need to determine if we are growing (Tail stationary) or moving (Tail moving).
        is_growing = len(self.snake) > len(self.prev_snake)
        
        # Intermediate points: snake[1] to snake[-2]
=======
        # 2. Add Static Body Points
        is_growing = len(self.snake) > len(self.prev_snake)
>>>>>>> 828a40c (update 02-19 22:45)
        for pt in self.snake[1:-1]:
             snake_points.append((pt.x, pt.y))
             
        # 3. Calculate Visual Tail
        if is_growing:
<<<<<<< HEAD
            # Tail is stationary at the end
            snake_points.append((self.snake[-1].x, self.snake[-1].y))
        else:
            # Tail is moving from prev_snake[-1] to snake[-1]
            if len(self.prev_snake) > 0:
                prev_tail = self.prev_snake[-1]
                curr_tail = self.snake[-1]
                
                # Lerp
                vt_x = prev_tail.x + (curr_tail.x - prev_tail.x) * interpolation
                vt_y = prev_tail.y + (curr_tail.y - prev_tail.y) * interpolation
                
=======
            snake_points.append((self.snake[-1].x, self.snake[-1].y))
        else:
            if len(self.prev_snake) > 0:
                prev_tail = self.prev_snake[-1]
                curr_tail = self.snake[-1]
                vt_x = prev_tail.x + (curr_tail.x - prev_tail.x) * interpolation
                vt_y = prev_tail.y + (curr_tail.y - prev_tail.y) * interpolation
>>>>>>> 828a40c (update 02-19 22:45)
                snake_points.append((vt_x, vt_y))
            else:
                 snake_points.append((self.snake[-1].x, self.snake[-1].y))

        # Convert to Screen Coordinates
        screen_points = []
        for pt in snake_points:
<<<<<<< HEAD
            sx = start_x + pt[0] * scale_x + (BLOCK_SIZE * scale_x) / 2
            sy = start_y + pt[1] * scale_y + (BLOCK_SIZE * scale_y) / 2
            screen_points.append((sx, sy))
            
        # Draw the Path with Rounded Corners
        # Since vertices are static grid centers (mostly), we can draw thick lines with circle caps.
        # This automatically creates rounded corners!
        
        snake_color = BLUE1 
        body_width = int(BLOCK_SIZE * scale_x * 0.9) 
        
        if len(screen_points) >= 2:
            # Draw segments
            for i in range(len(screen_points) - 1):
                p1 = screen_points[i]
                p2 = screen_points[i+1]
                
                # Draw thick line
                pygame.draw.line(surface, snake_color, p1, p2, body_width)
                
                # Draw circle at p1 (joint)
                pygame.draw.circle(surface, snake_color, p1, body_width // 2)
            
            # Draw circle at last point
            pygame.draw.circle(surface, snake_color, screen_points[-1], body_width // 2)
        else:
            # Just a dot
=======
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
>>>>>>> 828a40c (update 02-19 22:45)
            for p in screen_points:
                 pygame.draw.circle(surface, snake_color, p, body_width // 2)

        # 3. Draw Eyes on Head
        if len(screen_points) > 1:
<<<<<<< HEAD
            # Recalculate head orientation based on smooth path first segment
            # This makes eyes look in the direction of the curve
=======
>>>>>>> 828a40c (update 02-19 22:45)
            head_center = screen_points[0]
            next_pt = screen_points[1] if len(screen_points) > 1 else head_center
            
            dx = next_pt[0] - head_center[0]
            dy = next_pt[1] - head_center[1]
            dist = (dx**2 + dy**2)**0.5
            
<<<<<<< HEAD
            # Default direction if too close (e.g. at start)
            if dist < 0.1:
                dx, dy = 1, 0 # Right
            else:
                dx, dy = dx / dist, dy / dist
                # We need the vector pointing OUT of the head (head is at 0, moving towards -velocity effectively in list logic)
                # Wait, snake_points[0] is head. snake_points[1] is neck.
                # So vector FROM neck TO head is the forward direction.
                dx = -dx
                dy = -dy
            
            # Calculate perpendicular vector for eyes
=======
            if dist < 0.1:
                dx, dy = 1, 0 
            else:
                dx, dy = dx / dist, dy / dist
                dx = -dx
                dy = -dy
            
>>>>>>> 828a40c (update 02-19 22:45)
            px, py = -dy, dx
            
            head_radius = body_width // 2
            eye_radius = head_radius * 0.35
            pupil_radius = eye_radius * 0.5
            eye_offset_dist = head_radius * 0.4
            
            eye1_pos = (head_center[0] + px * eye_offset_dist, head_center[1] + py * eye_offset_dist)
            eye2_pos = (head_center[0] - px * eye_offset_dist, head_center[1] - py * eye_offset_dist)
            
<<<<<<< HEAD
            # Move eyes slightly forward
=======
>>>>>>> 828a40c (update 02-19 22:45)
            forward_offset = head_radius * 0.2
            eye1_pos = (eye1_pos[0] + dx * forward_offset, eye1_pos[1] + dy * forward_offset)
            eye2_pos = (eye2_pos[0] + dx * forward_offset, eye2_pos[1] + dy * forward_offset)
            
<<<<<<< HEAD
            # Draw Eyes (White sclera)
            pygame.draw.circle(surface, WHITE, eye1_pos, eye_radius)
            pygame.draw.circle(surface, WHITE, eye2_pos, eye_radius)
            
            # Draw Pupils (Black) - look slightly forward (along dx, dy)
=======
            pygame.draw.circle(surface, WHITE, eye1_pos, eye_radius)
            pygame.draw.circle(surface, WHITE, eye2_pos, eye_radius)
            
>>>>>>> 828a40c (update 02-19 22:45)
            pupil_offset = eye_radius * 0.3
            pupil1_pos = (eye1_pos[0] + dx * pupil_offset, eye1_pos[1] + dy * pupil_offset)
            pupil2_pos = (eye2_pos[0] + dx * pupil_offset, eye2_pos[1] + dy * pupil_offset)
            
            pygame.draw.circle(surface, BLACK, pupil1_pos, pupil_radius)
            pygame.draw.circle(surface, BLACK, pupil2_pos, pupil_radius)

<<<<<<< HEAD
        # Draw Apple (More realistic)
        import time
        pulse = (np.sin(time.time() * 5) + 1) / 2 # Slower pulse
        pulse_scale = 0.9 + 0.1 * pulse # Subtle pulse
        
        apple_size = BLOCK_SIZE * scale_x * pulse_scale
        center_x = start_x + self.food.x * scale_x + (BLOCK_SIZE * scale_x) / 2
        center_y = start_y + self.food.y * scale_y + (BLOCK_SIZE * scale_y) / 2
        
        # Apple Body (Red Circle)
        pygame.draw.circle(surface, RED, (center_x, center_y), apple_size / 2)
        
        # Apple Stem/Leaf
        leaf_rect = pygame.Rect(center_x - 2*scale_x, center_y - apple_size/2 - 4*scale_x, 4*scale_x, 6*scale_x)
        pygame.draw.ellipse(surface, (50, 200, 50), leaf_rect) # Green leaf

        # Draw Particles
        for p in self.particles:
            # We need to map particle (game logic coords) to screen coords
            # Wait, particle coords are in game logic (self.w, self.h)
            # draw method expects offset
            # Let's adjust Particle.draw to take offset and scale
            
            # Since particle.x/y are in game logic units (pixels in game space)
            # We need to scale them
            screen_px = start_x + p.x * scale_x
            screen_py = start_y + p.y * scale_y
            
            if p.life > 0:
                alpha = int(p.life * 255)
                # Create a small surface for alpha drawing if needed, or just circle
                # Direct drawing with alpha is tricky in pygame without surface, but let's try
                s = pygame.Surface((int(p.size * scale_x * 4), int(p.size * scale_x * 4)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, alpha), (int(p.size * scale_x * 2), int(p.size * scale_x * 2)), int(p.size * scale_x))
                surface.blit(s, (screen_px - p.size * scale_x * 2, screen_py - p.size * scale_x * 2))
=======
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
                s = pygame.Surface((int(p.size * block_size * 0.2), int(p.size * block_size * 0.2)), pygame.SRCALPHA) # Smaller particles relative to block
                pygame.draw.circle(s, (*p.color, alpha), (int(p.size * block_size * 0.1), int(p.size * block_size * 0.1)), int(p.size * block_size * 0.05))
                surface.blit(s, (screen_px, screen_py))
>>>>>>> 828a40c (update 02-19 22:45)

        # Death Overlay
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            alpha = int((self.death_timer / 30) * 100)
            overlay.fill((255, 0, 0, alpha))
            surface.blit(overlay, (x_offset, y_offset))
            
<<<<<<< HEAD
            # Text
            font = pygame.font.SysFont('Arial', int(40 * scale_x), bold=True)
            text = font.render(f"CRASH! {self.last_score}", True, (255, 255, 255))
=======
            font = pygame.font.SysFont('Arial', int(block_size * 2), bold=True)
            text = font.render(f"!", True, (255, 255, 255))
>>>>>>> 828a40c (update 02-19 22:45)
            text_rect = text.get_rect(center=(x_offset + width/2, y_offset + height/2))
            surface.blit(text, text_rect)
