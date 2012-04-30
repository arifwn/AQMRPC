
import json
import os
import logging
import datetime


class WRFtoAERMOD(object):
    def __init__(self, config):
        self.output_path = os.path.join(config['output_dir'], config['output'])
        
        self.vert_pressure_path = os.path.join(config['input_dir'], config['upper_air']['pressure'])
        self.vert_seapressure_path = os.path.join(config['input_dir'], config['upper_air']['seapressure'])
        self.vert_temp_path = os.path.join(config['input_dir'], config['upper_air']['temp'])
        self.vert_windir_path = os.path.join(config['input_dir'], config['upper_air']['windir'])
        self.vert_windspeed_path = os.path.join(config['input_dir'], config['upper_air']['windspeed'])
        self.vert_elevation_path = os.path.join(config['input_dir'], config['upper_air']['elevation'])
        self.vert_dewtemp_path = os.path.join(config['input_dir'], config['upper_air']['dewtemp'])
        self.vert_height_path = os.path.join(config['input_dir'], config['upper_air']['height'])
        
        self.sfc_pressure_path = os.path.join(config['input_dir'], config['surface']['pressure'])
        self.sfc_seapressure_path = os.path.join(config['input_dir'], config['surface']['seapressure'])
        self.sfc_temp_path = os.path.join(config['input_dir'], config['surface']['temp'])
        self.sfc_dewtemp_path = os.path.join(config['input_dir'], config['surface']['dewtemp'])
        self.sfc_relhumid_path = os.path.join(config['input_dir'], config['surface']['relhumid'])
        self.sfc_windir_path = os.path.join(config['input_dir'], config['surface']['windir'])
        self.sfc_windspeed_path = os.path.join(config['input_dir'], config['surface']['windspeed'])
        
        self.vert_pressure = []
        self.vert_seapressure = []
        self.vert_temp = []
        self.vert_windir = []
        self.vert_windspeed = []
        self.vert_elevation = []
        self.vert_dewtemp = []
        self.vert_height = []
        
        self.sfc_pressure = []
        self.sfc_seapressure = []
        self.sfc_temp = []
        self.sfc_dewtemp = []
        self.sfc_relhumid = []
        self.sfc_windir = []
        self.sfc_windspeed = []
        
        self.start_time = datetime.datetime(year=config['start_time']['year'],
                                            month=config['start_time']['month'],
                                            day=config['start_time']['day'],
                                            hour=config['start_time']['hour'],
                                            minute=config['start_time']['minute'],
                                            second=config['start_time']['second'])
        self.interval = datetime.timedelta(seconds=60*60)
        
        self.time_length = config['time_length']
        self.zsize = config['zsize']
    
    def get_numeric_list(self, file_path):
        output = []
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    num = float(line.strip())
                except ValueError:
                    continue
                
                output.append(num)
        return output
    
    def read_data(self):
        self.vert_pressure = self.get_numeric_list(self.vert_pressure_path)
        self.vert_seapressure = self.get_numeric_list(self.vert_seapressure_path)
        self.vert_temp = self.get_numeric_list(self.vert_temp_path)
        self.vert_windir = self.get_numeric_list(self.vert_windir_path)
        self.vert_windspeed = self.get_numeric_list(self.vert_windspeed_path)
        self.vert_elevation = self.get_numeric_list(self.vert_elevation_path)
        self.vert_dewtemp = self.get_numeric_list(self.vert_dewtemp_path)
        self.vert_height = self.get_numeric_list(self.vert_height_path)
        
        self.sfc_pressure = self.get_numeric_list(self.sfc_pressure_path)
        self.sfc_seapressure = self.get_numeric_list(self.sfc_seapressure_path)
        self.sfc_temp = self.get_numeric_list(self.sfc_temp_path)
        self.sfc_dewtemp = self.get_numeric_list(self.sfc_dewtemp_path)
        self.sfc_relhumid = self.get_numeric_list(self.sfc_relhumid_path)
        self.sfc_windir = self.get_numeric_list(self.sfc_windir_path)
        self.sfc_windspeed = self.get_numeric_list(self.sfc_windspeed_path)
    


def hptoheight(pressure, surface_elevation):
    '''
    Convert atmospheric pressure from hectopascal to meter from surface.
    '''
    return 44331.5 - (4946.62 * ((pressure)**0.1902632)) - surface_elevation    

def run(config_file='./config.json'):
    FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(lineno)d] %(message)s'
    logging.basicConfig(format=FORMAT)
    logger = logging.getLogger('runner')
    logger.setLevel(logging.DEBUG)
    
    logger.info('using config file: %s', config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    processor = WRFtoAERMOD(config)
    processor.read_data()
    

if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
    
    