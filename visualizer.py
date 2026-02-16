import pygame
import torch
import numpy as np

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
RED = (235, 87, 87)
GREEN = (39, 174, 96)
BLUE = (47, 128, 237)
YELLOW = (242, 201, 76)
CYAN = (86, 204, 242)
ORANGE = (242, 153, 74)
PURPLE = (155, 81, 224)
BTN_HOVER = (60, 60, 80)
BTN_NORMAL = (50, 50, 60)
BTN_ACTIVE = (70, 70, 90)

class Visualizer:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self.font = pygame.font.SysFont('Arial', 14)
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.small_font = pygame.font.SysFont('Arial', 10)
        self.buttons = {} # key: (rect, action_string)

    def handle_click(self, pos):
        """Returns action string if a button is clicked"""
        for key, (rect, action) in self.buttons.items():
            if rect.collidepoint(pos):
                return action
        return None

    def draw_dashboard(self, surface, agent, x, y, w, h, focused_activations, mode, focused_game_idx, paused):
        self.buttons = {} # Reset buttons for this frame (simple immediate mode GUI)

        # Draw background for dashboard
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (25, 25, 35), rect) # Slightly bluish dark background
        pygame.draw.line(surface, GRAY, (x, y), (x, h), 2)

        # Header Section
        self._draw_stats(surface, agent, x + 20, y + 20)
        
        # UI Controls (Tabs & Buttons)
        self._draw_controls(surface, x + 20, y + 140, w - 40, mode, focused_game_idx, paused)

        # Content Area Start Y
        content_y = y + 230
        available_h = h - content_y - 10 # 10 px padding bottom

        # Mode 0: Default (NN + Graphs)
        if mode == 0:
            # 2. Neural Network Visualization
            # Use dynamic height, max 280, min 150
            nn_height = min(280, max(150, int(available_h * 0.45)))
            
            nn_rect = pygame.Rect(x + 10, content_y, w - 20, nn_height)
            self._draw_neural_net(surface, focused_activations, nn_rect, focused_game_idx)

            # 3. Graphs (Score & Loss)
            graph_y_start = content_y + nn_height + 10
            graph_height = h - graph_y_start - 10
            
            if graph_height > 50: # Only draw if there is space
                graph_rect = pygame.Rect(x + 10, graph_y_start, w - 20, graph_height)
                self._draw_graphs(surface, agent, graph_rect)
        
        # Mode 1: Analytics (Full Graphs)
        elif mode == 1:
             graph_rect = pygame.Rect(x + 10, content_y, w - 20, h - content_y - 20)
             self._draw_graphs(surface, agent, graph_rect)

    def _draw_stats(self, surface, agent, x, y):
        # Title
        title = self.title_font.render("AI Training Dashboard", True, YELLOW)
        surface.blit(title, (x, y))
        
        # Compact Stats
        stats = [
            f"Games: {agent.n_games}",
            f"Epsilon: {agent.epsilon}",
            f"Best: {max(agent.score_history) if agent.score_history else 0}",
            f"Mean: {agent.mean_score_history[-1] if agent.mean_score_history else 0:.2f}"
        ]
        
        # Draw in a grid 2x2
        for i, stat in enumerate(stats):
            col = i % 2
            row = i // 2
            text = self.font.render(stat, True, WHITE)
            surface.blit(text, (x + col * 200, y + 35 + row * 25))

    def _draw_controls(self, surface, x, y, w, current_mode, focused_game_idx, paused):
        # Layout: Two Rows
        # Row 1: Mode Tabs (Left) | Speed (Right)
        # Row 2: Focus Buttons (Left, if Mode 0) | Play/Pause & Save (Right)
        
        row1_y = y
        row2_y = y + 40
        
        # --- ROW 1 ---
        
        # 1. Mode Tabs (Left)
        tab_w = 120
        tab_h = 30
        modes = ["Focus View", "Analytics"]
        for i, label in enumerate(modes):
            bx = x + i * (tab_w + 10)
            rect = pygame.Rect(bx, row1_y, tab_w, tab_h)
            
            is_active = (i == current_mode)
            color = BTN_ACTIVE if is_active else BTN_NORMAL
            
            mouse_pos = pygame.mouse.get_pos()
            if rect.collidepoint(mouse_pos) and not is_active:
                color = BTN_HOVER
                
            pygame.draw.rect(surface, color, rect, border_radius=5)
            pygame.draw.rect(surface, GRAY, rect, 1, border_radius=5)
            
            text = self.font.render(label, True, WHITE if is_active else GRAY)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)
            self.buttons[f"mode_{i}"] = (rect, f"SET_MODE_{i}")

        # 3. Speed Controls (Right aligned in Row 1)
        spd_x = x + w - 100
        
        # Up
        up_rect = pygame.Rect(spd_x, row1_y, 40, 30)
        pygame.draw.rect(surface, BTN_NORMAL, up_rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, up_rect, 1, border_radius=5)
        txt = self.font.render("+", True, WHITE)
        surface.blit(txt, txt.get_rect(center=up_rect.center))
        self.buttons["speed_up"] = (up_rect, "SPEED_UP")
        
        # Down
        down_rect = pygame.Rect(spd_x + 50, row1_y, 40, 30)
        pygame.draw.rect(surface, BTN_NORMAL, down_rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, down_rect, 1, border_radius=5)
        txt = self.font.render("-", True, WHITE)
        surface.blit(txt, txt.get_rect(center=down_rect.center))
        self.buttons["speed_down"] = (down_rect, "SPEED_DOWN")
        
        lbl = self.small_font.render("Speed", True, GRAY)
        # Position label above speed controls? Or to the left?
        # Let's put it to the left to save vertical space or above if there's room.
        # Above is fine.
        surface.blit(lbl, (spd_x + 25, row1_y - 12))

        # --- ROW 2 ---

        # 2. Focus Selectors (Left aligned in Row 2) - Only show in Mode 0
        if current_mode == 0:
            lbl = self.small_font.render("Focus Game:", True, GRAY)
            surface.blit(lbl, (x, row2_y - 12))
            
            for i in range(6):
                size = 30
                bx = x + i * (size + 5)
                rect = pygame.Rect(bx, row2_y, size, size)
                
                is_focused = (i == focused_game_idx)
                color = (255, 215, 0) if is_focused else BTN_NORMAL 
                
                mouse_pos = pygame.mouse.get_pos()
                if rect.collidepoint(mouse_pos) and not is_focused:
                    color = BTN_HOVER
                    
                pygame.draw.rect(surface, color, rect, border_radius=5)
                pygame.draw.rect(surface, GRAY, rect, 1, border_radius=5)
                
                text_color = BLACK if is_focused else WHITE
                text = self.font.render(str(i+1), True, text_color)
                text_rect = text.get_rect(center=rect.center)
                surface.blit(text, text_rect)
                self.buttons[f"focus_{i}"] = (rect, f"FOCUS_{i}")

        # 4. Play/Pause & Save (Right aligned in Row 2)
        ctrl_x = x + w - 140 # Adjust based on button widths
        
        # Pause Button
        pause_rect = pygame.Rect(ctrl_x, row2_y, 60, 30)
        color = RED if paused else GREEN
        pygame.draw.rect(surface, color, pause_rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, pause_rect, 1, border_radius=5)
        
        label = "RESUME" if paused else "PAUSE"
        txt = self.small_font.render(label, True, WHITE)
        surface.blit(txt, txt.get_rect(center=pause_rect.center))
        self.buttons["pause"] = (pause_rect, "TOGGLE_PAUSE")
        
        # Save Button
        save_rect = pygame.Rect(ctrl_x + 70, row2_y, 60, 30)
        pygame.draw.rect(surface, BLUE, save_rect, border_radius=5)
        pygame.draw.rect(surface, GRAY, save_rect, 1, border_radius=5)
        txt = self.small_font.render("SAVE", True, WHITE)
        surface.blit(txt, txt.get_rect(center=save_rect.center))
        self.buttons["save"] = (save_rect, "SAVE_MODEL")


    def _draw_neural_net(self, surface, activations, rect, focused_game_idx):
        # Draw container background
        bg_rect = rect.inflate(-10, -10)
        pygame.draw.rect(surface, (30, 30, 40), bg_rect, border_radius=10)
        pygame.draw.rect(surface, (50, 50, 60), bg_rect, 1, border_radius=10)
        
        # Label
        lbl = self.font.render(f"Neural Network State (Game #{focused_game_idx+1})", True, CYAN)
        surface.blit(lbl, (rect.x + 15, rect.y + 15))

        if activations is None:
            lbl = self.font.render("Waiting for data...", True, GRAY)
            surface.blit(lbl, (rect.centerx - 50, rect.centery))
            return

        # Get activations (handle if None)
        inputs = activations['input']
        hidden = activations['hidden']
        outputs = activations['output']
        
        if inputs is None: return

        # Layout
        layer_x = [rect.x + 50, rect.centerx, rect.right - 50]
        
        # Nodes counts
        n_in = 11
        n_hidden = 16 
        n_out = 3
        
        # Calculate Y positions
        content_rect = bg_rect.inflate(0, -40) # Add padding top/bottom
        content_rect.move_ip(0, 20)
        
        def get_y(count, index, height, offset_y):
            spacing = height / (count + 1)
            return offset_y + spacing * (index + 1)

        # Draw Inputs
        input_pos = []
        for i in range(n_in):
            pos = (layer_x[0], get_y(n_in, i, content_rect.height, content_rect.y))
            input_pos.append(pos)
            
            val = inputs[0][i] if len(inputs.shape) > 1 else inputs[i]
            # Input is binary (mostly), so simpler color logic
            color = GREEN if val > 0.5 else (60, 60, 60)
            
            # Draw connection lines to hidden first (so they are behind nodes)
            # Calculated later or in a separate pass? 
            # Let's collect positions first then draw lines, then nodes.
            
        # Draw Hidden
        hidden_pos = []
        h_vals = hidden[0] if len(hidden.shape) > 1 else hidden
        for i in range(min(n_hidden, len(h_vals))):
            pos = (layer_x[1], get_y(n_hidden, i, content_rect.height, content_rect.y))
            hidden_pos.append(pos)

        # Draw Output
        output_pos = []
        o_vals = outputs[0] if len(outputs.shape) > 1 else outputs
        for i in range(n_out):
            pos = (layer_x[2], get_y(n_out, i, content_rect.height, content_rect.y))
            output_pos.append(pos)

        # Draw Connections
        # Input -> Hidden
        for i, start in enumerate(input_pos):
            val_in = inputs[0][i] if len(inputs.shape) > 1 else inputs[i]
            if val_in > 0.5: # Only draw active connections clearly
                for end in hidden_pos:
                    pygame.draw.line(surface, (50, 100, 50), start, end, 1)

        # Hidden -> Output
        for i, start in enumerate(hidden_pos):
            val_h = h_vals[i]
            if val_h > 0: # ReLU activation check
                for end in output_pos:
                    intensity = min(150, int(val_h * 50)) + 50
                    pygame.draw.line(surface, (intensity, intensity, 0), start, end, 1)

        # Draw Nodes (on top of lines)
        # Input Nodes
        input_labels = ["D_Str", "D_R", "D_L", "L", "R", "U", "D", "F_L", "F_R", "F_U", "F_D"]
        for i, pos in enumerate(input_pos):
            val = inputs[0][i] if len(inputs.shape) > 1 else inputs[i]
            color = GREEN if val > 0.5 else (60, 60, 60)
            pygame.draw.circle(surface, color, pos, 6)
            pygame.draw.circle(surface, WHITE, pos, 6, 1) # border
            
            # Text Label
            lbl = self.small_font.render(input_labels[i], True, GRAY)
            surface.blit(lbl, (pos[0]-35, pos[1]-5))

        # Hidden Nodes
        for i, pos in enumerate(hidden_pos):
            val = h_vals[i]
            intensity = min(255, max(40, int(val * 100)))
            color = (intensity, intensity, 0) # Yellowish
            pygame.draw.circle(surface, color, pos, 6)
            pygame.draw.circle(surface, WHITE, pos, 6, 1)

        # Output Nodes
        output_labels = ["Straight", "Right", "Left"]
        best_action = torch.argmax(o_vals).item()
        for i, pos in enumerate(output_pos):
            val = o_vals[i]
            is_best = (i == best_action)
            color = RED if is_best else (60, 60, 60)
            
            # Glow effect for active output
            if is_best:
                pygame.draw.circle(surface, (200, 50, 50, 100), pos, 12) 
            
            pygame.draw.circle(surface, color, pos, 8)
            pygame.draw.circle(surface, WHITE, pos, 8, 1)
            
            lbl = self.font.render(output_labels[i], True, WHITE if is_best else GRAY)
            surface.blit(lbl, (pos[0]+15, pos[1]-7))

    def _draw_graphs(self, surface, agent, rect):
        # Background for graphs
        pygame.draw.rect(surface, (30, 30, 40), rect, border_radius=10)
        pygame.draw.rect(surface, (50, 50, 60), rect, 1, border_radius=10)

        # Split area: Top for Score, Bottom for Loss
        h_half = (rect.height - 40) / 2 # 40 for padding/labels
        
        score_rect = pygame.Rect(rect.x + 10, rect.y + 30, rect.width - 20, h_half)
        loss_rect = pygame.Rect(rect.x + 10, rect.y + 30 + h_half + 20, rect.width - 20, h_half)

        # 1. Score Graph
        self._draw_single_chart(surface, score_rect, agent.score_history, agent.mean_score_history, "Score History", CYAN, ORANGE)

        # 2. Loss Graph
        # We only pass one history list for loss
        self._draw_single_chart(surface, loss_rect, agent.loss_history, None, "Loss Trend", PURPLE, None)


    def _draw_single_chart(self, surface, rect, data1, data2, title, color1, color2):
        # Draw Title
        lbl = self.font.render(title, True, color1)
        surface.blit(lbl, (rect.x, rect.y - 20))

        # Draw Box
        pygame.draw.rect(surface, (20, 20, 25), rect)
        pygame.draw.rect(surface, (60, 60, 70), rect, 1)

        if not data1 or len(data1) < 2:
            return

        # Limit data to last 100 points for cleaner view
        limit = 100
        d1 = data1[-limit:]
        d2 = data2[-limit:] if data2 else []

        max_val = max(max(d1), max(d2) if d2 else 0)
        if max_val == 0: max_val = 1
        
        # Helper to map value to y
        def get_pt(i, val, data_len):
            x = rect.x + (i / (data_len - 1)) * rect.width
            # 10% padding top and bottom
            h = rect.height * 0.8
            y_base = rect.bottom - rect.height * 0.1
            y = y_base - (val / max_val) * h
            return (x, y)

        # Draw Data 1 (e.g. Raw Score)
        points1 = [get_pt(i, v, len(d1)) for i, v in enumerate(d1)]
        if len(points1) > 1:
            pygame.draw.lines(surface, color1, False, points1, 2)

        # Draw Data 2 (e.g. Mean Score)
        if d2 and len(d2) > 1:
            points2 = [get_pt(i, v, len(d2)) for i, v in enumerate(d2)]
            pygame.draw.lines(surface, color2, False, points2, 3) # Thicker line
            
            # Legend for Mean Score
            if color2 == ORANGE:
                leg = self.small_font.render("Mean Score", True, ORANGE)
                surface.blit(leg, (rect.right - 60, rect.y + 5))

        # Draw Grid lines (Horizontal)
        for i in range(5):
            y = rect.bottom - (i / 4) * rect.height
            pygame.draw.line(surface, (40, 40, 50), (rect.x, y), (rect.right, y), 1)
