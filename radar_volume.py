import scipy.io as scio
import numpy as np
from datetime import datetime

class RadarVolume(object):
    """
    An object containing the data and metadata for a single volume in a PAR scan.
    """
    def __init__(self, filename, radar, lat, lon, elev_m, height_m, lambda_m, prf_hz, nyq_m_per_s,
                 datestr, time, vcp, products, sclice_type, start_range_km, ranges_km,
                 doppler_resolution_km, azimuths_rad, azimuth_swath_rad, elevations_rad, 
                 elevation_swath_rad):
        self.filename = filename
        self.radar = radar
        self.lat = lat
        self.lon = lon
        self.elev_m = elev_m
        self.height_m = height_m
        self.lambda_m = lambda_m
        self.prf_hz = prf_hz
        self.nyq_m_per_s = nyq_m_per_s
        # FIXME: Double-quoted "" string arrays are not supported by SciPy at the moment. Datestr is derived differently below.
        self.datestr = datestr
        self.time = time
        self.vcp = vcp
        self.products = products
        self.sclice_type = sclice_type
        self.start_range_km = start_range_km
        self.ranges_km = ranges_km
        self.doppler_resolution_km = doppler_resolution_km
        self.azimuths_rad = azimuths_rad
        self.azimuth_swath_rad = azimuth_swath_rad
        self.elevations_rad = elevations_rad
        self.elevation_swath_rad  = elevation_swath_rad
    
    @staticmethod
    def build_radar_volume_from_matlab_file(file_path):
        """
        Static method for reading in a MATLAB data file containing a volume of data
        from a PAR scan. Using the static method convention to indicate that construction
        of one of these objects is non-trivial and may take some time.
        """
        try:
            # Load the data.
            #   squeeze_me=True, collapse unit dimensions (no 1x1 ndarrays).    
            data = scio.loadmat(file_path, squeeze_me=True)
        
            if 'volume' not in data:
                print("No 'volume' key found in the .mat file. Please check the data structure.")
                return None
            
            # TODO: After this point, it is assumed the data is well-formed. This is probably a bad assumption.

            # Process the volume into a convenient data format for our plots.
            volume = data['volume']
            first_slice = volume[0]

            # Extract metadata.
            azimuths_rad = [(az * np.pi / 180.0) for az in first_slice['az_deg']]
            azimuth_swath_rad = np.abs(azimuths_rad[-1] - azimuths_rad[0])
            num_azimuths = len(azimuths_rad)
            elevations_rad = [(entry['sweep_el_deg'] * np.pi / 180.0) for entry in volume]
            elevation_swath_rad = np.abs(elevations_rad[-1] - elevations_rad[0])
            num_elevations = len(elevations_rad)
            product_types = [entry['type'] for entry in first_slice['prod']]
            start_range_km = first_slice['start_range_km']
            # DR "doppler resolution"
            doppler_resolution_km = first_slice['prod'][0]['dr'] / 1000.0
            
            # Build up the range bins
            num_ranges = first_slice['prod'][0]['data'].shape[0]
            ranges_km = [(start_range_km + (doppler_resolution_km * i)) for i in range(num_ranges)]
            range_swath_km = np.abs(ranges_km[-1] - ranges_km[0])
            
            # Transform the data from each product into a 3-dimensional ndarray and place it in the products dictionary
            products = {}
            for p_type in product_types:
                # Initialize the 3-D block of data for the current product (el x az x range)
                products[p_type] = np.zeros((num_elevations, num_azimuths, num_ranges))

                # Transform the source data into the 3-D block for the current product.
                p_data = products[p_type]
                p_idx = product_types.index(p_type)
                for el_idx in range(num_elevations):
                    prods = volume[el_idx]['prod']
                    if p_type == 'R':
                        p_data[el_idx, :, :] = np.abs(prods[p_idx]['data']).astype(np.float32).T
                    else:
                        p_data[el_idx, :, :] = prods[p_idx]['data'].astype(np.float32).T
                    

            return RadarVolume(
                filename=file_path,
                radar=first_slice['radar'] if 'radar' in first_slice.dtype.names else None,
                lat=first_slice['lat'] if 'lat' in first_slice.dtype.names else None,
                lon=first_slice['lon'] if 'lon' in first_slice.dtype.names else None,
                elev_m=first_slice['elev_m'] if 'elev_m' in first_slice.dtype.names else None,
                height_m=first_slice['height_m'] if 'height_m' in first_slice.dtype.names else None,
                lambda_m=first_slice['lambda_m'] if 'lambda_m' in first_slice.dtype.names else None,
                prf_hz=first_slice['prf_hz'] if 'prf_hz' in first_slice.dtype.names else None,
                nyq_m_per_s=first_slice['nyq_m_per_s'] if 'nyq_m_per_s' in first_slice.dtype.names else None,
                # FIXME: Double-quoted "" string arrays are not supported by SciPy at the moment.
                # datestr=first_slice['datestr'] if 'datestr' in first_slice.dtype.names else None,
                datestr=0,
                time=first_slice['time'] if 'time' in first_slice.dtype.names else None,
                vcp=first_slice['vcp'] if 'vcp' in first_slice.dtype.names else None,
                products=products,
                sclice_type=first_slice['type'] if 'type' in first_slice.dtype.names else None,
                start_range_km=start_range_km,
                ranges_km=ranges_km,
                doppler_resolution_km=doppler_resolution_km,
                azimuths_rad=azimuths_rad,
                azimuth_swath_rad=azimuth_swath_rad,
                elevations_rad=elevations_rad,
                elevation_swath_rad=elevation_swath_rad)

        except:
            # TODO: Hushing any volume loading errors down to a single print statement for now. In the future, this should write to a log or something so that it can be triaged.
            print(f'Failed to load .mat file: "{file_path}"')
            return None