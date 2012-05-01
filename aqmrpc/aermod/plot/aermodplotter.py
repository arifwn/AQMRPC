
import datetime
import logging
import json

import numpy

import utm


class Plotter(object):
    def __init__(self, plt_path, ref_lat, ref_lon):
        self.plt_path = plt_path
        self.plot_title = ''
        self.data = []
        self.timeseries_data = {} # ex: self.timeseries_data[time][y][x]
        self.timeseries_dimension = {}
        self.n_time = 0
        self.interval = datetime.timedelta(seconds=60*60)
        
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
    
    def parse_line(self, plt_line):
        line = plt_line.strip()
        if len(line) == 0:
            return None
        
        if plt_line[0] == '*':
            return None
        
        data_list = line.split()
        data_list = [data.strip() for data in data_list]
        if len(data_list) != 10:
            return None
        
        data_dict = {}
        data_dict['x'] = float(data_list[0])
        data_dict['y'] = float(data_list[1])
        data_dict['conc'] = float(data_list[2])
        data_dict['elev'] = float(data_list[3])
        data_dict['hill'] = float(data_list[4])
        data_dict['zflag'] = float(data_list[5])
        data_dict['interval'] = int(data_list[6].split('-')[0])
        data_dict['group'] = data_list[7]
        
        date_str = data_list[8]
        year = int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])
        hour = int(date_str[6:8]) - 1
        if year > 30:
            # assume it's 19xx
            year += 1900
        else:
            year += 2000
            
        data_dict['date'] = datetime.datetime(year=year, month=month, day=day, hour=hour)
        data_dict['grid_id'] = data_list[9]
        
        return data_dict
    
    def read_data(self):
        logger = logging.getLogger('runner')
        logger.info('reading dataset')
        
        fd = open(self.plt_path, 'r')
        
        # reading title
        first_line = fd.readline()
        self.plot_title = first_line[19:90].strip()
        #logger.info(self.plot_title)
        
        for line in fd:
            data = self.parse_line(line)
            if data is None:
                continue
            self.data.append(data)
            # logger.info('%s', repr(data))
        fd.close()
        if len(self.data) == 0:
            return
        
        # find out data interval
        # assuming consistently spaced dataset
        interval = self.data[0]['interval']
        self.interval = datetime.timedelta(seconds=interval*60*60)
        
        # find out how many dataset are they
        dataset_date = ''
        for data in self.data:
            if dataset_date != data['date'].isoformat():
                dataset_date = data['date'].isoformat()
                self.timeseries_data[dataset_date] = []
                #logger.info(dataset_date)
            self.timeseries_data[dataset_date].append(data)
        self.n_time = len(self.timeseries_data)
        logger.info('dataset: %d', self.n_time)
        
        # find out grid dimension of each dataset
        for date_key in self.timeseries_data.iterkeys():
            data = self.timeseries_data[date_key]
            
            # determine Height
            y = data[0]['y']
            height = 0
            for d in data:
                if y != d['y']:
                    break
                height += 1
            
            # determine Width
            x = None
            width = 0
            for d in data:
                if x == d['x']:
                    break
                if x is None:
                    x = d['x']
                width += 1
                
            #logger.info('%s = %d x %d', date_key, width, height)
            self.timeseries_dimension[date_key] = {'w': width, 'h': height}
            
            # reshape the data so we can access it easily
            # e.g. self.timeseries_data[date_key][y][x]
            tmp = numpy.array(data)
            tmp = tmp.reshape((height, width))
            self.timeseries_data[date_key] = tmp
            #logger.info('%s', self.timeseries_data[date_key][0][0]['date'])
    
    def plot(self, output_dir):
        from mpl_toolkits.basemap import Basemap, cm
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        
        logger = logging.getLogger('runner')
        logger.info('plotting to %s', output_dir)
        
        zone, hem = utm.get_zone_hem(self.ref_lat, self.ref_lon)
        ref_easting, ref_northing = utm.convert_to_utm_fixzone(self.ref_lat, self.ref_lon, zone, hem)
        
        for date_key in self.timeseries_data.iterkeys():
            logger.info('plotting: %s', date_key)
            ## compute map projection coordinates of grid.
            #lats = (srtm['lat'] + (1.0/1200.0) * numpy.indices((1201,1201))[0,:,:])
            #lons = (srtm['lon'] + (1.0/1200.0) * numpy.indices((1201,1201))[1,:,:])
            #x, y = m(lons, lats)
            #im = m.contour(x,y,srtm['data'],levels=clevs,cmap=cm.GMT_relief)
        

def run(config_file='./config.json'):
    FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('runner')
    logger.setLevel(logging.DEBUG)
    
    logger.info('AERMOD Plotter started')
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    plotter = Plotter(config['plt_file'], config['ref_lat'], config['ref_lon'])
    plotter.read_data()
    plotter.plot(config['output_dir'])

if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
    