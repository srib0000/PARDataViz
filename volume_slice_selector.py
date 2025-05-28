from PySide6.QtWidgets import QApplication, QWidget, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QObject, Slot, QEvent
from PySide6.QtGui import QBrush, QPen
from radar_volume import RadarVolume

class CircleItem(QObject, QGraphicsEllipseItem):
    """
    A circle glyph rendered in the volume slice selector which visually
    encodes the position within a grid of angular extents in both azimuth and
    elevation. The row index "i" of each glyph represents the selected PPI slice
    (a planar horizontal slice at the given elevation angle), and the column 
    index "j" of each glyph represents the selected RHI slice (a planar vertical
    slice at the given azimuth angle).
    """
    mouse_hovered = Signal(int, int)

    def __init__(self, i, j, x, y, radius, *args, **kwargs):
        QObject.__init__(self)
        QGraphicsEllipseItem.__init__(self, x, y, radius * 2, radius * 2, *args, **kwargs)
        self.i = i
        self.j = j
        self.default_brush = QBrush(Qt.lightGray)
        self.highlight_brush = QBrush(Qt.red)
        self.selected_brush = QBrush(Qt.blue)
        self.selected = False
        self.setBrush(self.default_brush)
        self.setPen(QPen(Qt.black))
        # self.setAcceptHoverEvents(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.scene().on_circle_selected(self.i, self.j)

    # def hoverEnterEvent(self, event):
    #     self.mouse_hovered.emit(self.i, self.j)
    #     super().hoverEnterEvent(event)

    # def hoverLeaveEvent(self, event):
    #     self.scene().clear_highlights()
    #     super().hoverLeaveEvent(event)

    def set_highlighted(self, highlighted):
        if self.selected:
            self.setBrush(self.selected_brush)
        elif highlighted:
            self.setBrush(self.highlight_brush)
        else:
            self.setBrush(self.default_brush)

    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.setBrush(self.selected_brush)
        else:
            self.setBrush(self.default_brush)

class MouseLeaveFilter(QObject):
    """
    An event filter object which allows us to detect when the mouse has left the GraphicsScene
    for the volume slice selector.
    """
    mouse_left = Signal()

    def eventFilter(self, object, event: QEvent):
        # Useful debug message for figuring out what types of events can be filtered.
        # print(event.type())
        if event.type() == QEvent.Type.GraphicsSceneLeave:
            self.mouse_left.emit()
            # Return True because we responded to the event.
            return True
        # Return False because we didn't care about the event.
        return False

class CircleScene(QGraphicsScene):
    """
    A 2D graphics scene containing primitive circular glyphs which allows for the
    simultaneous interactive highlighting and selection of rows and columns
    (slices within a volumetric block of data).
    """
    mouse_hovered = Signal(int, int)

    def __init__(self, label, selector_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.selector_widget = selector_widget
        self.circles = []
        self.last_hover_x = -1
        self.last_hover_y = -1
        self.selected_row = 0
        self.selected_col = 0

        self.leave_filter = MouseLeaveFilter()
        self.leave_filter.mouse_left.connect(self.on_mouse_left)
        self.installEventFilter(self.leave_filter)

    def addItem(self, item):
        super().addItem(item)
        if isinstance(item, CircleItem):
            self.circles.append(item)

    def add_labels(self, rows, cols, x_spacing, y_spacing, radius, total_height):
        # Store values in attributes to be used by mouse move event
        self.rows = rows
        self.cols = cols
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.total_height = total_height
        
        for i in range(rows):
            y = total_height - (i * y_spacing) + radius - 10
            label = QGraphicsTextItem(str(i))
            label.setPos(-30, y)
            self.addItem(label)
        for j in range(cols):
            label = QGraphicsTextItem(str(j))
            label.setPos(j * x_spacing + radius / 2, rows * y_spacing)
            self.addItem(label)

    def highlight_row_and_column(self, row, col):
        for circle in self.circles:
            if circle.i == row or circle.j == col:
                circle.set_highlighted(True)
            else:
                circle.set_highlighted(False)

    def clear_highlights(self):
        for circle in self.circles:
            circle.set_highlighted(False)

    def mouseMoveEvent(self, event):
        # Map the scene position to the nearest grid indices
        pos = event.scenePos()
        col = int(pos.x() / self.x_spacing)
        row = int((self.total_height - pos.y()) / self.y_spacing) + 1

        self.highlight_row_and_column(row, col)

        # Check if the indices are within the grid bounds
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if self.last_hover_x != col or self.last_hover_y != row:
                # print(f"New hover location! ({col}, {row})")
                self.mouse_hovered.emit(row, col)
            self.last_hover_x = col
            self.last_hover_y = row
        else: 
            # Reset last hover coords when leaving bounds
            self.last_hover_x = -1
            self.last_hover_y = -1
        super().mouseMoveEvent(event)

    @Slot()
    def on_mouse_left(self):
        # Tell all the listeners to set themselves back to the selected row and col when the mouse leaves.
        self.clear_highlights()
        self.selector_widget.selection_changed.emit(self.selected_row, self.selected_col)

    @Slot(int, int)
    def on_circle_selected(self, i, j):
        """Slot to handle circle selection."""
        self.selected_row = i
        self.selected_col = j
        for circle in self.circles:
            if circle.i == i or circle.j == j:
                circle.set_selected(True)
            else:
                circle.set_selected(False)
        self.label.setText(f"Selected Indices: ({i}, {j})")
        self.selector_widget.selection_changed.emit(i, j)

class VolumeSliceSelector(QWidget):
    """
    Top-level class of the volume slice selector class. A widget which allows the
    user to dyanmically select a 2D position within a grid of encoded azimuth and
    elevation extents within volumetric PAR data. This 2D position represents
    both a horizontal (PPI) and vertical (RHI) slice of the volumetric data.
    
    The emitted "selection_changed" signal will indicate to other UI elements
    that the selected slices of the data has changed so they may update themselves
    accordingly.

    The "update_grid" slot allows other UI elements to update the grid. For instance,
    when a new volume of data is loaded with different angular extents).
    """
    # Signal emitted when a slice is selected
    selection_changed = Signal(int, int) 
    # Signal emitted when a slice is hovered
    slice_hovered = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Selected Indices: None")
        self.layout.addWidget(self.label)

        self.view = QGraphicsView()
        self.scene = CircleScene(self.label, self)
        self.scene.mouse_hovered.connect(self.on_hover)
        self.view.setScene(self.scene)
        self.layout.addWidget(self.view)

        self.rows = 0
        self.cols = 0
        self.x_spacing = 50
        self.y_spacing = 50
        self.radius = 20

    @Slot(int, int, int, int)
    def on_grid_updated(self, rows, cols, x_spacing, y_spacing, radius):
        """Dynamically update the grid with new parameters."""
        self.rows = rows
        self.cols = cols
        self.x_spacing = x_spacing
        self.y_spacing = y_spacing
        self.radius = radius

        # Clear the existing scene
        self.scene.clear()
        self.scene.circles = []

        # Calculate the total height for flipping the y-axis
        total_height = (rows - 1) * y_spacing

        # Add updated grid
        self.scene.add_labels(rows, cols, x_spacing, y_spacing, radius, total_height)
        for i in range(rows):
            for j in range(cols):
                x = j * x_spacing
                y = total_height - (i * y_spacing)
                circle = CircleItem(i, j, x, y, radius)
                # circle.mouse_hovered.connect(self.scene.highlight_row_and_column)
                self.scene.addItem(circle)

    @Slot(RadarVolume)
    def on_render_volume(self, r_volume: RadarVolume):
        self.on_grid_updated(len(r_volume.elevations_rad), len(r_volume.azimuths_rad), 20, 20, 10)

    @Slot(int, int)
    def on_selection(self, i, j):
        """Slot to programmatically select a slice."""
        self.scene.on_circle_selected(i, j)

    @Slot(int, int)
    def on_hover(self, i, j):
        self.slice_hovered.emit(i, j)

if __name__ == "__main__":
    import sys

    def on_selection_changed(i, j):
        print(f'Circle selected: ({i}, {j})')

    app = QApplication(sys.argv)
    widget = VolumeSliceSelector()
    widget.selection_changed.connect(on_selection_changed)

    # Update the grid
    widget.on_grid_updated(20, 44, 20, 20, 10)

    # Programmatically select a circle
    widget.on_selection(19, (44 // 2) - 1)

    widget.show()
    sys.exit(app.exec())
