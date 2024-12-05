import random
import sys
import os
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, InstructionGroup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.resources import resource_find
from kivy.uix.relativelayout import RelativeLayout

# Adjust for Android file paths
if platform == 'android':
    from android.storage import app_storage_path
    app_path = app_storage_path()
    os.chdir(app_path)

# Colors converted to Kivy's 0-1 range
def rgb_to_norm(rgb_tuple):
    return [x / 255.0 for x in rgb_tuple]

LIGHT_WOOD = rgb_to_norm((220, 190, 140))
DARK_WOOD = rgb_to_norm((115, 74, 18))
RED_BACKGROUND = rgb_to_norm((128, 0, 0))
BLUE = rgb_to_norm((0, 0, 255))
GREY = rgb_to_norm((128, 128, 128))
SELECTED_COLOR = rgb_to_norm((255, 255, 0))
TRAJECTORY_COLOR = rgb_to_norm((255, 255, 255))
BUTTON_COLOR = rgb_to_norm((200, 200, 200))
BUTTON_HOVER_COLOR = rgb_to_norm((160, 160, 160))
POSSIBLE_MOVE_COLOR = rgb_to_norm((152, 251, 152))

# Figures
standard_figures = ["king", "queen", "rook", "rook", "bishop", "bishop", "knight", "knight"]
all_figures = ["king", "queen", "rook", "bishop", "knight"]  # Used for unlimited configuration

class Figure:
    def __init__(self, type, initial_x, initial_y):
        self.type = type
        self.active = True
        self.trajectory = []
        self.initial_x = initial_x
        self.initial_y = initial_y

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.figure = None
        self.pawn = False

class PiecesLayer(RelativeLayout):
    """Layer to handle chess piece images."""
    def __init__(self, game_widget, **kwargs):
        super(PiecesLayer, self).__init__(**kwargs)
        self.game_widget = game_widget
        self.bind(size=self.update_pieces, pos=self.update_pieces)
        self.piece_widgets = {}  # Key: (x, y), Value: Image widget

    def update_pieces(self, *args):
        self.clear_widgets()
        for row in self.game_widget.board:
            for cell in row:
                if cell.pawn:
                    pawn_image_source = piece_images.get("pawn")
                    if pawn_image_source:
                        pawn_image = Image(
                            source=pawn_image_source,
                            size=(self.game_widget.SQUARE_SIZE, self.game_widget.SQUARE_SIZE),
                            size_hint=(None, None),
                            pos=(cell.x * self.game_widget.SQUARE_SIZE,
                                 self.game_widget.height - (cell.y + 1) * self.game_widget.SQUARE_SIZE),
                        )
                        self.add_widget(pawn_image)
                    else:
                        print("Pawn image not found. Skipping pawn rendering.")

                if cell.figure:
                    figure_image_source = piece_images.get(cell.figure.type)
                    if figure_image_source:
                        opacity = 0.4 if not cell.figure.active else 1.0
                        figure_image = Image(
                            source=figure_image_source,
                            size=(self.game_widget.SQUARE_SIZE, self.game_widget.SQUARE_SIZE),
                            size_hint=(None, None),
                            pos=(cell.x * self.game_widget.SQUARE_SIZE,
                                 self.game_widget.height - (cell.y + 1) * self.game_widget.SQUARE_SIZE),
                            opacity=opacity
                        )
                        self.add_widget(figure_image)
                        print(f"Rendering piece {cell.figure.type} at ({cell.x}, {cell.y})")
                    else:
                        print(f"Image for {cell.figure.type} not found. Skipping figure rendering.")

class GameWidget(RelativeLayout):
    SQUARE_SIZE = NumericProperty(0)
    move_count = NumericProperty(0)

    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)
        self.board = []
        self.figures = []
        self.selected_cell = None
        self.possible_moves = []
        # Initialize the pieces layer before starting the game
        self.pieces_layer = PiecesLayer(game_widget=self)
        self.add_widget(self.pieces_layer)
        # Create UI elements
        self.create_ui()
        # Bind move_count to update the steps label
        self.bind(move_count=self.update_steps_label)
        # Initialize the game
        self.init_game()
        # Bind size after initialization
        self.bind(size=self.on_size)

    def init_game(self):
        self.new_configuration()

    def on_size(self, *args):
        min_height = max(self.height - 50, 100)  # Ensure minimum height
        self.SQUARE_SIZE = min(self.width, min_height) / 8.0  # Leave space for UI
        self.draw_board()
        self.pieces_layer.update_pieces()
        self.update_ui_positions()

    def create_ui(self):
        # Create buttons and labels
        self.btn_height = 40
        self.spacing = 10
        self.btn_width = (self.width - 4 * self.spacing) / 3
        self.y_pos = self.height - self.btn_height - self.spacing

        self.btn_restart = Button(text="Restart", size_hint=(None, None),
                                 size=(self.btn_width, self.btn_height))
        self.btn_new_config = Button(text="New Config", size_hint=(None, None),
                                    size=(self.btn_width, self.btn_height))
        self.btn_unlimited = Button(text="Unlimited Config", size_hint=(None, None),
                                   size=(self.btn_width, self.btn_height))
        self.lbl_steps = Label(text=f"Steps: {self.move_count}", size_hint=(None, None),
                              size=(100, self.btn_height))

        # Bind button events
        self.btn_restart.bind(on_release=lambda *args: self.restart_game())
        self.btn_new_config.bind(on_release=lambda *args: self.new_configuration())
        self.btn_unlimited.bind(on_release=lambda *args: self.unlimited_configuration())

        # Add widgets to the layout
        self.add_widget(self.btn_restart)
        self.add_widget(self.btn_new_config)
        self.add_widget(self.btn_unlimited)
        self.add_widget(self.lbl_steps)

        # Update positions
        self.update_ui_positions()

    def update_ui_positions(self, *args):
        self.btn_width = (self.width - 4 * self.spacing) / 3
        self.y_pos = self.height - self.btn_height - self.spacing

        self.btn_restart.size = (self.btn_width, self.btn_height)
        self.btn_new_config.size = (self.btn_width, self.btn_height)
        self.btn_unlimited.size = (self.btn_width, self.btn_height)

        self.btn_restart.pos = (self.spacing, self.y_pos)
        self.btn_new_config.pos = (2 * self.spacing + self.btn_width, self.y_pos)
        self.btn_unlimited.pos = (3 * self.spacing + 2 * self.btn_width, self.y_pos)

        self.lbl_steps.size = (100, self.btn_height)
        self.lbl_steps.pos = (self.width - 100 - self.spacing, self.y_pos)

    def update_steps_label(self, *args):
        self.lbl_steps.text = f"Steps: {self.move_count}"

    def new_configuration(self):
        self.board = [[Cell(x, y) for y in range(8)] for x in range(8)]
        self.figures = []
        self.move_count = 0
        self.selected_cell = None
        self.possible_moves = []
        self.setup_pawns()
        self.setup_figures()
        self.draw_board()
        self.pieces_layer.update_pieces()

    def unlimited_configuration(self):
        self.board = [[Cell(x, y) for y in range(8)] for x in range(8)]
        self.figures = []
        self.move_count = 0
        self.selected_cell = None
        self.possible_moves = []
        self.setup_pawns()
        self.setup_unlimited_figures()
        self.draw_board()
        self.pieces_layer.update_pieces()

    def restart_game(self):
        self.move_count = 0
        self.selected_cell = None
        self.possible_moves = []
        for row in self.board:
            for cell in row:
                cell.figure = None
                cell.pawn = False
        self.setup_pawns()
        for figure in self.figures:
            figure.active = True
            figure.trajectory = []
            self.board[figure.initial_x][figure.initial_y].figure = figure
        self.draw_board()
        self.pieces_layer.update_pieces()

    def setup_pawns(self):
        for x in range(8):
            self.board[x][0].pawn = True

    def setup_figures(self):
        random.shuffle(standard_figures)
        for x in range(8):
            figure = Figure(standard_figures[x], x, 7)
            self.board[x][7].figure = figure
            self.figures.append(figure)

    def setup_unlimited_figures(self):
        unlimited_figures = [random.choice(all_figures) for _ in range(8)]
        for x in range(8):
            figure = Figure(unlimited_figures[x], x, 7)
            self.board[x][7].figure = figure
            self.figures.append(figure)
        # Ensure the game is winnable
        active_figures = len(self.figures)
        pawns = sum(1 for x in range(8) if self.board[x][0].pawn)
        if active_figures < pawns:
            needed_figures = pawns - active_figures
            for _ in range(needed_figures):
                x = random.randint(0, 7)
                while self.board[x][7].figure is not None:
                    x = random.randint(0, 7)
                figure = Figure(random.choice(all_figures), x, 7)
                self.board[x][7].figure = figure
                self.figures.append(figure)

    def draw_board(self):
        self.canvas.clear()
        #self.canvas.before.clear()
        with self.canvas.before:
            # Draw background
            Color(*RED_BACKGROUND)
            Rectangle(pos=self.pos, size=self.size)

            # Draw cells
            for row in self.board:
                for cell in row:
                    self.draw_cell(cell)

            # Draw trajectories
            self.draw_trajectories()

            # Highlight possible moves
            self.draw_possible_moves()

    def draw_cell(self, cell):
        x = cell.x
        y = cell.y
        SQUARE_SIZE = self.SQUARE_SIZE
        # Adjust y-coordinate
        rect_pos = (x * SQUARE_SIZE, self.height - (y + 1) * SQUARE_SIZE)
        rect_size = (SQUARE_SIZE, SQUARE_SIZE)
        # Draw the cell background
        if (x + y) % 2 == 0:
            Color(*LIGHT_WOOD)
        else:
            Color(*DARK_WOOD)
        Rectangle(pos=rect_pos, size=rect_size)
        # Highlight selected cell
        if self.selected_cell == cell:
            Color(*SELECTED_COLOR)
            Line(rectangle=(*rect_pos, *rect_size), width=2)

    def draw_trajectories(self):
        SQUARE_SIZE = self.SQUARE_SIZE
        Color(*TRAJECTORY_COLOR)
        for figure in self.figures:
            if figure.trajectory:
                points = []
                for coord in figure.trajectory:
                    x, y = coord
                    x_pos = x * SQUARE_SIZE + SQUARE_SIZE / 2
                    # Adjust y-coordinate
                    y_pos = self.height - (y * SQUARE_SIZE + SQUARE_SIZE / 2)
                    points.extend([x_pos, y_pos])
                if len(points) >= 4:
                    Line(points=points, width=2)

    def draw_possible_moves(self):
        SQUARE_SIZE = self.SQUARE_SIZE
        Color(*POSSIBLE_MOVE_COLOR)
        for x_move, y_move in self.possible_moves:
            x_pos = x_move * SQUARE_SIZE
            # Adjust y-coordinate
            y_pos = self.height - (y_move + 1) * SQUARE_SIZE
            Line(rectangle=(x_pos, y_pos, SQUARE_SIZE, SQUARE_SIZE), width=2)

    def on_touch_down(self, touch):
        # Let the children widgets handle the touch first
        super(GameWidget, self).on_touch_down(touch)

        x_mouse, y_mouse = touch.pos

        # Check if touch is within the board area
        board_height = self.SQUARE_SIZE * 8
        if y_mouse <= self.height and y_mouse >= self.height - board_height:
            x = int(x_mouse / self.SQUARE_SIZE)
            # Adjust y-coordinate
            y = int((self.height - y_mouse) / self.SQUARE_SIZE)
            if 0 <= x < 8 and 0 <= y < 8:
                if self.selected_cell:
                    if (x, y) in self.possible_moves:
                        self.make_move(x, y)
                    else:
                        self.selected_cell = None
                        self.possible_moves = []
                else:
                    cell = self.board[x][y]
                    if cell.figure and cell.figure.active:
                        self.selected_cell = cell
                        self.possible_moves = self.get_possible_moves(cell)
                self.draw_board()
                self.pieces_layer.update_pieces()

    def make_move(self, x, y):
        target_cell = self.board[x][y]
        # Record trajectory
        trajectory = self.get_trajectory(self.selected_cell, target_cell)
        # Update the figure's trajectory
        self.selected_cell.figure.trajectory.extend(trajectory[1:])
        # Move the figure to the new cell
        target_cell.figure = self.selected_cell.figure
        self.selected_cell.figure = None
        # If captures a pawn, set figure to inactive
        if target_cell.pawn:
            target_cell.pawn = False
            target_cell.figure.active = False
        self.selected_cell = None
        self.possible_moves = []
        self.move_count += 1
        # Check for game over conditions
        if self.all_pawns_destroyed():
            self.display_message(f"You won in {self.move_count} steps!")
        elif not self.any_possible_moves():
            self.display_message("No more possible moves.\nYou lost.")
        self.draw_board()
        self.pieces_layer.update_pieces()

    def get_possible_moves(self, cell):
        moves = []
        occupied_cells_figures, occupied_cells_pawns, trajectory_cells = self.get_occupied_cells(exclude_cell=cell)
        other_trajectories = trajectory_cells.copy()
        if cell.figure.trajectory:
            other_trajectories.difference_update(cell.figure.trajectory)
        figure_type = cell.figure.type
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
                        (x, y) not in cell.figure.trajectory):
                        moves.append((x, y))
        elif figure_type == "king":
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, 1), (1, 0), (-1, 0), (0, -1)]:
                x, y = cell.x + dx, cell.y + dy
                if 0 <= x < 8 and 0 <= y < 8:
                    if ((x, y) not in occupied_cells_figures and
                        (x, y) not in other_trajectories and
                        (x, y) not in cell.figure.trajectory):
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
                            break
                        if (x, y) in cell.figure.trajectory:
                            break
                        if (x, y) in other_trajectories:
                            continue
                        moves.append((x, y))
                    else:
                        break
        return moves

    def get_occupied_cells(self, exclude_cell=None):
        occupied_cells_figures = set()
        occupied_cells_pawns = set()
        trajectory_cells = set()
        for row in self.board:
            for cell in row:
                if cell.figure and cell != exclude_cell:
                    occupied_cells_figures.add((cell.x, cell.y))
                if cell.figure and cell.figure.trajectory:
                    trajectory_cells.update(cell.figure.trajectory)
                if cell.pawn:
                    occupied_cells_pawns.add((cell.x, cell.y))
        return occupied_cells_figures, occupied_cells_pawns, trajectory_cells

    def get_trajectory(self, start_cell, end_cell):
        trajectory = []
        x0, y0 = start_cell.x, start_cell.y
        x1, y1 = end_cell.x, end_cell.y
        figure_type = start_cell.figure.type
        if figure_type == "knight":
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

    def all_pawns_destroyed(self):
        for row in self.board:
            for cell in row:
                if cell.pawn:
                    return False
        return True

    def any_possible_moves(self):
        for row in self.board:
            for cell in row:
                if cell.figure and cell.figure.active:
                    possible_moves = self.get_possible_moves(cell)
                    if possible_moves:
                        return True
        return False

    def display_message(self, message):
        # Create content for the popup
        content = FloatLayout()
        label = Label(text=message, size_hint=(1, 0.7), pos_hint={'x': 0, 'top': 1})
        btn_restart = Button(text='Restart', size_hint=(0.45, 0.2), pos_hint={'x': 0.05, 'y': 0.05})
        btn_quit = Button(text='Quit', size_hint=(0.45, 0.2), pos_hint={'right': 0.95, 'y': 0.05})
        content.add_widget(label)
        content.add_widget(btn_restart)
        content.add_widget(btn_quit)
        # Create the popup
        popup = Popup(title='Game Over', content=content, size_hint=(0.8, 0.5))
        # Bind buttons
        btn_restart.bind(on_release=lambda *args: (popup.dismiss(), self.new_configuration()))
        btn_quit.bind(on_release=lambda *args: App.get_running_app().stop())
        popup.open()

# Load images for the pieces
piece_images = {}
for piece_name in ["king", "queen", "rook", "bishop", "knight", "pawn"]:
    image_path = resource_find(f"images/{piece_name}.png")
    if not image_path:
        print(f"Image {piece_name}.png not found. Please ensure it's in the images directory.")
    else:
        print(f"Loading image for {piece_name} from {image_path}")
        piece_images[piece_name] = image_path  # Store the path instead of texture

class ChessPuzzleApp(App):
    def build(self):
        self.title = "Trajectory Chess Puzzle"
        return GameWidget()

if __name__ == '__main__':
    ChessPuzzleApp().run()
