
import math
import json

import numpy

from aqmrpc.aermod.hillheight import utm

class ModelGrid(object):
    def __init__(self, x, y, delta_x, delta_y, w, h, base_elevation=0):
        self.x = x # x distance from ref coordinate in meter
        self.y = y # y distance from ref coordinate in meter
        self.delta_x = delta_x
        self.delta_y = delta_y
        self.w = w
        self.h = h
        self.base_elevation = base_elevation # ignore this for now...
        self.hillheight = numpy.array([])
        self.elevation = numpy.array([])
        self.hillheight.resize((w, h))
        self.elevation.resize((w, h))
    
    def set_hillheight(self, x, y, hillheight):
        self.hillheight[x][y] = hillheight
    
    def set_elevation(self, x, y, elevation):
        self.elevation[x][y] = elevation
    
    def get_elevation(self, x, y):
        ''' Return elevation for particular point in model grid. '''
        return self.elevation[x][y]

    def get_hillheight(self, x, y):
        ''' Return hill height for particular point in model grid. '''
        return self.hillheight[x][y]


class HillHeight(object):
    def __init__(self, ref_lat, ref_lon):
        self.srtm_files = []
        self.srtm_data = []
        self.model_grids = []
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.zone, self.hemisphere = utm.get_zone_hem(ref_lat, ref_lon)
        self.ref_easting, self.ref_northing = utm.convert_to_utm_fixzone(ref_lat, ref_lon, self.zone, self.hemisphere)
    
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
        hgt_data.lat = lat
        hgt_data.lon = lon
        self.easting, self.northing = utm.convert_to_utm_fixzone(lat, lon, self.zone, self.hemisphere)
        
        self.srtm_files.append(file_path)
        self.srtm_data.append(hgt_data)
    
    def add_model_grid(self, x, y, delta_x, delta_y, w, h, base_elevation=0):
        model_grid = ModelGrid(x, y, delta_x, delta_y, w, h, base_elevation)
        self.model_grids.append(model_grid)
    
    def srtm_get_x_distance(self, srtm, x_pos):
        '''
        Return the x axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        lon = srtm.lon + (float(x_pos) / 1200.0)
        easting, northing = utm.convert_to_utm_fixzone(srtm.lat, lon, self.zone, self.hemisphere)
        return easting - self.ref_easting
    
    def srtm_get_y_distance(self, srtm, y_pos):
        '''
        Return the y axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        lat = srtm.lat + (float(y_pos) / 1200.0)
        easting, northing = utm.convert_to_utm_fixzone(lat, srtm.lon, self.zone, self.hemisphere)
        return northing - self.ref_northing
    
    def modelgrid_get_distance_x(self, modelgrid, x_pos):
        '''
        Return the x axis distance between a point in model grid and
        the reference point (in m).
        '''
        return modelgrid.x + x_pos * modelgrid.delta_x
    
    def modelgrid_get_distance_y(self, modelgrid, y_pos):
        '''
        Return the y axis distance between a point in model grid and
        the reference point (in m).
        '''
        return modelgrid.y + y_pos * modelgrid.delta_y
    
    def modelgrid_get_elevation(self, modelgrid, x, y):
        ''' Obtain elevation for (x,y) position in modelgrid from srtm data. '''
        pos_x = self.modelgrid_get_distance_x(modelgrid, x)
        pos_y = self.modelgrid_get_distance_y(modelgrid, y)
        elevation = -9999
        easting  = pos_y + self.ref_easting
        northing  = pos_x + self.ref_northing
        lat, lon = convert_to_latlon(easting, northing, self.zone, self.hemisphere)
        
        for srtm in self.srtm_data:
            # determine which srtm data contains this coordinate
            if ((srtm.lat + 1) >= lat) and (srtm.lat <= lat) and ((srtm.lon + 1) >= lon) and (srtm.lon <= lon):
                # compute correct grid position
                lat_index = int((lat - srtm.lat) / (1.0 / 1200.0))
                lon_index = int((lon - srtm.lon) / (1.0 / 1200.0))
                elevation = srtm[lat_index][lon_index]
        
        return elevation
    
    def process(self):
        ''' Compute hillheight data from all srtm data. '''
        for grid in self.model_grids:
            for x in xrange(grid.w):
                for y in xrange(grid.h):
                    # obtain elevation for current point
                    elevation = self.modelgrid_get_elevation(grid, x, y)
                    grid.set_elevation(x, y, elevation)
                    
                    if elevation < -9998:
                        # blank data, do not compute hillheight
                        grid.set_hillheight(x, y, -9999)
                        continue
                    
                    # compute hillheight from srtm data
                    hillheight = elevation
                    distance_from_ref_x = self.modelgrid_get_distance_x(grid, x)
                    distance_from_ref_y = self.modelgrid_get_distance_y(grid, y)
                    
                    for srtm in self.srtm_data:
                        srtm_w, srtm_h = srtm.shape
                        
                        for lat_index in xrange(srtm_w):
                            srtm_y_distance = self.srtm_get_y_distance(srtm, lat_index)
                            
                            if abs(srtm_y_distance - distance_from_ref_y) > 3000:
                                # if this srtm point is less than 3000m from current modelgrid point,
                                # just skip it
                                continue
                            
                            for lon_index in xrange(srtm_h):
                                srtm_x_distance = self.srtm_get_x_distance(srtm, lon_index)
                                
                                if abs(srtm_x_distance - distance_from_ref_x) > 3000:
                                    # if this srtm point is less than 3000m from current modelgrid point,
                                    # just skip it
                                    continue
                                
                                distance = compute_distance(srtm_x_distance, srtm_y_distance, distance_from_ref_x, distance_from_ref_y)
                                
                                srtm_elevation = srtm[lat_index, lon_index]
                                delta_elevation = srtm_elevation - hillheight
                                if delta_elevation > (distance * 0.1):
                                    if srtm_elevation > hillheight:
                                        hillheight = srtm_elevation
                            
                    grid.set_hillheight(x, y, hillheight)
        
    
    def save(self, target_path):
        '''
        Save to intermediary format to be used for AERMOD runner.
        JSON maybe?
        '''
        data = {}
        
        elevation_list = []
        hillheight_list = []
        
        for grid in self.model_grids:
            el = grid.elevation.tolist()
            hh = grid.hillheight.tolist()
            elevation_list.append(el)
            hillheight_list.append(hh)
        
        data['elevations'] = elevation_list
        data['hillheights'] = hillheight_list
        
        with open(target_path, 'w') as f:
            json.dump(data, f)
        

def compute_distance(x1, y1, x2, y2):
    dx = x1 - x2;
    dy = y1 - y2;
    return math.sqrt(dx * dx + dy * dy);
    