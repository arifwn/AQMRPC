
import numpy


class ModelGrid(object):
    def __init__(self, pos_x, pos_y, delta_x, delta_y, grid_w, grid_h, elev_add):
        pass


class HillHeight(object):
    def __init__(self, ref_lat, ref_lon):
        self.srtm_files = []
        self.srtm_pos = []
        self.srtm_data = []
        self.model_data = []
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
    
    def add_srtm_file(self, file_path, lat, lon, zipped=True):
        if zipped:
            zip_file = zipfile.ZipFile(file_path, 'r')
            zip_file_name = zip_file.namelist()[0]
            hgt_string = zip_file.read(zip_file_name)
            zip_file.close()
        else:
            srtm_file = open(file_path, 'rb')
            hgt_string = srtm_file.read()
        
        hgt_data = numpy.flipud(((numpy.fromstring(string=hgt_string, dtype='int16')).byteswap()).reshape(1201,1201))
        
        self.srtm_files.append(file_path)
        self.srtm_pos.append((lat, lon))
        self.srtm_data.append(hgt_data)
    
    def add_model_grid(self, pos_x, pos_y, delta_x, delta_y, grid_w, grid_h, elev_add):
        model_grid = ModelGrid(pos_x, pos_y, delta_x, delta_y, grid_w, grid_h, elev_add)
        self.model_data.append(model_grid)
    
    def srtm_get_distance_x(self, srtm_index, x_pos):
        '''
        Return the x axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        pass
    
    def srtm_get_distance_y(self, srtm_index, y_pos):
        '''
        Return the y axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        pass
    
    def modelgrid_get_distance_x(self, modelgrid_index, x_pos):
        '''
        Return the x axis distance between a point in model grid and
        the reference point (in m).
        '''
        pass
    
    def modelgrid_get_distance_y(self, modelgrid_index, y_pos):
        '''
        Return the y axis distance between a point in model grid and
        the reference point (in m).
        '''
        pass
    
    def modelgrid_get_elevation(self, x, y):
        ''' Return elevation for particular point in model grid. '''
    
    def process(self):
        pass
    
    def save(self, target_path):
        pass
    