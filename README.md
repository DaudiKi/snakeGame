# Python Snake Game

A classic Snake game implementation using Python's Tkinter library. This modern implementation features smooth graphics, progressive difficulty, and a polished user interface.

## Features

- **Smooth Graphics**: Clean, modern visuals with a dark theme
- **Responsive Controls**: 
  - Arrow keys or WASD for movement
  - Instant direction changes (except 180° turns)
  - Press R to restart after game over
- **Progressive Difficulty**: Game speeds up as your score increases
- **Visual Polish**:
  - Distinct snake head color
  - Smooth movement on a 30x30 grid
  - Semi-transparent game over overlay
  - High-contrast color scheme for visibility
- **Score Tracking**: Live score display in top-left corner

## Requirements

- Python 3.x (tested with Python 3.8+)
- Tkinter (included in standard Python distribution)
- No external dependencies required!

## Installation

1. Ensure Python 3 is installed on your system
2. Clone or download this repository
3. No additional installation needed - the game uses only standard library components

## How to Run

```bash
# Navigate to the game directory
cd snake-game

# Run the game
python3 snake_tk.py
```

## Controls

- **Movement**:
  - Arrow Keys: ↑ ↓ ← → 
  - Alternative: WASD keys
  - Note: Can't turn 180° instantly (prevents accidental self-collision)
- **Restart**: 
  - Press R key after game over
  - Can use either uppercase or lowercase 'r'
- **Quit**: 
  - Close the window

## Game Rules

1. **Basic Gameplay**:
   - Control the snake to eat the red food pieces
   - Snake grows longer with each food eaten
   - Score increases by 1 for each food
   - Game ends if snake hits wall or itself

2. **Progressive Difficulty**:
   - Game starts at a moderate speed
   - Each food eaten makes the snake slightly faster
   - Speed caps at a challenging but manageable level

3. **Scoring System**:
   - 1 point per food eaten
   - No maximum score
   - Try to beat your high score!

## Technical Details

- Window Size: 600x600 pixels
- Grid: 30x30 cells (20px each)
- Frame Rate: Variable (starts at 150ms per frame, decreases with score)
- Minimum Frame Time: 50ms (maximum speed cap)

## Code Structure

The game is built using object-oriented programming principles:

- `Point`: Dataclass for 2D grid coordinates
- `SnakeGame`: Main game class handling:
  - Game state management
  - Input processing
  - Collision detection
  - Rendering
  - Game loop control

## Contributing

Feel free to fork this repository and make improvements! Some ideas:
- Add high score tracking
- Implement different difficulty levels
- Add sound effects
- Create power-ups or obstacles

## License

This project is open source and available for anyone to use and modify.