import pygame
import torch
import random
import numpy as np
from agent import Agent
from snake_game import SnakeGameAI
from visualizer import Visualizer

# Config
WINDOW_W = 1600
WINDOW_H = 900
INITIAL_FPS = 30 

def main():
    global WINDOW_W, WINDOW_H
    pygame.init()
    # Enable resizing
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Snake AI - Educational Demo (Use UP/DOWN to control speed)")
    clock = pygame.time.Clock()
    fps = INITIAL_FPS

    # Layout Config (Initial)
    # Use proportional layout instead of fixed pixels for better adaptability
    LEFT_PANEL_RATIO = 0.6 
    LEFT_PANEL_W = int(WINDOW_W * LEFT_PANEL_RATIO)
    RIGHT_PANEL_W = WINDOW_W - LEFT_PANEL_W
    
    # Grid for 6 games: 2 columns, 3 rows
    COLS = 2
    ROWS = 3
    # Logic size for the game (fixed coordinate system)
    LOGIC_GAME_W = 480 
    LOGIC_GAME_H = 320 
    
    # Draw size (dynamic)
    DRAW_GAME_W = LEFT_PANEL_W // COLS
    DRAW_GAME_H = WINDOW_H // ROWS

    # Initialize Components
    # We use fixed logic size so the AI learns on a consistent grid, 
    # but we will scale the drawing to whatever the window size is.
    games = [SnakeGameAI(w=LOGIC_GAME_W, h=LOGIC_GAME_H) for _ in range(COLS * ROWS)]
    agent = Agent()
    visualizer = Visualizer(RIGHT_PANEL_W, WINDOW_H)

    # Focus Mode State
    focused_game_idx = 0
    dashboard_mode = 0 # 0: Default (Focused Agent), 1: Stats Only, 2: Full Grid (Future?)

    # Time Accumulator for Logic Updates
    accumulator = 0
    last_time = pygame.time.get_ticks()
    
    # Game Control State
    paused = False

    # Define focused_activations outside loop to avoid UnboundLocalError
    focused_activations = None

    running = True
    while running:
        # Time Management
        current_time = pygame.time.get_ticks()
        dt = current_time - last_time
        last_time = current_time
        accumulator += dt

        # Calculate Step Interval based on target FPS (TPS)
        # fps variable now means "Game Steps Per Second"
        step_interval = 1000 / fps 

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # Handle resizing
                WINDOW_W, WINDOW_H = event.w, event.h
                screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
                
                # Recalculate layout
                LEFT_PANEL_W = int(WINDOW_W * LEFT_PANEL_RATIO)
                RIGHT_PANEL_W = WINDOW_W - LEFT_PANEL_W
                DRAW_GAME_W = LEFT_PANEL_W // COLS
                DRAW_GAME_H = WINDOW_H // ROWS
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    fps = min(fps + 10, 120)
                elif event.key == pygame.K_DOWN:
                    fps = max(fps - 10, 5)
                # Mode Switching
                elif event.key == pygame.K_1:
                    focused_game_idx = 0
                elif event.key == pygame.K_2:
                    focused_game_idx = 1
                elif event.key == pygame.K_3:
                    focused_game_idx = 2
                elif event.key == pygame.K_4:
                    focused_game_idx = 3
                elif event.key == pygame.K_5:
                    focused_game_idx = 4
                elif event.key == pygame.K_6:
                    focused_game_idx = 5
                elif event.key == pygame.K_TAB:
                    dashboard_mode = (dashboard_mode + 1) % 2 # Toggle modes
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_s:
                    agent.model.save()
                    print("Model saved manually!")
            
            # Click Handling
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    action = visualizer.handle_click(event.pos)
                    if action:
                        if action == "SPEED_UP":
                            fps = min(fps + 10, 120)
                        elif action == "SPEED_DOWN":
                            fps = max(fps - 10, 5)
                        elif action.startswith("SET_MODE_"):
                            dashboard_mode = int(action.split("_")[-1])
                        elif action.startswith("FOCUS_"):
                            focused_game_idx = int(action.split("_")[-1])
                        elif action == "TOGGLE_PAUSE":
                            paused = not paused
                        elif action == "SAVE_MODEL":
                            agent.model.save()
        
        # Display FPS & Mode
        status_str = "PAUSED" if paused else "RUNNING"
        pygame.display.set_caption(f"Snake AI - {status_str} | Speed: {fps} TPS | Mode: {dashboard_mode} | Focus: Game {focused_game_idx+1}")

        # Update & Train Logic
        # Run logic steps ONLY if accumulator > step_interval
        # We process as many steps as needed to catch up (or limit to 1 to avoid spiral of death)
        
        if not paused:
            steps_processed = 0
            while accumulator >= step_interval:
                accumulator -= step_interval
                steps_processed += 1
                
                # --- LOGIC UPDATE START ---
                
                # Capture focused agent's activations (only once per frame is enough usually, but strictly should be per step)
                # For visualization, we can just grab the latest.

                for i, game in enumerate(games):
                    # 1. Get State
                    state_old = agent.get_state(game)

                    # 2. Get Move
                    final_move = agent.get_action(state_old)
                    
                    # Capture activations ONLY for the focused game
                    if i == focused_game_idx:
                        focused_activations = {
                            'input': agent.model.activation_input.clone() if agent.model.activation_input is not None else None,
                            'hidden': agent.model.activation_hidden.clone() if agent.model.activation_hidden is not None else None,
                            'output': agent.model.activation_output.clone() if agent.model.activation_output is not None else None
                        }

                    # 3. Perform Move
                    reward, done, score = game.play_step(final_move)
                    
                    # 4. Train Short Memory
                    state_new = agent.get_state(game)
                    agent.train_short_memory(state_old, final_move, reward, state_new, done)
                    agent.remember(state_old, final_move, reward, state_new, done)

                    if done:
                        game.reset()
                        agent.n_games += 1
                        agent.train_long_memory()

                        # Always record score history to show progress (even 0)
                        agent.score_history.append(score)
                        mean_score = np.mean(agent.score_history[-100:])
                        agent.mean_score_history.append(mean_score)
                        
                        if score > (max(agent.score_history[:-1]) if len(agent.score_history) > 1 else 0):
                            agent.model.save()
                
                # --- LOGIC UPDATE END ---
                
                # Break if too many steps to avoid freeze (spiral of death)
                if steps_processed > 5:
                    accumulator = 0 # Discard lag
                    break
        else:
            # If paused, reset accumulator so we don't jump forward when unpaused
            accumulator = 0

        # Calculate Interpolation Alpha (0.0 to 1.0)
        # If paused, alpha should be static (1.0 or whatever)
        alpha = accumulator / step_interval if (step_interval > 0 and not paused) else 1.0
        if alpha > 1.0: alpha = 1.0
        
        screen.fill((20, 20, 20)) # Dark background

        # Draw Games
        if dashboard_mode == 0: # Focus Mode -> Draw One Big Game
            focused_game = games[focused_game_idx]
            # Draw it full size in left panel
            focused_game.draw(screen, 0, 0, LEFT_PANEL_W, WINDOW_H, interpolation=alpha)
            
            # Overlay score
            font = pygame.font.SysFont('Arial', 32, bold=True)
            score_text = font.render(f"Score: {focused_game.score}", True, (0, 0, 0)) # Black text for visibility
            screen.blit(score_text, (20, 20))
            
            # Label
            label_text = font.render(f"FOCUSED AGENT #{focused_game_idx+1}", True, (255, 215, 0))
            screen.blit(label_text, (20, WINDOW_H - 50))
            
        else: # Analytics Mode -> Draw Grid
            for i, game in enumerate(games):
                # Calculate position
                col = i % COLS
                row = i // COLS
                x_offset = col * DRAW_GAME_W
                y_offset = row * DRAW_GAME_H
                
                # Draw border
                game.draw(screen, x_offset, y_offset, DRAW_GAME_W, DRAW_GAME_H, interpolation=alpha)
                
                # Highlight focused game border
                border_color = (255, 215, 0) if i == focused_game_idx else (60, 60, 60)
                border_width = 4 if i == focused_game_idx else 2
                pygame.draw.rect(screen, border_color, (x_offset, y_offset, DRAW_GAME_W, DRAW_GAME_H), border_width)
                
                # Draw individual score
                font = pygame.font.SysFont('Arial', 18, bold=True)
                score_color = (20, 20, 20) # Dark text for visibility on light green background
                score_text = font.render(f"Score: {game.score}", True, score_color) 
                screen.blit(score_text, (x_offset + 10, y_offset + 10))
                
                # Draw label
                label_text = font.render(f"#{i+1}", True, score_color)
                screen.blit(label_text, (x_offset + DRAW_GAME_W - 30, y_offset + 10))

        # Draw Dashboard
        visualizer.draw_dashboard(screen, agent, LEFT_PANEL_W, 0, RIGHT_PANEL_W, WINDOW_H, focused_activations, dashboard_mode, focused_game_idx, paused)

        pygame.display.flip()
        
        # Limit Render FPS (e.g. 60 or 120) to avoid 100% CPU usage
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
