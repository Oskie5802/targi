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
        self.font = pygame.font.SysFont('Arial', 18) # Increased from 14
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True) # Increased from 20
        self.small_font = pygame.font.SysFont('Arial', 14) # Increased from 10
        self.buttons = {} # key: (rect, action_string)

    def handle_click(self, pos):
        """Returns action string if a button is clicked"""
        for key, (rect, action) in self.buttons.items():
            if rect.collidepoint(pos):
                return action
        return None

    def _draw_button(self, surface, rect, text, action, is_active=False, is_hovered=False, base_color=BTN_NORMAL, active_color=BTN_ACTIVE, text_color=WHITE):
        color = active_color if is_active else base_color
        if is_hovered and not is_active:
            # Lighten the color slightly
            color = (min(color[0]+20, 255), min(color[1]+20, 255), min(color[2]+20, 255))
        
        # Shadow
        shadow_rect = rect.move(2, 2)
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=8)
        
        # Button Body
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, GRAY, rect, 1, border_radius=8)
        
        # Text
        txt_surf = self.font.render(text, True, text_color)
        txt_rect = txt_surf.get_rect(center=rect.center)
        surface.blit(txt_surf, txt_rect)
        
        self.buttons[f"btn_{action}"] = (rect, action)

    def draw_dashboard(self, surface, agent, x, y, w, h, focused_activations, mode, focused_game_idx, paused, show_help=False):
        self.buttons = {} # Reset buttons for this frame (simple immediate mode GUI)

        # Draw background for dashboard
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (25, 25, 35), rect) # Slightly bluish dark background
        pygame.draw.line(surface, GRAY, (x, y), (x, h), 2)

        # Header Section
        self._draw_stats(surface, agent, x + 20, y + 20)
        
        # UI Controls (Only Save/Help/Status now)
        self._draw_controls(surface, x + 20, y + 140, w - 40, paused)

        # Help Overlay (if active)
        if show_help:
            self._draw_help(surface, x, y, w, h)
            return # Skip drawing content if help is open

        # Content Area Start Y
        content_y = y + 200
        
        # Always draw Graphs (No Focus Mode)
        # We assume w and h are enough
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

    def _draw_controls(self, surface, x, y, w, paused):
        # Simply show status
        
        row1_y = y
        # mouse_pos = pygame.mouse.get_pos()

        # Status Label
        status_text = "PAUSED" if paused else "RUNNING"
        color = RED if paused else GREEN
        lbl = self.title_font.render(status_text, True, color)
        surface.blit(lbl, (x, row1_y))

        # Removed Buttons (Save, Help) as requested
        # help_rect = pygame.Rect(x + w - 50, row1_y, 50, 35)
        # self._draw_button(surface, help_rect, "?", "TOGGLE_HELP", False, help_rect.collidepoint(mouse_pos), base_color=(100, 100, 150))

        # save_rect = pygame.Rect(x + w - 120, row1_y, 60, 35)
        # self._draw_button(surface, save_rect, "SAVE", "SAVE_MODEL", False, save_rect.collidepoint(mouse_pos), base_color=BLUE)

    def _draw_help(self, surface, x, y, w, h):
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((20, 20, 30, 240))
        surface.blit(overlay, (x, y))
        
        # Close button
        close_rect = pygame.Rect(x + w - 40, y + 10, 30, 30)
        pygame.draw.rect(surface, RED, close_rect, border_radius=5)
        txt = self.font.render("X", True, WHITE)
        surface.blit(txt, txt.get_rect(center=close_rect.center))
        self.buttons["close_help"] = (close_rect, "TOGGLE_HELP")
        
        # Content
        lines = [
            "User Guide:",
            "",
            "Controls:",
            "- UP/DOWN: Adjust Game Speed (TPS)",
            "- SPACE: Pause / Resume",
            "- TAB: Toggle View Mode (Focus / Analytics)",
            "- 1-6: Switch Focused Agent (in Focus Mode)",
            "- S: Save Model Manually",
            "",
            "Neural Network Inputs:",
            "- D_Str/R/L: Danger Straight/Right/Left (Binary)",
            "- L/R/U/D: Moving Left/Right/Up/Down (One-hot)",
            "- F_L/R/U/D: Food is Left/Right/Up/Down (Binary)",
            "",
            "Dashboard:",
            "- Score History: Raw score per game",
            "- Mean Score: Average of last 100 games",
            "- Loss Trend: Training error (lower is better)",
        ]
        
        start_y = y + 50
        for i, line in enumerate(lines):
            color = YELLOW if i == 0 or line.endswith(":") else WHITE
            font = self.title_font if i == 0 else self.font
            txt = font.render(line, True, color)
            surface.blit(txt, (x + 30, start_y + i * 25))


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
        # Background
        pygame.draw.rect(surface, (30, 34, 40), rect, border_radius=6) # Darker modern bg
        pygame.draw.rect(surface, (60, 65, 75), rect, 1, border_radius=6) # Border

        # Title
        lbl = self.font.render(title, True, color1)
        surface.blit(lbl, (rect.x + 10, rect.y + 5))

        if not data1 or len(data1) < 2:
            return

        # Data processing
        limit = 200 # Show more history
        d1 = data1[-limit:]
        d2 = data2[-limit:] if data2 else []

        # Dynamic Scaling
        all_vals = d1 + (d2 if d2 else [])
        if not all_vals: return
        
        min_val = min(all_vals)
        max_val = max(all_vals)
        val_range = max(1, max_val - min_val)
        
        # Margins
        margin_x = 40 # Left margin for Y-axis labels
        margin_y = 30 # Bottom margin
        plot_w = rect.width - margin_x - 10
        plot_h = rect.height - margin_y - 30 # Top margin for title
        plot_x = rect.x + margin_x
        plot_y = rect.y + 30

        # Grid & Labels
        grid_lines = 5
        for i in range(grid_lines):
            # Y position (from bottom up)
            y_norm = i / (grid_lines - 1)
            y_pos = plot_y + plot_h - y_norm * plot_h
            
            # Grid line
            pygame.draw.line(surface, (45, 50, 60), (plot_x, y_pos), (plot_x + plot_w, y_pos), 1)
            
            # Label
            val = min_val + y_norm * val_range
            label_text = f"{val:.1f}" if val < 10 else f"{int(val)}"
            lbl = self.small_font.render(label_text, True, (150, 150, 160))
            lbl_rect = lbl.get_rect(right=plot_x - 5, centery=y_pos)
            surface.blit(lbl, lbl_rect)

        # Helper to map data point to screen coordinates
        def get_pt(i, val, count):
            x = plot_x + (i / max(1, count - 1)) * plot_w
            # Normalize value to 0-1 range within min-max
            norm_val = (val - min_val) / val_range
            y = plot_y + plot_h - (norm_val * plot_h)
            return (x, y)

        # Draw Data 1 (e.g. Raw Score) - Filled Area Style
        if len(d1) > 1:
            points1 = [get_pt(i, v, len(d1)) for i, v in enumerate(d1)]
            
            # Create a polygon for filling
            poly_points = points1 + [(points1[-1][0], plot_y + plot_h), (points1[0][0], plot_y + plot_h)]
            
            # Transparent fill
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            fill_color = (*color1, 40) # Low opacity
            # We need to offset polygon points because surface is blitted at rect.x, rect.y?
            # No, if surface is same size as screen (or rect), we need local coords.
            # Let's make surface size of rect
            s_poly = [(p[0]-rect.x, p[1]-rect.y) for p in poly_points]
            pygame.draw.polygon(s, fill_color, s_poly)
            surface.blit(s, (rect.x, rect.y))
            
            # Line (Anti-aliased)
            if len(points1) > 1:
                pygame.draw.aalines(surface, color1, False, points1)

        # Draw Data 2 (e.g. Mean Score) - Thicker Line
        if d2 and len(d2) > 1:
            points2 = [get_pt(i, v, len(d2)) for i, v in enumerate(d2)]
            
            # Manual thickness for AA line (draw multiple with offset)
            # Or just use normal lines for thickness
            pygame.draw.lines(surface, color2, False, points2, 3)
            
            # Legend
            leg_text = "Mean (L100)"
            leg = self.small_font.render(leg_text, True, color2)
            surface.blit(leg, (rect.right - 80, rect.y + 5))
