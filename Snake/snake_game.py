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

    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        # init display
        self.display = None # Managed externally if needed, or we just draw to a surface
        self.particles = []
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

        # Visual feedback for reset (Death)
        self.last_score = getattr(self, 'score', 0)
        self.death_timer = 30 if self.last_score > 0 else 0

        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0
        self.particles = [] # Clear particles on reset

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
            # Add particles
            for _ in range(10):
                self.particles.append(Particle(self.head.x + BLOCK_SIZE/2, self.head.y + BLOCK_SIZE/2, RED))
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
        # Update particles first (logic in draw is weird but keeps it simple for visual only)
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.life > 0]
        
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            self.death_timer -= 1

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

        # Draw Snake with Interpolation (Continuous Body)
        # Helper for interpolation
        def lerp(p1, p2, t):
            return p1 + (p2 - p1) * t

        # 1. Collect all interpolated points for the snake body
        snake_points = []
        for i, pt in enumerate(self.snake):
            curr_x = pt.x
            curr_y = pt.y
            
            # Interpolate if we have history
            if i < len(self.prev_snake):
                prev_pt = self.prev_snake[i]
                dist = ((curr_x - prev_pt.x)**2 + (curr_y - prev_pt.y)**2)**0.5
                if dist < BLOCK_SIZE * 2: 
                    d_x = lerp(prev_pt.x, curr_x, interpolation)
                    d_y = lerp(prev_pt.y, curr_y, interpolation)
                else:
                    d_x = curr_x
                    d_y = curr_y
            else:
                d_x = curr_x
                d_y = curr_y

            # Convert to screen coordinates (center of the block)
            screen_x = start_x + d_x * scale_x + (BLOCK_SIZE * scale_x) / 2
            screen_y = start_y + d_y * scale_y + (BLOCK_SIZE * scale_y) / 2
            snake_points.append((screen_x, screen_y))

        # 2. Draw the continuous body with Rounded Corners (Spline-like)
        snake_color = BLUE1 
        body_width = int(BLOCK_SIZE * scale_x * 0.9) 
        
        # Helper to generate quadratic bezier points for a corner
        def get_corner_points(p_prev, p_curr, p_next, radius=10):
            # Vector 1: prev -> curr
            v1_x = p_curr[0] - p_prev[0]
            v1_y = p_curr[1] - p_prev[1]
            len1 = (v1_x**2 + v1_y**2)**0.5
            
            # Vector 2: curr -> next
            v2_x = p_next[0] - p_curr[0]
            v2_y = p_next[1] - p_curr[1]
            len2 = (v2_x**2 + v2_y**2)**0.5
            
            if len1 < 0.1 or len2 < 0.1: # Too short to round
                return [p_curr]
            
            # Limit radius to half the shortest segment to avoid overlap
            actual_radius = min(radius, len1/2, len2/2)
            
            # Calculate start and end of curve
            t1 = actual_radius / len1
            start_x = p_curr[0] - v1_x * t1
            start_y = p_curr[1] - v1_y * t1
            
            t2 = actual_radius / len2
            end_x = p_curr[0] + v2_x * t2
            end_y = p_curr[1] + v2_y * t2
            
            # Generate Quadratic Bezier points
            points = []
            steps = 10
            for t in [i/steps for i in range(steps+1)]:
                # B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
                bx = (1-t)**2 * start_x + 2*(1-t)*t * p_curr[0] + t**2 * end_x
                by = (1-t)**2 * start_y + 2*(1-t)*t * p_curr[1] + t**2 * end_y
                points.append((bx, by))
            
            return points

        # Generate smooth path
        smooth_path = []
        if len(snake_points) < 3:
            smooth_path = snake_points # Not enough points to curve
        else:
            # Add start point
            smooth_path.append(snake_points[0])
            
            for i in range(1, len(snake_points) - 1):
                p_prev = snake_points[i-1]
                p_curr = snake_points[i]
                p_next = snake_points[i+1]
                
                # Check for corner (dot product logic or just coordinates)
                # Since grid aligned, if x changes then y changes, it's a corner.
                # If straight line (dx1 != 0 and dx2 != 0, dy1=0, dy2=0), no corner.
                dx1 = p_curr[0] - p_prev[0]
                dy1 = p_curr[1] - p_prev[1]
                dx2 = p_next[0] - p_curr[0]
                dy2 = p_next[1] - p_curr[1]
                
                # Cross product to check collinearity (0 means collinear)
                cross = dx1 * dy2 - dx2 * dy1
                
                if abs(cross) < 1.0: # Collinear (straight)
                    smooth_path.append(p_curr)
                else: # Corner
                    # Generate curve points
                    curve = get_corner_points(p_prev, p_curr, p_next, radius=BLOCK_SIZE*scale_x*0.6)
                    # We replace p_curr with the curve
                    # Note: We need to connect from last point to start of curve?
                    # Yes, but since we append points sequentially, drawing lines between them covers gaps.
                    smooth_path.extend(curve)
            
            # Add end point
            smooth_path.append(snake_points[-1])

        # Draw the smooth path
        # Use many circles to create a thick smooth "tube"
        # This handles joints perfectly without artifacts
        step_draw = max(1, int(scale_x * 2)) # Optimize drawing step
        
        # Draw circles along the path
        for i in range(len(smooth_path) - 1):
            p1 = smooth_path[i]
            p2 = smooth_path[i+1]
            
            dist = ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)**0.5
            if dist == 0: continue
            
            steps = max(1, int(dist / step_draw))
            for j in range(steps + 1):
                t = j / steps
                x = p1[0] + (p2[0] - p1[0]) * t
                y = p1[1] + (p2[1] - p1[1]) * t
                pygame.draw.circle(surface, snake_color, (x, y), body_width // 2)

        # 3. Draw Eyes on Head
        if smooth_path:
            # Recalculate head orientation based on smooth path first segment
            # This makes eyes look in the direction of the curve
            head_center = smooth_path[0]
            next_pt = smooth_path[1] if len(smooth_path) > 1 else head_center
            
            dx = next_pt[0] - head_center[0]
            dy = next_pt[1] - head_center[1]
            dist = (dx**2 + dy**2)**0.5
            
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
            px, py = -dy, dx
            
            head_radius = body_width // 2
            eye_radius = head_radius * 0.35
            pupil_radius = eye_radius * 0.5
            eye_offset_dist = head_radius * 0.4
            
            eye1_pos = (head_center[0] + px * eye_offset_dist, head_center[1] + py * eye_offset_dist)
            eye2_pos = (head_center[0] - px * eye_offset_dist, head_center[1] - py * eye_offset_dist)
            
            # Move eyes slightly forward
            forward_offset = head_radius * 0.2
            eye1_pos = (eye1_pos[0] + dx * forward_offset, eye1_pos[1] + dy * forward_offset)
            eye2_pos = (eye2_pos[0] + dx * forward_offset, eye2_pos[1] + dy * forward_offset)
            
            # Draw Eyes (White sclera)
            pygame.draw.circle(surface, WHITE, eye1_pos, eye_radius)
            pygame.draw.circle(surface, WHITE, eye2_pos, eye_radius)
            
            # Draw Pupils (Black) - look slightly forward (along dx, dy)
            pupil_offset = eye_radius * 0.3
            pupil1_pos = (eye1_pos[0] + dx * pupil_offset, eye1_pos[1] + dy * pupil_offset)
            pupil2_pos = (eye2_pos[0] + dx * pupil_offset, eye2_pos[1] + dy * pupil_offset)
            
            pygame.draw.circle(surface, BLACK, pupil1_pos, pupil_radius)
            pygame.draw.circle(surface, BLACK, pupil2_pos, pupil_radius)

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

        # Death Overlay
        if hasattr(self, 'death_timer') and self.death_timer > 0:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            alpha = int((self.death_timer / 30) * 100)
            overlay.fill((255, 0, 0, alpha))
            surface.blit(overlay, (x_offset, y_offset))
            
            # Text
            font = pygame.font.SysFont('Arial', int(40 * scale_x), bold=True)
            text = font.render(f"CRASH! {self.last_score}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(x_offset + width/2, y_offset + height/2))
            surface.blit(text, text_rect)
