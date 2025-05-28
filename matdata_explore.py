import scipy.io as scio
import numpy as np
import sys
import vispy.app
from vispy.scene import SceneCanvas, PanZoomCamera, AxisWidget
from vispy.scene.visuals import Image
from vispy.plot import Fig, PlotWidget
from vispy.color import Colormap
from vispy.visuals.transforms import STTransform, PolarTransform
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QDockWidget
from PySide6.QtCore import Qt, Slot, QObject
from color_maps import ColorMaps
from volume_slice_selector import VolumeSliceSelector
from polar_transform_editor import PolarTransformEditor

# mat_file = 'D:/cs5093/20240428/Scan 12/MATLAB/HRUS_240428_020033000_100.mat'
mat_file = 'D:/cs5093/20240428/Scan 12/MATLAB/HRUS_240428_020051000_100.mat'

# Load the data, collapse unit dimensions (no 1x1 ndarrays)
data = scio.loadmat(mat_file, squeeze_me=True)

print(data.keys())
# dict_keys(['__header__', '__version__', '__globals__', 'volume', '__function_workspace__'])

print(f'Volume shape: {data["volume"].shape}')
print(f'Volume ndim: {data["volume"].ndim}')

volume = data['volume']

# Extract the azimuth metadata
azimuths = [(az * np.pi / 180.0) for az in volume[0]['az_deg']]

# Extract the elevation metadata
print(volume[0]['sweep_el_deg'])
elevations = [(entry['sweep_el_deg'] * np.pi / 180.0) for entry in volume]

# Extract the product metadata
products = [entry['type'] for entry in volume[0]['prod']]

# Extraxt the range metadata
start_range_km = volume[0]['start_range_km']
doppler_resolution = volume[0]['prod'][0]['dr']

# Calculate this in the plotter once you have the metadata there
y_start = np.floor(start_range_km * 1000 / doppler_resolution)

num_ranges = volume[0]['prod'][0]['data'].shape[0]
ranges = [(start_range_km + (doppler_resolution * i) / 1000.0) for i in range(num_ranges)]

vol_prod_dict = {}
print(products)
for product in products:
    # Initialize the 3-D block of data for the current product (el x az x range)
    if product == 'R':
        vol_prod_dict[product] = np.zeros((len(elevations), len(azimuths), len(ranges)), dtype=complex)
    else:
        vol_prod_dict[product] = np.zeros((len(elevations), len(azimuths), len(ranges)))

    # Transform the source data into the 3-D block for the current product.
    vol = vol_prod_dict[product]
    prod_idx = products.index(product)
    for el_idx in range(len(elevations)):
        prods = volume[el_idx]['prod']
        # if product == 'Z':
        #     vol[el_idx, :, :] = np.nan_to_num(prods[prod_idx]['data'].T, nan=0.0)
        # else:
        vol[el_idx, :, :] = prods[prod_idx]['data'].T

# Print metadata shapes for verification
print("Num products: ", len(products))                # 9
print("Num elevations: ", len(elevations))            # 20
print("Num azimuths: ", len(azimuths))                # 44
print("Num ranges: ", len(ranges))                    # 1822
print("Volume shape:", vol_prod_dict['Z'].shape)      # (20, 44, 1822)

print(f'Range start: {ranges[0]}, range end: {ranges[-1]}')

# Reflectivity
vol = vol_prod_dict['Z']
# PPI
el_idx = 0

ppi_slice = vol[el_idx, :, :]
print(f'PPI slice shape {ppi_slice.shape}')

# RHI
az_idx = len(azimuths) // 2
rhi_slice = vol[:, az_idx, :]
print(f'RHI slice shape {rhi_slice.shape}')

class SlicePlot(QObject):
    cmaps = ColorMaps('D:/cs5093/20240428/MATLAB Display Code/colormaps.mat')

    def __init__(self, parent=None, slice_type='ppi'):
        super().__init__(parent=parent)
        
        # The type of data slice to display ('ppi'/'rhi')
        self.slice_type = slice_type

        # Radar Volume information
        self.azimuths = azimuths
        self.elevations = elevations
        self.ranges = ranges
        self.vol_prod_dict = vol_prod_dict

        # Current locations on the principle axes to slice the data.
        self.current_az = len(azimuths) // 2
        eid = elevations.index(2.25 * np.pi / 180) or None
        self.current_el = eid if eid is not None else 0

        # Scene setup
        if self.slice_type == 'rhi':
            self.canvas = SceneCanvas(size=(len(elevations), len(ranges)))
        else:
            self.canvas = SceneCanvas(size=(len(azimuths), len(ranges)))
        # self.grid = self.canvas.central_widget.add_grid(spacing=0)
        # self.view = self.grid.add_view(row=0, col=1, camera='panzoom')
        self.view = self.canvas.central_widget.add_view(camera='panzoom')

        # Color Setup (depends on displayed product)
        self.cmap = SlicePlot.cmaps.reflectivity()

        vol = self.vol_prod_dict['Z']
        if self.slice_type == 'rhi':
            # RHI: elevation x range
            slice = vol[:, self.current_az, :].T
        else:
            # PPI: azimuth x range.
            slice = vol[self.current_el, :, :].T
        self.image = Image(slice, parent=self.view.scene, cmap=self.cmap, clim=(-10, 70), grid=(1, 360), method='subdivide')
        # self.view.camera = "panzoom"

        # Axes
        # self.x_axis = AxisWidget(orientation='bottom', axis_label="Range (km)")
        # self.x_axis.stretch = (1, 0.1)
        # self.grid.add_widget(self.x_axis, row=1, col=1)
        # self.x_axis.link_view(self.view)

        # Because we transform into polar coordinates
        # Width of the camera is range_start_km * 1000 / doppler_resolution + len(ranges)
        cam_width = y_start + len(ranges)
        if self.slice_type == 'rhi':
            self.view.camera.set_range((0, cam_width), (0, cam_width))
        else:
            self.view.camera.set_range((-cam_width, cam_width), (-cam_width, cam_width))
        
        # Calculate the radial extents of the slice
        if self.slice_type == 'rhi':
            self.radial_swath = elevations[-1] - elevations[0]
        else:
            self.radial_swath = azimuths[-1] - azimuths[0]

        # Complicated method for transforming an image in cartesian coordinates into polar coordinates
        # Credit: https://stackoverflow.com/a/68390497/13542651
        scx = 1
        scy = 1
        xoff = 0
        yoff = 0

        ori0 = 0 # Side of the image to collapse at origin (0 for top/1 for bottom)
        loc0 = self.radial_swath if self.slice_type == 'ppi' else self.elevations[0] # Location of zero (0, 2* np.pi) clockwise
        dir0 = 1 # Direction cw/ccw -1, 1

        self.on_transform_changed(scx, scy, xoff, yoff, ori0, loc0, dir0)
        # self.update_plot()

    @Slot(float, float, int, int, int, float, int)
    def on_transform_changed(self, scale_x, scale_y, offset_x, offset_y, orig0, loc0, dir0):
        transform = (
            STTransform(scale=(scale_x, scale_y), translate=(offset_x, offset_y))

            *PolarTransform()

            # 1
            # pre scale image to work with polar transform
            # PolarTransform does not work without this
            # scale vertex coordinates to 2*pi
            *STTransform(scale=(self.radial_swath / self.image.size[0], 1.0))

            # 2
            # origin switch via translate.y, fix translate.x
            *STTransform(translate=(self.image.size[0] * (orig0 % 2) * 0.5,                                                                   
                                    -self.image.size[1] * (orig0 % 2)))

            # 3
            # location change via translate.x
            *STTransform(translate=(self.image.size[0] * (loc0), 0.0))

            # 4
            # direction switch via inverting scale.x
            * STTransform(scale=(-dir0 if self.slice_type == 'ppi' else dir0, 1.0))

            # 5
            # Shift the image up for the receive start (start_range_km * 1000 / doppler_resolution)
            *STTransform(translate=(0, y_start))
        )
        self.image.transform = transform
        self.canvas.update()

    @Slot(int, int)
    def on_az_el_index_selection_changed(self, el_idx, az_idx):
        # slice_changed = False
        # if self.slice_type == 'rhi' and self.current_az != az_idx:
        #     slice_changed = True
        # elif self.current_el != el_idx:
        #     slice_changed = True
        
        self.current_az = az_idx
        self.current_el = el_idx
        
        vol = self.vol_prod_dict['Z']
        if self.slice_type == 'rhi':
            # print("RHI Plot Update")
            # RHI: elevation x range
            slice = vol[:, self.current_az, :].T
            # x_extent = (0, self.ranges[-1], self.elevations[0], self.elevations[-1])
        else:
            # print("PPI Plot Update")
            # PPI: azimuth x range
            slice = vol[self.current_el, :, :].T
            # extent = (0, self.ranges[-1], self.azimuths[0], self.azimuths[-1])
        
        self.image.set_data(slice)
        self.canvas.update()

if __name__ == "__main__":
    app = vispy.app.use_app("pyside6")
    app.create()

    window = QMainWindow()
    window.setWindowTitle("Plotting RHI Data")

    widget = QWidget()
    layout = QHBoxLayout(widget)

    ppi = SlicePlot(widget)
    layout.addWidget(ppi.canvas.native)

    rhi = SlicePlot(widget, slice_type='rhi')
    layout.addWidget(rhi.canvas.native)

    dockable_vss = QDockWidget("Volume Slice Selector", window)
    window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dockable_vss)
    volume_slice_selector = VolumeSliceSelector()
    volume_slice_selector.on_grid_updated(len(elevations), len(azimuths), 20, 20, 10)
    volume_slice_selector.selection_changed.connect(ppi.on_az_el_index_selection_changed)
    volume_slice_selector.selection_changed.connect(rhi.on_az_el_index_selection_changed)
    dockable_vss.setWidget(volume_slice_selector)

    # dockable_te = QDockWidget("Transform Editor", window)
    # window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dockable_te)
    # polar_transform_editor = PolarTransformEditor()
    # polar_transform_editor.transform_updated.connect(rhi.on_transform_changed)
    # dockable_te.setWidget(polar_transform_editor)

    window.setDockNestingEnabled(True)
    window.setCentralWidget(widget)

    window.show()
    app.run()
