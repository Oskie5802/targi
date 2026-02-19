import pygame
import torch
import random
import numpy as np
from agent import Agent
from snake_game import SnakeGameAI
from visualizer import Visualizer
from network import NetworkManager
import time
import io

# Config
WINDOW_W = 1600
WINDOW_H = 900
INITIAL_FPS = 30 
SERVER_URL = "https://localhost:5001"

def main():
    global WINDOW_W, WINDOW_H
    pygame.init()
    # Enable resizing
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
    pygame.display.set_caption("Snake AI - Remote Controlled (Dashboard Only)")
    clock = pygame.time.Clock()
    fps = INITIAL_FPS
    
    # Initialize Network Manager
    print(f"Connecting to dashboard at {SERVER_URL}...")
    network = NetworkManager(url=SERVER_URL)

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
    COLS = 3
    ROWS = 2
    # Logic size for the game (fixed coordinate system)
    LOGIC_GAME_W = 17 
    LOGIC_GAME_H = 17 
    
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

    view_mode = 0 # 0: Grid, 1: Fullscreen
    dashboard_mode = 0 # 0: Default (Focused Agent), 1: Stats Only, 2: Full Grid (Future?)

    # Time Accumulator for Logic Updates
    accumulator = 0
    last_time = pygame.time.get_ticks()
    last_stream_time = 0
    
    # Game Control State
    paused = False
    show_help = False

    # Define focused_activations outside loop to avoid UnboundLocalError
    focused_activations = None

    running = True
    while running:
        # Network Sync (Receive Settings)
        settings = network.get_settings()
        if settings:
            fps = settings.get('fps', fps)
            paused = settings.get('paused', paused)
        
        # Network Sync (Receive Commands)
        commands = network.get_commands()
        for cmd in commands:
            print(f"Received command: {cmd}")
            if cmd == "RESET":
                for g in games:
                    g.reset()
                agent.n_games = 0
            elif cmd == "SAVE_MODEL":
                agent.model.save()
            elif cmd.startswith("SET_EPSILON_"):
                try:
                    agent.epsilon = int(cmd.split("_")[2])
                except: pass

            elif cmd.startswith("FOCUS_"):
                try:
                    focused_game_idx = int(cmd.split("_")[1])
                    view_mode = 1 # Switch to fullscreen on focus
                except: pass
            elif cmd == "VIEW_GRID":
                view_mode = 0

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
                network.stop()
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
                # Removed local control for FPS/Pause as requested
                # Mode Switching
                if event.key == pygame.K_1:
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
                elif event.key == pygame.K_s:
                    agent.model.save()
                    print("Model saved manually!")
            
            # Click Handling
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click
                    action = visualizer.handle_click(event.pos)
                    if action:
                        # Removed local control actions for speed/pause
                        if action.startswith("SET_MODE_"):
                            dashboard_mode = int(action.split("_")[-1])
                        elif action.startswith("FOCUS_"):
                            focused_game_idx = int(action.split("_")[-1])
                        elif action == "SAVE_MODEL":
                            agent.model.save()
        
        # Display FPS & Mode
        status_str = "PAUSED (REMOTE)" if paused else "RUNNING"
        conn_str = "ONLINE" if network.connected else "OFFLINE"
        pygame.display.set_caption(f"Snake AI - {status_str} | Speed: {fps} TPS | Focus: Game {focused_game_idx+1} | Server: {conn_str}")

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
                    try:
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
                    except Exception as e:
                        print(f"CRASH in Game {i}: {e}")
                        game.reset() # Reset only the crashed game
                        continue # Continue to next game
                
                # --- LOGIC UPDATE END ---
                
                # Network Sync (Send State) - sending only focused game
                focused_game = games[focused_game_idx]
                state_data = {
                    "score": focused_game.score,
                    "n_games": agent.n_games, # Global games count
                    "snake": [{"x": p.x, "y": p.y} for p in focused_game.snake],
                    "food": {"x": focused_game.food.x, "y": focused_game.food.y} if focused_game.food else None,
                    "fps": fps
                }
                network.update_state(state_data)

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
        
        # Draw everything
        screen.fill((0, 0, 0)) # Clear screen
        

        # Draw Left Panel (Games)
        for i, game in enumerate(games):
            row = i // COLS
            col = i % COLS
            x = col * DRAW_GAME_W
            y = row * DRAW_GAME_H
            
            # Highlight focused game
            if i == focused_game_idx:
                pygame.draw.rect(screen, (255, 255, 0), (x, y, DRAW_GAME_W, DRAW_GAME_H), 2)
            
            game.draw(screen, x, y, DRAW_GAME_W, DRAW_GAME_H, interpolation=alpha)

        # Draw Right Panel (Visualizer)
        visualizer.draw_dashboard(screen, agent, LEFT_PANEL_W, 0, RIGHT_PANEL_W, WINDOW_H, focused_activations, dashboard_mode, focused_game_idx, paused)
=======
        if view_mode == 0:
            # GRID VIEW
            # Draw Left Panel (Games)
            for i, game in enumerate(games):
                row = i // COLS
                col = i % COLS
                x = col * DRAW_GAME_W
                y = row * DRAW_GAME_H
                
                # Highlight focused game
                if i == focused_game_idx:
                    # Add gap between games for visibility
                    pygame.draw.rect(screen, (255, 255, 0), (x+2, y+2, DRAW_GAME_W-4, DRAW_GAME_H-4), 4)
                
                # Draw game with slight padding to separate them
                game.draw(screen, x+5, y+5, DRAW_GAME_W-10, DRAW_GAME_H-10, interpolation=alpha)

            # Draw Right Panel (Visualizer)
            visualizer.draw_dashboard(screen, agent, LEFT_PANEL_W, 0, RIGHT_PANEL_W, WINDOW_H, focused_activations, dashboard_mode, focused_game_idx, paused)
            
        else:
            # FULLSCREEN FOCUS VIEW
            # Draw only the focused game using full window dimensions
            # We skip the visualizer in this mode to maximize the game view
            games[focused_game_idx].draw(screen, 0, 0, WINDOW_W, WINDOW_H, interpolation=alpha)
            
            # Optional: Overlay some minimal info
            font = pygame.font.SysFont('Arial', 24)
            text = font.render(f"Agent {focused_game_idx+1} | Score: {games[focused_game_idx].score}", True, (255, 255, 255))
            screen.blit(text, (20, 20))
>>>>>>> 828a40c (update 02-19 22:45)

        # Capture and Stream Frame (Every ~33ms = 30FPS)
        if current_time - last_stream_time > 33: 
             last_stream_time = current_time
             try:
                 # Resize for dashboard? 
                 # Let's send full res but scaled down if too big to save bandwidth
                 # Target width ~800
                 target_w = 800
                 target_h = int(WINDOW_H * (800 / WINDOW_W))
                 scaled = pygame.transform.smoothscale(screen, (target_w, target_h))
                 
                 # Save to buffer
                 buf = io.BytesIO()
                 pygame.image.save(scaled, buf, "JPEG")
                 network.update_frame(buf.getvalue())
             except Exception as e:
                 print(f"Stream error: {e}")

        pygame.display.flip()
        clock.tick(120) # Limit loop speed (not game logic speed)

    pygame.quit()
    network.stop()

if __name__ == '__main__':
    main()
