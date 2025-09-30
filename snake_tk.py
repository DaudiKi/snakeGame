#!/usr/bin/env python3
"""
Classic Snake Game Implementation using Tkinter

This module implements a classic Snake game where the player controls a snake
that grows by eating food while avoiding collisions with walls and itself.
The game features increasing difficulty as the snake grows longer.

Key Features:
- Smooth snake movement on a 30x30 grid
- Food spawning system
- Score tracking
- Progressive difficulty (speed increases)
  - Game over detection and restart mechanism
  - Modern color scheme with visual polish

"""

import tkinter as tk
from dataclasses import dataclass
from random import randint
from typing import List, Tuple, Optional, Set

@dataclass
class Point:
    """
    Represents a 2D point in the game grid.
    
    This class is used to track positions of the snake segments,
    food, and movement directions. It provides basic functionality
    for position comparison and hashing, which is essential for
    collision detection and set operations.
    
    Attributes:
        x (int): X-coordinate in the grid (horizontal position)
        y (int): Y-coordinate in the grid (vertical position)
    """
    x: int  # Horizontal position in the grid (0 = leftmost, increases rightward)
    y: int  # Vertical position in the grid (0 = topmost, increases downward)

    def __eq__(self, other):
        """
        Compare two points for equality.
        
        Args:
            other: Another Point object to compare with
            
        Returns:
            bool: True if points have same coordinates, False otherwise
            
        This is used for collision detection (e.g., snake hitting itself
        or eating food) and position comparison.
        """
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """
        Generate a hash value for the Point.
        
        Returns:
            int: Hash value based on x and y coordinates
            
        This allows Point objects to be used in sets and as dictionary keys,
        which is crucial for efficient collision detection using set operations.
        """
        return hash((self.x, self.y))


class SnakeGame:
    """
    Main game class that handles the snake game logic and UI.
    
    This class is responsible for:
    1. Managing the game state (snake position, food, score)
    2. Handling user input (keyboard controls)
    3. Updating game logic (movement, collisions, scoring)
    4. Rendering the game interface using Tkinter
    5. Controlling game flow (start, pause, game over)
    
    The game runs on a grid-based system where each cell can contain
    either a snake segment, food, or nothing. The snake moves continuously
    in the current direction until it hits itself or changes direction
    via user input.
    """
    
    # Color scheme using modern flat UI colors for visual appeal and clarity
    BG_COLOR = "#2C3E50"      # Dark blue-gray background - easy on the eyes
    SNAKE_COLOR = "#2ECC71"    # Bright green snake body - stands out against background
    SNAKE_HEAD_COLOR = "#27AE60"  # Darker green head - distinguishable from body
    FOOD_COLOR = "#E74C3C"     # Red food - contrasts with snake and background
    TEXT_COLOR = "#ECF0F1"     # Light gray text - readable on dark background
    
    # Game configuration constants for customizable gameplay
    CELL_SIZE = 20        # Size of each grid cell in pixels (20x20 px squares)
    GRID_WIDTH = 30       # Number of cells horizontally (600px total width)
    GRID_HEIGHT = 30      # Number of cells vertically (600px total height)
    INITIAL_SPEED = 150   # Starting speed: 150ms delay between moves
    SPEED_INCREASE = 2    # Decrease delay by 2ms per food eaten (faster)
    MIN_SPEED = 50        # Fastest possible speed: 50ms delay (speed cap)

    def __init__(self):
        """
        Initialize the game window and game state.
        
        This method performs the complete game setup:
        1. Creates and configures the main Tkinter window
        2. Initializes all game state variables
        3. Sets up the user interface
        4. Binds keyboard controls
        5. Starts a new game
        
        The game starts with:
        - Empty snake list (populated in reset_game)
        - Initial direction set to right
        - Score at 0
        - Default game speed
        - Game over flag cleared
        """
        # Create and configure main window with fixed size
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)  # Prevent window resizing for consistent gameplay
        
        # Initialize game state variables
        self.snake: List[Point] = []       # List of Points representing snake segments
        self.direction = Point(1, 0)       # Current movement direction (right)
        self.next_direction = Point(1, 0)  # Buffered next direction (prevents multiple turns per frame)
        self.food: Optional[Point] = None  # Current food position (None until first spawn)
        self.score = 0                     # Player's current score
        self.game_speed = self.INITIAL_SPEED  # Current game update interval in milliseconds
        self.game_over_flag = False        # Tracks if game is in "game over" state
        
        # Complete setup by calling helper methods
        self.setup_ui()      # Create and configure UI elements
        self.bind_keys()     # Set up keyboard controls
        self.reset_game()    # Initialize game state for first play

    def setup_ui(self):
        """
        Initialize the game's user interface.
        
        Creates and configures two main UI components:
        1. Game Canvas:
           - 600x600 pixels (30x30 grid of 20px cells)
           - Dark background
           - No border for clean look
           - Used for rendering snake, food, and game over screen
        
        2. Score Display:
           - Top-left corner
           - Large, readable font
           - Dynamic updates via StringVar
           - Matches game color scheme
        
        The UI is designed for clarity and visual appeal, with
        consistent spacing and modern styling.
        """
        # Create main game canvas for rendering all game elements
        self.canvas = tk.Canvas(
            self.root,
            width=self.GRID_WIDTH * self.CELL_SIZE,    # 600px (30 * 20)
            height=self.GRID_HEIGHT * self.CELL_SIZE,  # 600px (30 * 20)
            bg=self.BG_COLOR,
            highlightthickness=0  # Remove border for clean look
        )
        self.canvas.pack()

        # Create score display with modern styling
        self.score_var = tk.StringVar(value="Score: 0")  # Dynamic score tracking
        self.score_label = tk.Label(
            self.root,
            textvariable=self.score_var,  # Updates automatically when score changes
            fg=self.TEXT_COLOR,           # Light text color for contrast
            bg=self.BG_COLOR,            # Match background for seamless look
            font=("TkDefaultFont", 16)    # Large, readable font size
        )
        self.score_label.place(x=10, y=10)  # Fixed position in top-left corner

    def bind_keys(self):
        """
        Set up keyboard controls for the game.
        
        This method configures all keyboard input handling:
        
        1. Movement Controls:
           - Arrow keys (←↑→↓): Traditional controls
           - WASD keys: Alternative for WASD players
           Each key maps to a direction vector:
           - Left/A:  (-1, 0) - Move left
           - Right/D: (1, 0)  - Move right
           - Up/W:    (0, -1) - Move up
           - Down/S:  (0, 1)  - Move down
        
        2. Game Control:
           - R key: Restart game (case insensitive)
           
        Safety Features:
        - 180° turns are prevented (can't go right when moving left)
        - Lambda functions preserve direction values
        - Multiple key presses are buffered properly
        """
        # Define movement controls with direction vectors
        key_bindings = {
            # Arrow keys for traditional snake controls
            "Left": (-1, 0),   # Move left (negative x)
            "Right": (1, 0),   # Move right (positive x)
            "Up": (0, -1),     # Move up (negative y)
            "Down": (0, 1),    # Move down (positive y)
            
            # WASD keys for alternative control scheme
            "a": (-1, 0),      # Alternative left
            "d": (1, 0),       # Alternative right
            "w": (0, -1),      # Alternative up
            "s": (0, 1)        # Alternative down
        }
        
        # Bind all movement keys to the direction change handler
        # Lambda ensures correct dx/dy values are captured for each key
        for key, (dx, dy) in key_bindings.items():
            self.root.bind(f"<{key}>", 
                         lambda e, dx=dx, dy=dy: self.on_keypress(dx, dy))
            
        # Bind restart key (both uppercase and lowercase R)
        self.root.bind("<r>", lambda e: self.reset_game())  # lowercase r
        self.root.bind("<R>", lambda e: self.reset_game())  # uppercase R

    def reset_game(self):
        """
        Reset the game to its initial state.
        
        This method:
        1. Resets snake to starting position (1/4 across screen)
        2. Resets direction, score, and speed
        3. Spawns initial food
        4. Clears and redraws the canvas
        5. Starts the game loop
        """
        # Initialize snake with single segment at starting position
        self.snake = [Point(self.GRID_WIDTH // 4, self.GRID_HEIGHT // 2)]
        
        # Reset movement direction (start moving right)
        self.direction = Point(1, 0)
        self.next_direction = Point(1, 0)
        
        # Reset game state
        self.score = 0
        self.game_speed = self.INITIAL_SPEED
        self.game_over_flag = False
        
        # Update score display to 0
        self.score_var.set(f"Score: {self.score}")
        
        # Generate first food piece
        self.spawn_food()
        
        # Clear canvas and draw initial state
        self.canvas.delete("all")
        self.draw()
        
        # Start game loop with initial speed
        self.root.after(self.game_speed, self.game_loop)

    def get_occupied_cells(self) -> Set[Point]:
        """
        Get all grid cells currently occupied by the snake.
        
        This method creates a set of all Points where the snake's body
        segments are located. Using a set provides O(1) lookup time for
        collision detection and food spawning.
        
        Returns:
            Set[Point]: Set containing all points occupied by snake segments.
                       Each point represents one body segment's position.
        
        Usage:
        - Collision detection: Check if new head position exists in set
        - Food spawning: Ensure new food doesn't overlap with snake
        - Efficient position lookup with O(1) time complexity
        """
        return set(self.snake)  # Convert list to set for O(1) lookups

    def spawn_food(self):
        """
        Spawn new food in a random empty cell.
        
        This method ensures food is placed:
        1. In a valid grid position (within bounds)
        2. Not overlapping with snake body
        3. Completely random among available cells
        
        Algorithm:
        1. Get set of cells occupied by snake (O(n) time)
        2. Generate random coordinates within grid
        3. Check if position is empty (O(1) lookup)
        4. Repeat 2-3 until valid position found
        5. Place food at chosen position
        
        Note: While this could theoretically loop forever,
        in practice it's very fast since:
        - Snake typically occupies small % of grid
        - Grid is 30x30 = 900 cells total
        - Snake length is usually < 100 cells
        """
        occupied = self.get_occupied_cells()  # Get current snake positions
        
        while True:
            # Generate random coordinates within grid bounds
            food = Point(
                randint(0, self.GRID_WIDTH - 1),   # Random x in [0, 29]
                randint(0, self.GRID_HEIGHT - 1)   # Random y in [0, 29]
            )
            # Place food if cell is empty (O(1) lookup in set)
            if food not in occupied:
                self.food = food
                break

    def move_snake(self) -> bool:
        """
        Move snake one step in current direction.
        
        This is the core game logic method that:
        1. Updates snake direction (if valid turn)
        2. Calculates new head position
        3. Handles collisions and food eating
        4. Updates score and speed
        
        Movement Rules:
        - Snake moves one cell per game tick
        - Wraps around grid edges (e.g., right edge → left edge)
        - Can't reverse direction (180° turns blocked)
        - Grows by one cell when eating food
        
        Collision Rules:
        - Game over if snake hits itself
        - Wrapping around edges is allowed
        - Food collision = growth + score increase
        
        Speed Mechanics:
        - Speed increases with each food eaten
        - Caps at MIN_SPEED (50ms) for playability
        - Each food reduces delay by SPEED_INCREASE (2ms)
        
        Returns:
            bool: True if move was successful, False if game over
        """
        # Update direction if turn is valid (no 180° turns)
        if (self.next_direction.x != -self.direction.x or 
            self.next_direction.y != -self.direction.y):
            self.direction = self.next_direction

        # Calculate new head position with grid wrapping
        head = self.snake[0]
        new_head = Point(
            (head.x + self.direction.x) % self.GRID_WIDTH,   # Wrap x coordinate
            (head.y + self.direction.y) % self.GRID_HEIGHT   # Wrap y coordinate
        )

        # Check for collision with snake body (game over condition)
        if new_head in self.snake:
            return False  # Game over - snake hit itself

        # Add new head to front of snake
        self.snake.insert(0, new_head)
        
        # Handle food collision and snake growth
        if new_head == self.food:
            # Food eaten - increase score and speed
            self.score += 1
            self.score_var.set(f"Score: {self.score}")
            # Speed up game (decrease delay, minimum 50ms)
            self.game_speed = max(
                self.MIN_SPEED,
                self.game_speed - self.SPEED_INCREASE
            )
            self.spawn_food()  # Generate new food
        else:
            self.snake.pop()  # No food - remove tail to maintain length

        return True  # Move successful

    def draw(self):
        """
        Render the current game state to the canvas.
        
        This method handles the complete rendering pipeline:
        
        Rendering Order (back to front):
        1. Clear previous frame (prevent ghosting)
        2. Draw food (red circle)
        3. Draw snake (green segments, darker head)
        4. Draw game over overlay (if needed)
        
        Visual Design:
        - Background: Dark blue-gray (#2C3E50) for reduced eye strain
        - Snake Body: Bright green (#2ECC71) for high visibility
        - Snake Head: Darker green (#27AE60) to distinguish direction
        - Food: Red circle (#E74C3C) for contrast against snake
        - Text: Light gray (#ECF0F1) for readability
        
        Performance Considerations:
        - No borders on shapes (width=0) reduces render time
        - Single canvas.delete("all") is faster than individual updates
        - Minimal overlap between elements reduces overdraw
        - Grid-based positioning eliminates sub-pixel rendering
        
        Accessibility Features:
        - High contrast color scheme
        - Clear visual hierarchy
        - Large, readable text
        - Distinct game elements
        """
        # Clear previous frame to prevent visual artifacts
        self.canvas.delete("all")
        
        # Draw food as a circle (if it exists)
        if self.food:
            # Convert grid coordinates to pixel coordinates
            x1 = self.food.x * self.CELL_SIZE  # Left edge
            y1 = self.food.y * self.CELL_SIZE  # Top edge
            self.canvas.create_oval(
                x1, y1,                        # Top-left corner
                x1 + self.CELL_SIZE,          # Right edge
                y1 + self.CELL_SIZE,          # Bottom edge
                fill=self.FOOD_COLOR,         # Bright red
                width=0                        # No border for clean look
            )

        # Draw snake segments (body + head)
        for i, point in enumerate(self.snake):
            # Convert grid coordinates to pixel coordinates
            x1 = point.x * self.CELL_SIZE     # Left edge
            y1 = point.y * self.CELL_SIZE     # Top edge
            
            # Head (i=0) gets darker color for visual distinction
            color = self.SNAKE_HEAD_COLOR if i == 0 else self.SNAKE_COLOR
            
            # Draw segment as filled rectangle
            self.canvas.create_rectangle(
                x1, y1,                        # Top-left corner
                x1 + self.CELL_SIZE,          # Right edge
                y1 + self.CELL_SIZE,          # Bottom edge
                fill=color,                    # Green (dark for head)
                width=0                        # No border for clean look
            )

        # Draw game over overlay when game has ended
        if self.game_over_flag:
            # Create semi-transparent dark overlay for contrast
            self.canvas.create_rectangle(
                0, 0,                                    # Top-left corner
                self.GRID_WIDTH * self.CELL_SIZE,       # Full width
                self.GRID_HEIGHT * self.CELL_SIZE,      # Full height
                fill=self.BG_COLOR,                     # Dark background
                stipple="gray50"                        # 50% transparency
            )
            
            # Display game over message and final score
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,  # Center horizontally
                self.GRID_HEIGHT * self.CELL_SIZE // 2 - 30,  # Above center
                text=f"Game Over! Score: {self.score}",
                fill=self.TEXT_COLOR,                   # Light gray
                font=("TkDefaultFont", 24)              # Large, bold font
            )
            
            # Show restart instructions below score
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,  # Center horizontally
                self.GRID_HEIGHT * self.CELL_SIZE // 2 + 30,  # Below center
                text="Press R to restart",
                fill=self.TEXT_COLOR,                   # Light gray
                font=("TkDefaultFont", 16)              # Smaller font
            )

    def game_loop(self):
        """
        Main game loop that drives the game.
        
        This is the heart of the game, responsible for:
        1. Game State Management:
           - Checking if game is active
           - Moving snake
           - Detecting collisions
           - Handling game over
        
        2. Rendering:
           - Updating display after each move
           - Drawing game over screen when needed
        
        3. Timing Control:
           - Runs every game_speed milliseconds
           - Speed progression: 150ms → 50ms
           - Faster updates as score increases
        
        The loop uses Tkinter's after() method for timing,
        which provides smoother animation than a while loop
        and properly integrates with the Tkinter event system.
        
        Game Speed Progression:
        - Start: 150ms between frames
        - Each food: -2ms speed increase
        - Minimum: 50ms (maximum speed cap)
        """
        if not self.game_over_flag:
            if self.move_snake():  # Try to move snake (False = collision)
                self.draw()        # Update display with new positions
                # Schedule next frame using dynamic game speed
                self.root.after(self.game_speed, self.game_loop)
            else:
                self.game_over()   # Handle collision and end game

    def game_over(self):
        """
        Handle the game over state.
        
        This method manages the end-game sequence:
        
        1. State Changes:
           - Sets game over flag to stop main loop
           - Preserves final score and snake position
           - Stops snake movement
        
        2. Visual Feedback:
           - Triggers game over screen drawing
           - Shows final score
           - Displays restart instructions
        
        3. Player Options:
           - Can restart with R key (case insensitive)
           - Can close window to quit
           - Score is preserved until restart
        
        The game over state remains until player either:
        - Restarts game with R key
        - Closes the window
        """
        self.game_over_flag = True  # Stop game loop
        self.draw()  # Show game over screen with score

    def on_keypress(self, dx: int, dy: int):
        """
        Handle keyboard input for direction changes.
        
        This method implements the game's control system:
        
        Input Handling:
        - Captures arrow keys and WASD
        - Converts key presses to direction vectors
        - Buffers next direction change
        
        Direction Vector:
        dx: Horizontal movement
            -1 = Left
             0 = No horizontal change
             1 = Right
        
        dy: Vertical movement
            -1 = Up
             0 = No vertical change
             1 = Down
        
        Safety Features:
        - Direction change isn't instant (prevents multiple turns per frame)
        - 180° turns are blocked in move_snake()
        - Invalid combinations are ignored
        
        Note: Changes take effect on next game tick for smooth,
        consistent movement and to prevent rapid direction changes
        that could cause instant game over.
        """
        self.next_direction = Point(dx, dy)  # Buffer next direction change

    def run(self):
        """
        Start the game and enter the main event loop.
        
        This method initializes the game and starts Tkinter's
        event processing loop. It handles:
        
        1. Game Initialization:
           - Window creation and setup
           - Initial game state
           - First food spawn
        
        2. Event Processing:
           - Keyboard input
           - Window events
           - Timer events (game loop)
        
        3. Game Flow:
           - Continuous updates
           - Score tracking
           - Game over detection
        
        The game runs until the window is closed. The mainloop()
        call blocks until then, handling all game events and
        updates in the background.
        """
        self.root.mainloop()  # Start Tkinter event loop


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
