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

Author: AI Assistant
Date: September 2025
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
    food, and movement directions.
    
    Attributes:
        x (int): X-coordinate in the grid
        y (int): Y-coordinate in the grid
    """
    x: int
    y: int

    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


class SnakeGame:
    """
    Main game class that handles the snake game logic and UI.
    
    This class manages the game state, handles user input, updates game logic,
    and renders the game interface using Tkinter.
    """
    
    # Color scheme using modern flat UI colors
    BG_COLOR = "#2C3E50"      # Dark blue-gray for background
    SNAKE_COLOR = "#2ECC71"    # Bright green for snake body
    SNAKE_HEAD_COLOR = "#27AE60"  # Darker green for snake head
    FOOD_COLOR = "#E74C3C"     # Red for food
    TEXT_COLOR = "#ECF0F1"     # Light gray for text
    
    # Game configuration constants
    CELL_SIZE = 20        # Size of each grid cell in pixels
    GRID_WIDTH = 30       # Number of cells horizontally (600px / 20px)
    GRID_HEIGHT = 30      # Number of cells vertically (600px / 20px)
    INITIAL_SPEED = 150   # Starting game speed (milliseconds between moves)
    SPEED_INCREASE = 2    # How much faster the game gets per food eaten
    MIN_SPEED = 50        # Maximum speed cap (minimum milliseconds between moves)

    def __init__(self):
        """
        Initialize the game window and game state.
        
        Sets up the Tkinter window, initializes game variables, creates the UI,
        binds keyboard controls, and starts a new game.
        """
        # Create and configure main window
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)  # Fixed window size
        
        # Initialize game state
        self.snake: List[Point] = []
        self.direction = Point(1, 0)  # Start moving right
        self.next_direction = Point(1, 0)
        self.food: Optional[Point] = None
        self.score = 0
        self.game_speed = self.INITIAL_SPEED
        self.game_over_flag = False
        
        self.setup_ui()
        self.bind_keys()
        self.reset_game()

    def setup_ui(self):
        """
        Initialize the game's user interface.
        
        Creates and configures:
        1. Main game canvas (600x600 pixels) for rendering the game
        2. Score display label in the top-left corner
        3. Sets up the visual styling (colors, fonts, etc.)
        """
        # Create main game canvas for rendering
        self.canvas = tk.Canvas(
            self.root,
            width=self.GRID_WIDTH * self.CELL_SIZE,    # 600px (30 * 20)
            height=self.GRID_HEIGHT * self.CELL_SIZE,  # 600px (30 * 20)
            bg=self.BG_COLOR,
            highlightthickness=0  # Remove border
        )
        self.canvas.pack()

        # Create score display with modern styling
        self.score_var = tk.StringVar(value="Score: 0")
        self.score_label = tk.Label(
            self.root,
            textvariable=self.score_var,  # Dynamic score updates
            fg=self.TEXT_COLOR,
            bg=self.BG_COLOR,
            font=("TkDefaultFont", 16)    # Large, readable font
        )
        self.score_label.place(x=10, y=10)  # Position in top-left corner

    def bind_keys(self):
        """
        Set up keyboard controls for the game.
        
        Binds the following controls:
        - Arrow keys: Change snake direction
        - WASD keys: Alternative direction controls
        - R key: Restart game (both uppercase and lowercase)
        
        Note: The game prevents 180-degree turns to avoid instant game over.
        """
        # Define movement controls (both arrow keys and WASD)
        key_bindings = {
            "Left": (-1, 0),  # Move left
            "Right": (1, 0),  # Move right
            "Up": (0, -1),    # Move up
            "Down": (0, 1),   # Move down
            "a": (-1, 0),     # Alternative left
            "d": (1, 0),      # Alternative right
            "w": (0, -1),     # Alternative up
            "s": (0, 1)       # Alternative down
        }
        
        # Bind all movement keys to the direction change handler
        for key, (dx, dy) in key_bindings.items():
            self.root.bind(f"<{key}>", 
                         lambda e, dx=dx, dy=dy: self.on_keypress(dx, dy))
            
        # Bind restart key (both cases)
        self.root.bind("<r>", lambda e: self.reset_game())
        self.root.bind("<R>", lambda e: self.reset_game())

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
        
        Returns:
            Set[Point]: Set of all points containing snake segments
        
        Used for collision detection and food spawning.
        """
        return set(self.snake)

    def spawn_food(self):
        """
        Spawn new food in a random empty cell.
        
        Algorithm:
        1. Get set of cells occupied by snake
        2. Generate random coordinates
        3. If cell is occupied, try again
        4. Place food when empty cell is found
        """
        occupied = self.get_occupied_cells()
        
        while True:
            # Generate random coordinates within grid bounds
            food = Point(
                randint(0, self.GRID_WIDTH - 1),
                randint(0, self.GRID_HEIGHT - 1)
            )
            # Place food if cell is empty
            if food not in occupied:
                self.food = food
                break

    def move_snake(self) -> bool:
        """
        Move snake one step in current direction.
        
        Game Logic:
        1. Update direction (if valid - no 180° turns)
        2. Calculate new head position
        3. Check for collisions
        4. Move snake (grow if food eaten)
        5. Update game state (score, speed)
        
        Returns:
            bool: False if game over (collision), True otherwise
        """
        # Update direction (no 180° turns allowed)
        if (self.next_direction.x != -self.direction.x or 
            self.next_direction.y != -self.direction.y):
            self.direction = self.next_direction

        # Calculate new head position
        head = self.snake[0]
        new_head = Point(
            (head.x + self.direction.x) % self.GRID_WIDTH,
            (head.y + self.direction.y) % self.GRID_HEIGHT
        )

        # Check for collision with self
        if new_head in self.snake:
            return False

        # Move snake
        self.snake.insert(0, new_head)
        
        # Check for food
        if new_head == self.food:
            self.score += 1
            self.score_var.set(f"Score: {self.score}")
            self.game_speed = max(
                self.MIN_SPEED,
                self.game_speed - self.SPEED_INCREASE
            )
            self.spawn_food()
        else:
            self.snake.pop()

        return True

    def draw(self):
        """
        Render the current game state to the canvas.
        
        This method handles all the game's visual elements:
        1. Clear previous frame
        2. Draw food (red circle)
        3. Draw snake (green rectangles, darker head)
        4. Draw game over screen if needed
        
        Visual hierarchy:
        - Background: Dark blue-gray
        - Snake: Green body, darker green head
        - Food: Red circle
        - Game Over: Semi-transparent overlay with centered text
        """
        # Clear previous frame
        self.canvas.delete("all")
        
        # Draw food as a circle
        if self.food:
            x1 = self.food.x * self.CELL_SIZE
            y1 = self.food.y * self.CELL_SIZE
            self.canvas.create_oval(
                x1, y1,
                x1 + self.CELL_SIZE,
                y1 + self.CELL_SIZE,
                fill=self.FOOD_COLOR,
                width=0  # No border
            )

        # Draw snake segments
        for i, point in enumerate(self.snake):
            x1 = point.x * self.CELL_SIZE
            y1 = point.y * self.CELL_SIZE
            # Different color for head (i=0) vs body
            color = self.SNAKE_HEAD_COLOR if i == 0 else self.SNAKE_COLOR
            self.canvas.create_rectangle(
                x1, y1,
                x1 + self.CELL_SIZE,
                y1 + self.CELL_SIZE,
                fill=color,
                width=0  # No border
            )

        # Draw game over overlay when needed
        if self.game_over_flag:
            # Create semi-transparent dark overlay
            self.canvas.create_rectangle(
                0, 0,
                self.GRID_WIDTH * self.CELL_SIZE,
                self.GRID_HEIGHT * self.CELL_SIZE,
                fill=self.BG_COLOR,
                stipple="gray50"  # 50% transparency pattern
            )
            
            # Display game over message and final score
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,  # Centered horizontally
                self.GRID_HEIGHT * self.CELL_SIZE // 2 - 30,  # Slightly above center
                text=f"Game Over! Score: {self.score}",
                fill=self.TEXT_COLOR,
                font=("TkDefaultFont", 24)  # Large font for main message
            )
            
            # Show restart instructions
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,  # Centered horizontally
                self.GRID_HEIGHT * self.CELL_SIZE // 2 + 30,  # Slightly below center
                text="Press R to restart",
                fill=self.TEXT_COLOR,
                font=("TkDefaultFont", 16)  # Smaller font for instructions
            )

    def game_loop(self):
        """
        Main game loop that drives the game.
        
        This method:
        1. Checks if game is still active
        2. Moves the snake
        3. Updates the display
        4. Schedules the next frame
        5. Handles game over condition
        
        The loop runs every game_speed milliseconds (starts at 150ms,
        decreases as score increases, minimum 50ms).
        """
        if not self.game_over_flag:
            if self.move_snake():  # Returns False on game over
                self.draw()  # Update display
                # Schedule next frame
                self.root.after(self.game_speed, self.game_loop)
            else:
                self.game_over()  # Handle collision

    def game_over(self):
        """
        Handle the game over state.
        
        This method:
        1. Sets the game over flag
        2. Triggers the game over screen draw
        3. Stops the game loop
        
        Player can restart by pressing R key.
        """
        self.game_over_flag = True
        self.draw()  # Draw game over screen

    def on_keypress(self, dx: int, dy: int):
        """
        Handle keyboard input for direction changes.
        
        Args:
            dx (int): Horizontal direction (-1: left, 1: right, 0: no change)
            dy (int): Vertical direction (-1: up, 1: down, 0: no change)
        
        Note: Direction change is not immediate but takes effect on next game loop
        to prevent multiple direction changes between frames.
        """
        self.next_direction = Point(dx, dy)

    def run(self):
        """
        Start the game and enter the main event loop.
        
        This method:
        1. Starts the Tkinter event loop
        2. Handles window events
        3. Runs until window is closed
        """
        self.root.mainloop()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
