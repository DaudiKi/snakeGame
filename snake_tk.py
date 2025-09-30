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
from random import randint, random
from typing import List, Tuple, Optional, Set, Dict, Literal
from enum import Enum, auto

# Feature flags
FEATURES = {
    "score_tier_colors": True,
    "moving_food": True,
    "special_food": True,
    "progressive_obstacles": True,
    "bounded_grid": True,
    "speed_scales_with_eats": True
}

# Game tuning parameters
GAME_TUNING = {
    "food_move_every_n_ticks": 6,
    "special_spawn_chance": 0.22,        # 22% of spawns are special
    "rotten_ratio_within_special": 0.35, # else golden
    "min_snake_len": 1,
    "obstacle_every_n_foods": 3,         # add new obstacle after every 3 fruits
    "max_obstacles": 40,                 # cap for fairness
    "speed_base": 150,                   # starting delay in ms (kept from original)
    "speed_step_per_food": 2,            # decrease delay per fruit (kept from original)
    "speed_min": 50,                     # minimum delay (max speed) (kept from original)
    "score_tiers": [0, 5, 10, 20, 35, 50],
    "tier_colors": ["#22c55e", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444", "#eab308"]
}

# Food types
class FoodType(Enum):
    NORMAL = auto()
    GOLDEN = auto()
    ROTTEN = auto()

# Food colors
FOOD_COLORS = {
    FoodType.NORMAL: "#E74C3C",  # Original red
    FoodType.GOLDEN: "#f59e0b",  # Gold
    FoodType.ROTTEN: "#8b5cf6"   # Purple
}

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
        """Compare two points for equality."""
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """Generate a hash value for the Point."""
        return hash((self.x, self.y))
    
    def add(self, other: 'Point') -> 'Point':
        """Add two points component-wise."""
        return Point(self.x + other.x, self.y + other.y)
    
    def in_bounds(self, width: int, height: int) -> bool:
        """Check if point is within grid bounds."""
        return 0 <= self.x < width and 0 <= self.y < height

@dataclass
class Food:
    """
    Represents a food item in the game.
    
    Attributes:
        pos (Point): Position on the grid
        type (FoodType): Type of food (normal, golden, or rotten)
        is_moving (bool): Whether this food can move
    """
    pos: Point
    type: FoodType
    is_moving: bool = True
    
    @property
    def color(self) -> str:
        """Get the color for this food type."""
        return FOOD_COLORS[self.type]
    
    @property
    def score_value(self) -> int:
        """Get the score value for this food type."""
        return {
            FoodType.NORMAL: 1,
            FoodType.GOLDEN: 3,
            FoodType.ROTTEN: -1
        }[self.type]
    
    @property
    def growth_value(self) -> int:
        """Get how much the snake should grow when eating this food."""
        return self.score_value  # Same as score for simplicity


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
    a snake segment, food, obstacle, or nothing. The snake moves continuously
    until collision with wall, self, or obstacle.
    """
    
    # Color scheme using modern flat UI colors for visual appeal and clarity
    BG_COLOR = "#2C3E50"      # Dark blue-gray background - easy on the eyes
    TEXT_COLOR = "#ECF0F1"    # Light gray text - readable on dark background
    OBSTACLE_COLOR = "#475569" # Dark gray for obstacles
    
    # Game configuration constants
    CELL_SIZE = 20            # Size of each grid cell in pixels (20x20 px squares)
    GRID_WIDTH = 30           # Number of cells horizontally (600px total width)
    GRID_HEIGHT = 30          # Number of cells vertically (600px total height)
    
    # Movement vectors
    DIRECTIONS = [
        Point(1, 0),   # Right
        Point(-1, 0),  # Left
        Point(0, -1),  # Up
        Point(0, 1)    # Down
    ]

    def __init__(self):
        """
        Initialize the game window and game state.
        
        This method performs the complete game setup:
        1. Creates and configures the main Tkinter window
        2. Initializes all game state variables
        3. Sets up the user interface
        4. Binds keyboard controls
        5. Starts a new game
        """
        # Create and configure main window with fixed size
        self.root = tk.Tk()
        self.root.title("Snake Game")
        self.root.resizable(False, False)  # Prevent window resizing
        
        # Initialize game state variables
        self.snake: List[Point] = []       # List of Points representing snake segments
        self.direction = Point(1, 0)       # Current movement direction (right)
        self.next_direction = Point(1, 0)  # Buffered next direction
        self.food: Optional[Food] = None   # Current food object
        self.obstacles: Set[Point] = set() # Set of obstacle positions
        self.score = 0                     # Player's current score
        self.foods_eaten = 0              # Counter for obstacle spawning
        self.tick_count = 0               # Counter for food movement
        self.game_speed = GAME_TUNING["speed_base"]  # Current update interval
        self.game_over_flag = False       # Tracks if game is over
        
        # Complete setup
        self.setup_ui()      # Create UI elements
        self.bind_keys()     # Set up controls
        self.reset_game()    # Start new game
        
    def snake_color_for_score(self) -> str:
        """Get the snake color based on current score tier."""
        if not FEATURES["score_tier_colors"]:
            return "#2ECC71"  # Default green
            
        tiers = GAME_TUNING["score_tiers"]
        colors = GAME_TUNING["tier_colors"]
        
        # Find the highest tier below or equal to current score
        for tier, color in zip(reversed(tiers), reversed(colors)):
            if self.score >= tier:
                return color
                
        return colors[0]  # Fallback to first color
        
    def is_cell_free(self, pos: Point) -> bool:
        """Check if a cell is available (no snake, food, or obstacle)."""
        if not pos.in_bounds(self.GRID_WIDTH, self.GRID_HEIGHT):
            return False
        return (pos not in self.snake and 
                (not self.food or pos != self.food.pos) and
                pos not in self.obstacles)
                
    def bfs_reachable(self, start: Point, target: Point) -> bool:
        """Check if target is reachable from start using BFS."""
        if not FEATURES["progressive_obstacles"]:
            return True
            
        visited = {start}
        queue = [start]
        
        while queue:
            current = queue.pop(0)
            if current == target:
                return True
                
            # Try all directions
            for direction in self.DIRECTIONS:
                next_pos = current.add(direction)
                if (next_pos.in_bounds(self.GRID_WIDTH, self.GRID_HEIGHT) and
                    next_pos not in visited and
                    next_pos not in self.obstacles and
                    next_pos not in self.snake[:-1]):  # Allow reaching tail
                    visited.add(next_pos)
                    queue.append(next_pos)
                    
        return False

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
        
        Features:
        1. Random position (not on snake/obstacles)
        2. Special food types (normal, golden, rotten)
        3. Moving food capability
        """
        # Determine food type
        food_type = FoodType.NORMAL
        if FEATURES["special_food"] and random() < GAME_TUNING["special_spawn_chance"]:
            food_type = (FoodType.ROTTEN 
                        if random() < GAME_TUNING["rotten_ratio_within_special"]
                        else FoodType.GOLDEN)
        
        # Find empty position
        attempts = 200  # Prevent infinite loop
        while attempts > 0:
            pos = Point(
                randint(0, self.GRID_WIDTH - 1),
                randint(0, self.GRID_HEIGHT - 1)
            )
            if self.is_cell_free(pos):
                # Create food object
                self.food = Food(
                    pos=pos,
                    type=food_type,
                    is_moving=FEATURES["moving_food"]
                )
                return
            attempts -= 1
            
        # If we get here, the grid is too full
        self.game_over()
        
    def try_move_food(self):
        """Attempt to move food if conditions are met."""
        if (not FEATURES["moving_food"] or
            not self.food or
            not self.food.is_moving or
            self.tick_count % GAME_TUNING["food_move_every_n_ticks"] != 0):
            return
            
        # Try each direction randomly
        directions = self.DIRECTIONS.copy()
        while directions:
            # Pick and remove a random direction
            idx = randint(0, len(directions) - 1)
            direction = directions.pop(idx)
            
            # Calculate new position
            new_pos = self.food.pos.add(direction)
            if self.is_cell_free(new_pos):
                self.food.pos = new_pos
                return

    def move_snake(self) -> bool:
        """
        Move snake one step in current direction.
        
        Features:
        1. Bounded grid (no wrapping)
        2. Special food effects
        3. Obstacle collisions
        4. Progressive speed scaling
        
        Returns:
            bool: True if move successful, False if game over
        """
        # Update direction if valid (no 180° turns)
        if (self.next_direction.x != -self.direction.x or 
            self.next_direction.y != -self.direction.y):
            self.direction = self.next_direction

        # Calculate new head position
        head = self.snake[0]
        new_head = head.add(self.direction)
        
        # Check bounds if bounded grid enabled
        if FEATURES["bounded_grid"]:
            if not new_head.in_bounds(self.GRID_WIDTH, self.GRID_HEIGHT):
                return False  # Hit wall
        else:
            # Wrap around grid
            new_head = Point(
                new_head.x % self.GRID_WIDTH,
                new_head.y % self.GRID_HEIGHT
            )

        # Check collisions
        if new_head in self.snake:
            return False  # Hit self
        if new_head in self.obstacles:
            return False  # Hit obstacle

        # Add new head
        self.snake.insert(0, new_head)
        
        # Handle food collision
        if self.food and new_head == self.food.pos:
            # Apply food effects
            self.score = max(0, self.score + self.food.score_value)
            self.score_var.set(f"Score: {self.score}")
            
            # Handle growth/shrink
            growth = self.food.growth_value
            if growth < 0:
                # Shrink snake (remove extra segments)
                for _ in range(-growth):
                    if len(self.snake) > GAME_TUNING["min_snake_len"]:
                        self.snake.pop()
            
            # Speed up game if enabled
            if FEATURES["speed_scales_with_eats"]:
                self.game_speed = max(
                    GAME_TUNING["speed_min"],
                    self.game_speed - GAME_TUNING["speed_step_per_food"]
                )
            
            # Track food eaten
            self.foods_eaten += 1
            
            # Maybe spawn obstacle
            if (FEATURES["progressive_obstacles"] and
                self.foods_eaten % GAME_TUNING["obstacle_every_n_foods"] == 0):
                self.try_spawn_obstacles(1)
            
            # Spawn new food
            self.spawn_food()
        else:
            # No food - remove tail
            self.snake.pop()

        return True  # Move successful
        
    def try_spawn_obstacles(self, count: int):
        """
        Spawn creative obstacle patterns.
        
        Patterns include:
        - L-shapes
        - Small squares
        - Diagonal lines
        - Zigzag patterns
        - Single blocks
        """
        if len(self.obstacles) >= GAME_TUNING["max_obstacles"]:
            return
            
        # Choose a random pattern based on score
        patterns = [
            self._spawn_l_shape,
            self._spawn_small_square,
            self._spawn_diagonal,
            self._spawn_zigzag,
            self._spawn_single_block
        ]
        
        pattern_func = patterns[randint(0, len(patterns) - 1)]
        pattern_func()
        
    def _spawn_l_shape(self):
        """Spawn an L-shaped obstacle."""
        attempts = 10
        while attempts > 0:
            # Try to place the base point of the L
            base = Point(
                randint(1, self.GRID_WIDTH - 3),
                randint(1, self.GRID_HEIGHT - 3)
            )
            
            # Define the L shape (3 blocks)
            l_points = [
                base,
                Point(base.x + 1, base.y),
                Point(base.x, base.y + 1)
            ]
            
            # Check if all points are valid
            if all(self.is_cell_free(p) for p in l_points):
                # Verify snake can reach food
                temp_obstacles = self.obstacles.copy()
                temp_obstacles.update(l_points)
                
                if self._check_path_with_temp_obstacles(temp_obstacles):
                    self.obstacles.update(l_points)
                    return True
            
            attempts -= 1
        return False
        
    def _spawn_small_square(self):
        """Spawn a 2x2 square obstacle."""
        attempts = 10
        while attempts > 0:
            base = Point(
                randint(1, self.GRID_WIDTH - 3),
                randint(1, self.GRID_HEIGHT - 3)
            )
            
            square_points = [
                base,
                Point(base.x + 1, base.y),
                Point(base.x, base.y + 1),
                Point(base.x + 1, base.y + 1)
            ]
            
            if all(self.is_cell_free(p) for p in square_points):
                temp_obstacles = self.obstacles.copy()
                temp_obstacles.update(square_points)
                
                if self._check_path_with_temp_obstacles(temp_obstacles):
                    self.obstacles.update(square_points)
                    return True
                    
            attempts -= 1
        return False
        
    def _spawn_diagonal(self):
        """Spawn a diagonal line of obstacles."""
        attempts = 10
        while attempts > 0:
            base = Point(
                randint(1, self.GRID_WIDTH - 4),
                randint(1, self.GRID_HEIGHT - 4)
            )
            
            diagonal_points = [
                base,
                Point(base.x + 1, base.y + 1),
                Point(base.x + 2, base.y + 2)
            ]
            
            if all(self.is_cell_free(p) for p in diagonal_points):
                temp_obstacles = self.obstacles.copy()
                temp_obstacles.update(diagonal_points)
                
                if self._check_path_with_temp_obstacles(temp_obstacles):
                    self.obstacles.update(diagonal_points)
                    return True
                    
            attempts -= 1
        return False
        
    def _spawn_zigzag(self):
        """Spawn a zigzag pattern."""
        attempts = 10
        while attempts > 0:
            base = Point(
                randint(1, self.GRID_WIDTH - 4),
                randint(1, self.GRID_HEIGHT - 3)
            )
            
            zigzag_points = [
                base,
                Point(base.x + 1, base.y),
                Point(base.x + 1, base.y + 1),
                Point(base.x + 2, base.y + 1)
            ]
            
            if all(self.is_cell_free(p) for p in zigzag_points):
                temp_obstacles = self.obstacles.copy()
                temp_obstacles.update(zigzag_points)
                
                if self._check_path_with_temp_obstacles(temp_obstacles):
                    self.obstacles.update(zigzag_points)
                    return True
                    
            attempts -= 1
        return False
        
    def _spawn_single_block(self):
        """Spawn a single obstacle block."""
        attempts = 10
        while attempts > 0:
            pos = Point(
                randint(0, self.GRID_WIDTH - 1),
                randint(0, self.GRID_HEIGHT - 1)
            )
            
            if self.is_cell_free(pos):
                temp_obstacles = self.obstacles.copy()
                temp_obstacles.add(pos)
                
                if self._check_path_with_temp_obstacles(temp_obstacles):
                    self.obstacles.add(pos)
                    return True
                    
            attempts -= 1
        return False
        
    def _check_path_with_temp_obstacles(self, temp_obstacles: Set[Point]) -> bool:
        """Check if snake can reach food with temporary obstacles."""
        if not self.food:
            return True
            
        # Save current obstacles
        original_obstacles = self.obstacles
        self.obstacles = temp_obstacles
        
        # Check path
        has_path = self.bfs_reachable(self.snake[0], self.food.pos)
        
        # Restore original obstacles
        self.obstacles = original_obstacles
        
        return has_path

    def draw(self):
        """
        Render the current game state to the canvas.
        
        Features:
        1. Score-based snake coloring
        2. Special food types with distinct colors
        3. Obstacles
        4. Game over overlay
        """
        # Clear previous frame
        self.canvas.delete("all")
        
        # Draw obstacles
        for pos in self.obstacles:
            x1 = pos.x * self.CELL_SIZE
            y1 = pos.y * self.CELL_SIZE
            self.canvas.create_rectangle(
                x1, y1,
                x1 + self.CELL_SIZE,
                y1 + self.CELL_SIZE,
                fill=self.OBSTACLE_COLOR,
                width=0
            )
        
        # Draw food
        if self.food:
            x1 = self.food.pos.x * self.CELL_SIZE
            y1 = self.food.pos.y * self.CELL_SIZE
            self.canvas.create_oval(
                x1, y1,
                x1 + self.CELL_SIZE,
                y1 + self.CELL_SIZE,
                fill=self.food.color,
                width=0
            )
            
            # Optional: Draw indicator for special food
            if self.food.type == FoodType.GOLDEN:
                # Draw a small star/crown
                center_x = x1 + self.CELL_SIZE // 2
                center_y = y1 + self.CELL_SIZE // 4
                size = self.CELL_SIZE // 4
                self.canvas.create_text(
                    center_x, center_y,
                    text="★",
                    fill="#ffffff",
                    font=("TkDefaultFont", size)
                )
            elif self.food.type == FoodType.ROTTEN:
                # Draw an X
                center_x = x1 + self.CELL_SIZE // 2
                center_y = y1 + self.CELL_SIZE // 4
                size = self.CELL_SIZE // 4
                self.canvas.create_text(
                    center_x, center_y,
                    text="×",
                    fill="#ffffff",
                    font=("TkDefaultFont", size)
                )

        # Draw snake with score-based color
        snake_color = self.snake_color_for_score()
        head_color = snake_color  # Could make slightly darker if desired
        
        for i, point in enumerate(self.snake):
            x1 = point.x * self.CELL_SIZE
            y1 = point.y * self.CELL_SIZE
            color = head_color if i == 0 else snake_color
            
            self.canvas.create_rectangle(
                x1, y1,
                x1 + self.CELL_SIZE,
                y1 + self.CELL_SIZE,
                fill=color,
                width=0
            )

        # Draw game over overlay
        if self.game_over_flag:
            self.canvas.create_rectangle(
                0, 0,
                self.GRID_WIDTH * self.CELL_SIZE,
                self.GRID_HEIGHT * self.CELL_SIZE,
                fill=self.BG_COLOR,
                stipple="gray50"
            )
            
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,
                self.GRID_HEIGHT * self.CELL_SIZE // 2 - 30,
                text=f"Game Over! Score: {self.score}",
                fill=self.TEXT_COLOR,
                font=("TkDefaultFont", 24)
            )
            
            self.canvas.create_text(
                self.GRID_WIDTH * self.CELL_SIZE // 2,
                self.GRID_HEIGHT * self.CELL_SIZE // 2 + 30,
                text="Press R to restart",
                fill=self.TEXT_COLOR,
                font=("TkDefaultFont", 16)
            )

    def game_loop(self):
        """
        Main game loop that drives the game.
        
        Features:
        1. Moving food
        2. Progressive speed scaling
        3. Collision detection
        4. Score-based coloring
        """
        if not self.game_over_flag:
            # Update tick counter
            self.tick_count += 1
            
            # Try to move food
            self.try_move_food()
            
            # Move snake
            if self.move_snake():
                self.draw()
                # Schedule next frame
                self.root.after(self.game_speed, self.game_loop)
            else:
                self.game_over()

    def game_over(self):
        """Handle game over state."""
        self.game_over_flag = True
        self.draw()

    def reset_game(self):
        """Reset game to initial state."""
        # Reset snake
        self.snake = [Point(self.GRID_WIDTH // 4, self.GRID_HEIGHT // 2)]
        self.direction = Point(1, 0)
        self.next_direction = Point(1, 0)
        
        # Reset game state
        self.score = 0
        self.foods_eaten = 0
        self.tick_count = 0
        self.game_speed = GAME_TUNING["speed_base"]
        self.game_over_flag = False
        self.obstacles.clear()
        
        # Update score display
        self.score_var.set(f"Score: {self.score}")
        
        # Clear and redraw
        self.canvas.delete("all")
        self.spawn_food()
        self.draw()
        
        # Start game loop
        self.root.after(self.game_speed, self.game_loop)

    def on_keypress(self, dx: int, dy: int):
        """Handle keyboard input for direction changes."""
        self.next_direction = Point(dx, dy)

    def run(self):
        """Start the game."""
        self.root.mainloop()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()
