
import json
import logging

import payload
from openpyxl.reader.excel import load_workbook

class PollutantData():
    def __init__(self, pollutant, conversion_factor, worksheet,
                 row_start, row_end,
                 lat_column, lon_column,
                 x_column, y_column,
                 emission_column):
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


def run(config_file='./config.json'):
    FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('runner')
    logger.setLevel(logging.DEBUG)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    data_file = config['data_file']
    save_path = config['save_path']
    grid_w = config['grid_w']
    grid_h = config['grid_h']
    size_w = config['size_w'] # size of a grid in m
    size_h = config['size_h']
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
                            pollutant['emission_column'])
        pollutants.append(plt)
    
    proc = payload.PayloadThreadProc()
    proc.workbook = load_workbook(data_file)
    proc.source_list = pollutants
    proc.save_path = save_path
    proc.width = grid_w
    proc.height = grid_h
    proc.size_w = size_w
    proc.size_h = size_h
    proc.start()
    
    
if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
