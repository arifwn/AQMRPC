'''
Hill Height Generator - Generate AERMOD hill height data from srtm elevation data.
'''

import json
import logging
import math
import os
import zipfile

import numpy

import utm

class ModelGrid(object):
    '''
    Model Grid start from lower left.
    '''
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
    def __init__(self, ref_lat, ref_lon, padding_file=None):
        self.padding_file = padding_file
        self.srtm_data = []
        self.model_grids = []
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        self.zone, self.hemisphere = utm.get_zone_hem(ref_lat, ref_lon)
        self.ref_easting, self.ref_northing = utm.convert_to_utm_fixzone(ref_lat, ref_lon, self.zone, self.hemisphere)
    
    def add_srtm_file(self, file_path, lat, lon, zipped=True):
        logger = logging.getLogger('runner')
        try:
            os.stat(file_path)
            
            if zipped:
                zip_file = zipfile.ZipFile(file_path, 'r')
                zip_file_name = zip_file.namelist()[0]
                hgt_string = zip_file.read(zip_file_name)
                zip_file.close()
            else:
                srtm_file = open(file_path, 'rb')
                hgt_string = srtm_file.read()
                srtm_file.close()
        except OSError:
            logger.error('SRTM File not found: %s', file_path)
            if self.padding_file is None:
                raise OSError('cannot access SRTM File: %s' % file_path)
            
            logger.info('substitute with padding file: %s', self.padding_file)
            zip_file = zipfile.ZipFile(self.padding_file, 'r')
            zip_file_name = zip_file.namelist()[0]
            hgt_string = zip_file.read(zip_file_name)
            zip_file.close()
        
        hgt_data = {}
        # srtm data start from lower left
        hgt_data['data'] = numpy.flipud(((numpy.fromstring(string=hgt_string, dtype='int16')).byteswap()).reshape(1201,1201))
        # this is the coordinate of lower left point
        hgt_data['lat'] = lat
        hgt_data['lon'] = lon
        
        lats = []
        lons = []
        
        for i in xrange(1201):
            point_lat = lat + i * (1.0 / 1200.0)
            point_lon = lon + i * (1.0 / 1200.0)
            
            lats.append(point_lat)
            lons.append(point_lon)
        
        hgt_data['lats'] = lats
        hgt_data['lons'] = lons
        
        hgt_data['path'] = file_path
        self.easting, self.northing = utm.convert_to_utm_fixzone(lat, lon, self.zone, self.hemisphere)
        
        self.srtm_data.append(hgt_data)
    
    def add_model_grid(self, x, y, delta_x, delta_y, w, h, base_elevation=0):
        model_grid = ModelGrid(x, y, delta_x, delta_y, w, h, base_elevation)
        self.model_grids.append(model_grid)
    
    def srtm_get_x_distance(self, srtm, x_pos):
        '''
        Return the x axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        lon = srtm['lon'] + (float(x_pos) / 1200.0)
        easting, northing = utm.convert_to_utm_fixzone(srtm['lat'], lon, self.zone, self.hemisphere)
        return easting - self.ref_easting
    
    def srtm_get_y_distance(self, srtm, y_pos):
        '''
        Return the y axis distance between a point in srtm grid and
        the reference point (in m).
        '''
        lat = srtm['lat'] + (float(y_pos) / 1200.0)
        easting, northing = utm.convert_to_utm_fixzone(lat, srtm['lon'], self.zone, self.hemisphere)
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
    
    def modelgrid_get_lat_lon(self, modelgrid, x, y):
        '''
        Return grid position in degrees.
        '''
        pos_x = self.modelgrid_get_distance_x(modelgrid, x)
        pos_y = self.modelgrid_get_distance_y(modelgrid, y)
        easting  = pos_y + self.ref_easting
        northing  = pos_x + self.ref_northing
        lat, lon = utm.convert_to_latlon(easting, northing, self.zone, self.hemisphere)
        return lat, lon
    
    def modelgrid_get_elevation(self, modelgrid, x, y):
        ''' Obtain elevation for (x,y) position in modelgrid from srtm data. '''
        #pos_x = self.modelgrid_get_distance_x(modelgrid, x)
        #pos_y = self.modelgrid_get_distance_y(modelgrid, y)
        elevation = -9999
        #easting  = pos_y + self.ref_easting
        #northing  = pos_x + self.ref_northing
        #lat, lon = utm.convert_to_latlon(easting, northing, self.zone, self.hemisphere)
        lat, lon = self.modelgrid_get_lat_lon(modelgrid, x, y)
        
        for srtm in self.srtm_data:
            # determine which srtm data contains this coordinate
            if ((srtm['lat'] + 1) >= lat) and (srtm['lat'] <= lat) and ((srtm['lon'] + 1) >= lon) and (srtm['lon'] <= lon):
                # compute correct grid position
                lat_index = int((lat - srtm['lat']) / (1.0 / 1200.0))
                lon_index = int((lon - srtm['lon']) / (1.0 / 1200.0))
                elevation = srtm['data'][lat_index][lon_index]
        
        logger = logging.getLogger('runner')
        logger.debug('elevation: %f, %f, %f', lat, lon, elevation)
        return elevation
    
    def process(self):
        ''' Compute hillheight data from all srtm data. '''
        logger = logging.getLogger('runner')
        
        for grid_n, grid in enumerate(self.model_grids):
            logger.debug('processing grid %i', grid_n)
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
                        #logger.debug('processing srtm (%f, %f)', srtm['lat'], srtm['lon'])
                        srtm_w, srtm_h = srtm['data'].shape
                        
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
                                
                                srtm_elevation = srtm['data'][lat_index, lon_index]
                                delta_elevation = srtm_elevation - hillheight
                                if delta_elevation > (distance * 0.1):
                                    if srtm_elevation > hillheight:
                                        hillheight = srtm_elevation
                            
                    logger.debug('hillheight: %d, %d, %f', x, y, hillheight)
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
    
    def save_image(self, target_path, width=4, height=4):
        from mpl_toolkits.basemap import Basemap, cm
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        
        min_lat = self.ref_lat - (float(height) / 2)
        max_lat = self.ref_lat + (float(height) / 2)
        min_lon = self.ref_lon - (float(width) / 2)
        max_lon = self.ref_lon + (float(width) / 2)
        
        # create the figure and axes instances.
        fig = plt.figure()
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        # setup mercator map projection.
        m = Basemap(llcrnrlon=min_lon,llcrnrlat=min_lat,urcrnrlon=max_lon,urcrnrlat=max_lat,\
                    rsphere=(6378137.00,6356752.3142),\
                    resolution='i',projection='merc',\
                    lat_0=self.ref_lat,lon_0=self.ref_lon,lat_ts=abs(self.ref_lat))
        
        for srtm in self.srtm_data:
            # compute map projection coordinates of grid.
            lats = (srtm['lat'] + (1.0/1200.0) * numpy.indices((1201,1201))[0,:,:])
            lons = (srtm['lon'] + (1.0/1200.0) * numpy.indices((1201,1201))[1,:,:])
            x, y = m(lons, lats)
            clevs = [0,10,30,50,70,100,150,200,250,300,400,500,600,750,1500,2500]
            im = m.contourf(x,y,srtm['data'],clevs,cmap=cm.GMT_globe)
            
            #clevs = [0,50,100,200,400,750,1500,2500]
            #im = m.contour(x,y,srtm['data'],levels=clevs,cmap=cm.GMT_relief)
            
        
        for grid in self.model_grids:
            lat, lon = self.modelgrid_get_lat_lon(grid, 0, 0)
            x1, y1 = m(lon, lat)
            
            lat, lon = self.modelgrid_get_lat_lon(grid, 0, grid.h-1)
            x2, y2 = m(lon, lat)
            
            lat, lon = self.modelgrid_get_lat_lon(grid, grid.w-1, grid.h-1)
            x3, y3 = m(lon, lat)
            
            lat, lon = self.modelgrid_get_lat_lon(grid, grid.w-1, 0)
            x4, y4 = m(lon, lat)
            
            p = Polygon([(x1,y1),(x2,y2),(x3,y3),(x4,y4)],facecolor='red',edgecolor='red',linewidth=2)
            ax.add_patch(p)
        
        # draw coastlines and political boundaries.
        m.drawcoastlines()
        m.drawcountries()
        m.drawstates()
        # draw parallels and meridians. label on left and bottom of map.
        parallels = numpy.arange(0.,80,20.)
        m.drawparallels(parallels,labels=[1,0,0,1])
        meridians = numpy.arange(10.,360.,30.)
        m.drawmeridians(meridians,labels=[1,0,0,1])
        # add colorbar
        cb = m.colorbar(im,"right", size="5%", pad='2%')
        ax.set_title('AERMOD Grid Configuration')
        fig.savefig(target_path)
        

def compute_distance(x1, y1, x2, y2):
    dx = x1 - x2;
    dy = y1 - y2;
    return math.sqrt(dx * dx + dy * dy);

def run(config_file='./config.json'):
    FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('runner')
    logger.setLevel(logging.DEBUG)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    logger.info('latitude / longitude: (%f, %f)', config['ref_lat'], config['ref_lon'])
    hh = HillHeight(config['ref_lat'], config['ref_lon'], os.path.join(config['srtm_dir'], config['padding']))
    
    # add srtm data
    for srtm_info in config['srtm_data']:
        logger.info('adding srtm file: %s (%f, %f)', srtm_info['filename'], srtm_info['lat'], srtm_info['lon'])
        srtm_path = os.path.join(config['srtm_dir'], srtm_info['filename'])
        hh.add_srtm_file(srtm_path, srtm_info['lat'], srtm_info['lon'])
    
    # add model grid data
    for grid_info in config['modelgrid']:
        logger.info('adding model grid: (%d x %d)', grid_info['w'], grid_info['h'])
        hh.add_model_grid(grid_info['x'], grid_info['y'],
                          grid_info['delta_x'], grid_info['delta_y'],
                          grid_info['w'], grid_info['h'],
                          grid_info['base_elevation'])
    
    logger.info('saving image...')
    hh.save_image(config['image_path'], 2, 2)
    
    logger.info('processing...')
    hh.process()
    
    logger.info('saving...')
    hh.save(config['save_path'])
    
    logger.info('done')
    
if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
    