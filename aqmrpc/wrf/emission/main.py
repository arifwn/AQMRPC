
import json
import logging

import namelist_reader
import payload
from openpyxl.reader.excel import load_workbook

class PollutantData():
    def __init__(self, pollutant, conversion_factor, worksheet,
                 row_start, row_end,
                 lat_column, lon_column,
                 x_column, y_column,
                 emission_column,
                 timezone=None,
                 hourly_fluctuation=None):
        self.pollutant = pollutant
        self.conversion_factor = conversion_factor
        self.worksheet = worksheet
        self.row_start = row_start
        self.row_end = row_end
        self.emission_column = emission_column
        self.lat_column = lat_column
        self.lon_column = lon_column
        self.x_column = x_column
        self.y_column = y_column
        
        if timezone is None:
            self.timezone = 0
        else:
            self.timezone = timezone
        
        if hourly_fluctuation is None:
            self.hourly_fluctuation = [
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
            ]
        else:
            # make sure the timezone is sane
            assert((12 >= self.timezone) and (self.timezone >= -12))
            # make sure hourly fluctuation data is sane
            assert(len(hourly_fluctuation) == 24)
            
            local_hourly_fluctuation = []
            tz = self.timezone
            if tz < 0:
                tz = 24 - tz
            
            for i in range(24):
                hour = i + tz
                if hour >= 48:
                    hour = hour - 48
                elif hour >= 24:
                    hour = hour - 24
                local_hourly_fluctuation.append(hourly_fluctuation[hour])
            
            self.hourly_fluctuation = local_hourly_fluctuation


def run(config_file='./config.json'):
    FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('runner')
    logger.setLevel(logging.DEBUG)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    data_file = config['data_file']
    output_dir = config['output_dir']
    namelist_wps = config['namelist_wps']
    grid_w = config['grid_w']
    grid_h = config['grid_h']
    timezone = config['timezone']
    pollutants = []
    
    for pollutant in config['pollutants']:
        logger.info('pollutant: %s', pollutant['pollutant'])
        plt = PollutantData(pollutant['pollutant'],
                            pollutant['conversion_factor'],
                            pollutant['worksheet'],
                            pollutant['row_start'],
                            pollutant['row_end'],
                            pollutant['lat_column'],
                            pollutant['lon_column'],
                            pollutant['x_column'],
                            pollutant['y_column'],
                            pollutant['emission_column'],
                            timezone,
                            pollutant['hourly_fluctuation'])
        pollutants.append(plt)
    
    proc = payload.PayloadThreadProc()
    proc.namelist = namelist_reader.WPSNamelistReader(namelist_wps)
    proc.workbook = load_workbook(data_file)
    proc.source_list = pollutants
    proc.save_dir = output_dir
    proc.width    = grid_w
    proc.height   = grid_h
    proc.run()
    
    
if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
