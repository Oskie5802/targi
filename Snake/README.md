# Snake AI - Deep Q-Learning Demo

This is a local Python-based AI that learns to play Snake using Deep Q-Learning (DQN). It features a split-screen layout with 6 concurrent game instances and a real-time visualization of the Neural Network's "brain" and learning progress.

## Features

- **Google Snake Style**: Familiar visuals and colors.
- **Deep Q-Learning**: Uses a Linear Q-Network (Input -> Hidden -> Output).
- **Multi-Instance Training**: Runs 6 games simultaneously to speed up observation.
- **Educational Dashboard**:
  - Real-time Neural Network visualization (Input nodes, Hidden layer activations, Output decision).
  - Live graphs for Score History and Loss Trend.
  - Training statistics (Epsilon, Games count, Mean score).

## Requirements

- Python 3.8+
- Pygame
- PyTorch
- NumPy

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install pygame torch numpy
   ```

## Usage

Run the main script:

```bash
python3 main.py
```

## How it Works

- **Left Panel**: Shows 6 independent instances of the Snake game. They all share the same "Brain" (AI Agent) but play in their own environment.
- **Right Panel**:
  - **Stats**: Current training progress.
  - **Neural Net**: Visual representation of the AI's decision process.
    - **Green Nodes (Input)**: The state of the game (Walls, Food direction, Danger).
    - **Yellow/Orange Nodes (Hidden)**: The "thought" patterns (ReLU activations).
    - **Red/Grey Nodes (Output)**: The decision (Straight, Right, Left).
  - **Graphs**:
    - **Cyan**: Score history (higher is better).
    - **Red**: Loss trend (lower is generally better, but it fluctuates).

## Customization

- **Speed**: You can change `FPS` in `main.py` to make it run faster or slower.
- **Network**: You can adjust the hidden layer size in `agent.py`.
- **Reward System**: Tweak `snake_game.py` to change rewards (e.g., punishment for looping).
