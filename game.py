import pygame
import random
import os
import sys

def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores its path in sys._MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Initialize Pygame
pygame.init()

# Window size and settings
WIDTH, HEIGHT = 800, 900  # Height accommodates the buttons
SQUARE_SIZE = WIDTH // 8
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Puzzle Game")

# Colors
LIGHT_WOOD = (220, 190, 140)  # Light wood color
DARK_WOOD = (115, 74, 18)     # Dark wood color
RED_BACKGROUND = (128, 0, 0)  # Board background
BLUE = (0, 0, 255)
GREY = (128, 128, 128)
SELECTED_COLOR = (255, 255, 0)       # Yellow for selected figure
TRAJECTORY_COLOR = (255, 255, 255)   # White color for trajectory
BUTTON_COLOR = (200, 200, 200)       # Light grey for buttons
BUTTON_HOVER_COLOR = (160, 160, 160) # Darker grey when hovered
POSSIBLE_MOVE_COLOR = (152, 251, 152)  # Pale Green for possible moves

# Figures
standard_figures = ["king", "queen", "rook", "rook", "bishop", "bishop", "knight", "knight"]
all_figures = ["king", "queen", "rook", "bishop", "knight"]  # Used for unlimited configuration

# Load images for the pieces
piece_images = {}
for piece_name in ["king", "queen", "rook", "bishop", "knight", "pawn"]:
    image_path = resource_path(f"{piece_name}.png")
    image = pygame.image.load(image_path)
    image = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
    piece_images[piece_name] = image

# Font for displaying messages and buttons
font = pygame.font.Font(None, 36)
button_font = pygame.font.Font(None, 30)
large_font = pygame.font.Font(None, 60)  # Reduced font size for large messages

# Class for the figures
class Figure:
    def __init__(self, type, initial_x, initial_y):
        self.type = type
        self.active = True
        self.trajectory = []
        self.initial_x = initial_x
        self.initial_y = initial_y

# Class for chessboard cells
class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.figure = None
        self.pawn = False

    def draw(self, selected=False):
        # Draw the cell
        rect = pygame.Rect(self.x * SQUARE_SIZE, self.y * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        color = LIGHT_WOOD if (self.x + self.y) % 2 == 0 else DARK_WOOD
        if selected:
            pygame.draw.rect(screen, SELECTED_COLOR, rect)
        else:
            pygame.draw.rect(screen, color, rect)
        # Draw a pawn
        if self.pawn:
            pawn_image = piece_images["pawn"]
            screen.blit(pawn_image, rect.topleft)
        # Draw a figure
        if self.figure:
            image = piece_images[self.figure.type]
            if not self.figure.active:
                # Dim the image if the figure is inactive
                image = image.copy()
                image.fill((100, 100, 100, 100), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(image, rect.topleft)

# Function to create a new game with existing configuration
def restart_game():
    global board, figures, move_count, selected_cell, possible_moves
    # Reset move count and selections
    move_count = 0
    selected_cell = None
    possible_moves = []
    # Reset figures and pawns on the board
    for row in board:
        for cell in row:
            cell.figure = None
            cell.pawn = False
    # Place pawns on the top row
    for x in range(8):
        board[x][0].pawn = True
    # Reset figures to initial positions
    for figure in figures:
        figure.active = True
        figure.trajectory = []
        board[figure.initial_x][figure.initial_y].figure = figure

# Function to create a new game with new standard configuration
def new_configuration():
    global board, figures, move_count, selected_cell, possible_moves
    # Create the chessboard
    board = [[Cell(x, y) for y in range(8)] for x in range(8)]
    # List to keep track of all figures
    figures = []
    # Reset move count and selections
    move_count = 0
    selected_cell = None
    possible_moves = []
    setup_pawns()
    setup_figures()

# Function to create a new game with unlimited configuration
def unlimited_configuration():
    global board, figures, move_count, selected_cell, possible_moves
    # Create the chessboard
    board = [[Cell(x, y) for y in range(8)] for x in range(8)]
    # List to keep track of all figures
    figures = []
    # Reset move count and selections
    move_count = 0
    selected_cell = None
    possible_moves = []
    setup_pawns()
    setup_unlimited_figures()

# Set up pawns on the top row (y = 0)
def setup_pawns():
    for x in range(8):
        board[x][0].pawn = True

# Set up figures on the bottom row (y = 7)
def setup_figures():
    random.shuffle(standard_figures)  # Shuffle the standard set
    for x in range(8):
        figure = Figure(standard_figures[x], x, 7)
        board[x][7].figure = figure
        figures.append(figure)

# Set up unlimited figures on the bottom row (y = 7)
def setup_unlimited_figures():
    # Randomly choose figures, could be duplicates
    unlimited_figures = [random.choice(all_figures) for _ in range(8)]
    for x in range(8):
        figure = Figure(unlimited_figures[x], x, 7)
        board[x][7].figure = figure
        figures.append(figure)
    # Ensure the game is winnable by having at least as many active figures as pawns
    active_figures = len(figures)
    pawns = sum(1 for x in range(8) if board[x][0].pawn)
    if active_figures < pawns:
        # Add more figures until the number of active figures is at least the number of pawns
        needed_figures = pawns - active_figures
        for i in range(needed_figures):
            x = random.randint(0, 7)
            while board[x][7].figure is not None:
                x = random.randint(0, 7)
            figure = Figure(random.choice(all_figures), x, 7)
            board[x][7].figure = figure
            figures.append(figure)

# Function to get all occupied cells and trajectory cells
def get_occupied_cells(exclude_cell=None):
    occupied_cells_figures = set()
    occupied_cells_pawns = set()
    trajectory_cells = set()
    for row in board:
        for cell in row:
            if cell.figure and cell != exclude_cell:
                occupied_cells_figures.add((cell.x, cell.y))
            if cell.figure and cell.figure.trajectory:
                trajectory_cells.update(cell.figure.trajectory)
            if cell.pawn:
                occupied_cells_pawns.add((cell.x, cell.y))
    return occupied_cells_figures, occupied_cells_pawns, trajectory_cells

# Function to get the trajectory between two cells
def get_trajectory(start_cell, end_cell):
    trajectory = []
    x0, y0 = start_cell.x, start_cell.y
    x1, y1 = end_cell.x, end_cell.y
    figure_type = start_cell.figure.type

    if figure_type == "knight":
        # For knight, include the L-shape path
        dx = x1 - x0
        dy = y1 - y0
        trajectory.append((x0, y0))
        if abs(dx) == 2 and abs(dy) == 1:
            mid_x = x0 + dx // 2
            trajectory.append((mid_x, y0))
        elif abs(dx) == 1 and abs(dy) == 2:
            mid_y = y0 + dy // 2
            trajectory.append((x0, mid_y))
        trajectory.append((x1, y1))
    elif figure_type in ["rook", "bishop", "queen"]:
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy))
        dx_step = (dx // steps) if steps != 0 else 0
        dy_step = (dy // steps) if steps != 0 else 0
        x, y = x0, y0
        for _ in range(steps + 1):
            trajectory.append((x, y))
            x += dx_step
            y += dy_step
    elif figure_type == "king":
        trajectory.append((x0, y0))
        trajectory.append((x1, y1))
    return trajectory

# Get possible moves for a figure
def get_possible_moves(cell):
    moves = []
    occupied_cells_figures, occupied_cells_pawns, trajectory_cells = get_occupied_cells(exclude_cell=cell)

    # Other trajectories (excluding the current figure's own trajectory)
    other_trajectories = trajectory_cells.copy()
    if cell.figure.trajectory:
        other_trajectories.difference_update(cell.figure.trajectory)

    figure_type = cell.figure.type

    # For different figure types
    if figure_type == "knight":
        knight_moves = [
            (-2, -1), (-1, -2), (1, -2), (2, -1),
            (2, 1), (1, 2), (-1, 2), (-2, 1)
        ]
        for dx, dy in knight_moves:
            x, y = cell.x + dx, cell.y + dy
            if 0 <= x < 8 and 0 <= y < 8:
                if ((x, y) not in occupied_cells_figures and
                    (x, y) not in other_trajectories and
                    (x, y) not in cell.figure.trajectory):  # Exclude own trajectory
                    moves.append((x, y))
    elif figure_type == "king":
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 1), (1, 0), (-1, 0), (0, -1)]:
            x, y = cell.x + dx, cell.y + dy
            if 0 <= x < 8 and 0 <= y < 8:
                if ((x, y) not in occupied_cells_figures and
                    (x, y) not in other_trajectories and
                    (x, y) not in cell.figure.trajectory):  # Exclude own trajectory
                    moves.append((x, y))
    elif figure_type in ["rook", "bishop", "queen"]:
        directions = []
        if figure_type == "rook":
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif figure_type == "bishop":
            directions = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        elif figure_type == "queen":
            directions = [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 1), (1, 0), (-1, 0), (0, -1)]
        for dx, dy in directions:
            for step in range(1, 8):
                x = cell.x + dx * step
                y = cell.y + dy * step
                if 0 <= x < 8 and 0 <= y < 8:
                    if (x, y) in occupied_cells_figures:
                        break  # Can't move past another figure
                    if (x, y) in cell.figure.trajectory:
                        break  # Can't land on or move past own trajectory
                    # Can fly over other trajectories but cannot land on them
                    if (x, y) in other_trajectories:
                        continue
                    moves.append((x, y))
                else:
                    break
    return moves

# Check if all pawns are destroyed
def all_pawns_destroyed():
    for row in board:
        for cell in row:
            if cell.pawn:
                return False
    return True

# Check if any moves are possible
def any_possible_moves():
    for row in board:
        for cell in row:
            if cell.figure and cell.figure.active:
                possible_moves = get_possible_moves(cell)
                if possible_moves:
                    return True
    return False

# Function to display a message on the screen
def display_message(message):
    # Semi-transparent overlay
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Split the message into lines if necessary
    message_lines = message.split('\n')
    for i, line in enumerate(message_lines):
        text_surface = large_font.render(line, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30 + i * 40))
        screen.blit(text_surface, text_rect)

    # Render the instruction to restart or quit
    instruction_surface = font.render("Press 'R' to Restart or 'Q' to Quit", True, (255, 255, 255))
    instruction_rect = instruction_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    screen.blit(instruction_surface, instruction_rect)

    pygame.display.flip()

    # Wait for the user to restart or quit
    waiting = True
    clock = pygame.time.Clock()
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game()
                    waiting = False
                    return  # Exit the function to continue the game loop
                elif event.key == pygame.K_q:
                    waiting = False
                    pygame.quit()
                    sys.exit()
        clock.tick(60)

# Draw the buttons and steps counter
def draw_ui():
    mouse_pos = pygame.mouse.get_pos()

    # Button dimensions
    button_width = 150
    button_height = 30
    button_spacing = 10
    start_x = 10
    y_position = HEIGHT - 50

    # Define button rects
    restart_rect = pygame.Rect(start_x, y_position, button_width, button_height)
    new_config_rect = pygame.Rect(start_x + button_width + button_spacing, y_position, button_width, button_height)
    unlimited_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), y_position, button_width + 20, button_height)

    # Draw the restart button
    if restart_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR, restart_rect)
    else:
        pygame.draw.rect(screen, BUTTON_COLOR, restart_rect)
    restart_text = button_font.render("Restart", True, (0, 0, 0))
    restart_text_rect = restart_text.get_rect(center=restart_rect.center)
    screen.blit(restart_text, restart_text_rect)

    # Draw the new config button
    if new_config_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR, new_config_rect)
    else:
        pygame.draw.rect(screen, BUTTON_COLOR, new_config_rect)
    new_config_text = button_font.render("New Config", True, (0, 0, 0))
    new_config_text_rect = new_config_text.get_rect(center=new_config_rect.center)
    screen.blit(new_config_text, new_config_text_rect)

    # Draw the unlimited config button
    if unlimited_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR, unlimited_rect)
    else:
        pygame.draw.rect(screen, BUTTON_COLOR, unlimited_rect)
    unlimited_text = button_font.render("Unlimited Config", True, (0, 0, 0))
    unlimited_text_rect = unlimited_text.get_rect(center=unlimited_rect.center)
    screen.blit(unlimited_text, unlimited_text_rect)

    # Draw the steps counter
    steps_text = font.render(f"Steps: {move_count}", True, (255, 255, 255))
    steps_text_rect = steps_text.get_rect(topright=(WIDTH - 10, y_position))
    screen.blit(steps_text, steps_text_rect)

# Initialize the game
new_configuration()

# Main game loop
running = True
selected_cell = None
possible_moves = []
move_count = 0

while running:
    screen.fill(RED_BACKGROUND)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x_mouse, y_mouse = pygame.mouse.get_pos()
            x = x_mouse // SQUARE_SIZE
            y = y_mouse // SQUARE_SIZE

            # Button dimensions
            button_width = 150
            button_height = 30
            button_spacing = 10
            start_x = 10
            y_position = HEIGHT - 50

            # Define button rects
            restart_rect = pygame.Rect(start_x, y_position, button_width, button_height)
            new_config_rect = pygame.Rect(start_x + button_width + button_spacing, y_position, button_width, button_height)
            unlimited_rect = pygame.Rect(start_x + 2 * (button_width + button_spacing), y_position, button_width + 20, button_height)

            # Check if the buttons were clicked
            if restart_rect.collidepoint(x_mouse, y_mouse):
                restart_game()
                continue
            elif new_config_rect.collidepoint(x_mouse, y_mouse):
                new_configuration()
                continue
            elif unlimited_rect.collidepoint(x_mouse, y_mouse):
                unlimited_configuration()
                continue

            if y >= 8:
                continue  # Clicked below the board

            if selected_cell:
                # Check for valid moves
                if (x, y) in possible_moves:
                    target_cell = board[x][y]

                    # Record trajectory
                    trajectory = get_trajectory(selected_cell, target_cell)
                    # Update the figure's trajectory
                    selected_cell.figure.trajectory.extend(trajectory[1:])  # Exclude starting cell to avoid duplicates

                    # Move the figure to the new cell
                    target_cell.figure = selected_cell.figure
                    selected_cell.figure = None

                    # If captures a pawn, set figure to inactive
                    if target_cell.pawn:
                        target_cell.pawn = False
                        target_cell.figure.active = False

                    selected_cell = None
                    possible_moves = []

                    # Increment move count
                    move_count += 1

                    # Check for game over conditions
                    if all_pawns_destroyed():
                        display_message(f"You won in {move_count} steps!")
                    elif not any_possible_moves():
                        display_message("No more possible moves.\nYou lost.")
                else:
                    selected_cell = None
                    possible_moves = []
            elif 0 <= x < 8 and 0 <= y < 8:
                if board[x][y].figure and board[x][y].figure.active:
                    selected_cell = board[x][y]
                    possible_moves = get_possible_moves(selected_cell)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                restart_game()

    # Draw the chessboard
    for row in board:
        for cell in row:
            is_selected = selected_cell == cell
            cell.draw(selected=is_selected)

    # Draw trajectories for all figures
    for figure in figures:
        if figure.trajectory:
            for i in range(len(figure.trajectory) - 1):
                start_coord = figure.trajectory[i]
                end_coord = figure.trajectory[i + 1]
                start_pos = (start_coord[0] * SQUARE_SIZE + SQUARE_SIZE // 2,
                             start_coord[1] * SQUARE_SIZE + SQUARE_SIZE // 2)
                end_pos = (end_coord[0] * SQUARE_SIZE + SQUARE_SIZE // 2,
                           end_coord[1] * SQUARE_SIZE + SQUARE_SIZE // 2)
                pygame.draw.line(screen, TRAJECTORY_COLOR, start_pos, end_pos, 5)

    # Highlight possible moves with the new color
    for x_move, y_move in possible_moves:
        pygame.draw.rect(screen, POSSIBLE_MOVE_COLOR,
                         (x_move * SQUARE_SIZE, y_move * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

    # Draw the UI elements (buttons and steps counter)
    draw_ui()

    pygame.display.flip()

pygame.quit()
