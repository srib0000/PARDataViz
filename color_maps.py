import scipy.io as scio
from vispy.color import Colormap

class ColorMaps:
    """
    Reflectivity and Velocity Colormaps
    """
    def __init__(self, path_to_maps) -> None:
        self.path_to_maps = path_to_maps
        self.maps_mat = scio.loadmat(self.path_to_maps)
        # Products: ['Z', 'V', 'W', 'D', 'P', 'R']
        self.maps_by_prod = {
            'Z': (self.reflectivity(), self.reflectivity_lims()),
            'V': (self.velocity(), self.velocity_lims()),
            'W': (self.spectrum_width(), self.spectrum_width_lims()),
            'D': (self.zdr(), self.zdr_lims()),
            'P': (self.phi_dp(), self.phi_dp_lims()),
            'R': (self.rho_hv(), self.rho_hv_lims())
        }
        self.units_by_prod = {
            'Z': 'dB',
            'V': 'm/s',
            'W': 'σ(m/s)',
            'D': 'dB',
            'P': '',
            'R': '°'
        }

    def get_cmap_and_clims_for_product(self, product):
        return self.maps_by_prod[product]  

    def get_units_for_product(self, product):
        return self.units_by_prod[product]      

    def reflectivity(self):
        return Colormap(self.maps_mat['reflectivity'])
    
    def reflectivity_lims(self):
        return (-10, 70)

    def velocity(self):
        return Colormap(self.maps_mat['velocity'])
    
    def velocity_lims(self):
        return (-24, 24)
    
    def phi_dp(self):
        return Colormap(self.maps_mat['phi'])
    
    def phi_dp_lims(self):
        return (20, 150)
    
    def spectrum_width(self):
        return Colormap(self.maps_mat['width'])
    
    def spectrum_width_lims(self):
        return (-1, 8)
    
    def zdr(self):
        return Colormap(self.maps_mat['zdr'])
    
    def zdr_lims(self):
        return (-2, 6)
    
    def rho_hv(self):
        return Colormap(self.maps_mat['rho'])
    
    def rho_hv_lims(self):
        return (0.8, 1.05)
    