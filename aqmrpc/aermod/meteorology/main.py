
'''
Merge File Format:

* daily master header record:
    READ( ) year, month, day, j_day, n_ua, n_sfc, n_os
    FORMAT (7(I8,1X))
    where:
    j_day = the Julian date for year/month/day.
    n_ua = number of NWS upper air observations.
    n_sfc = number of NWS surface observations.
    n_os = number of site-specific observations.
    
    UNDOCUMENTED FIELDS: UADATA, SFDATA, OSDATA
    

* Upper Air Record
    READ( ) year, month, day, hour, # levels
    FORMAT (1X, 4I2, I5)

    Upper air sounding level data (if # levels > 0), repeated # levels times.
    READ( ) UAPR, UAHT, UATT, UATD, UAWD, UAWS
    FORMAT (6(1X,I6))
    where:
    UAPR = atmospheric pressure (millibars), multiplied by 10
    UAHT = height above ground level (meters)
    UATT = dry bulb temperature (C), multiplied by 10
    UATD = dew temperature (C), multiplied by 10
    UAWD = wind direction (degrees from north)
    UAWS = wind speed (meters/second), multiplied by 10

* Surface Air Record
    The first record of a surface observation is written as follows:
    year, month, day, hour, ASOSFLG
    (4I2,A1)
    where:
    ASOSFLG = flag indicating whether observation is ASOS ('A') or
             non-ASOS ('N')
    
    The second record of a surface observation is written as follows:
    PRCP, SLVP, PRES, CLHT, TSKC, C2C3, CLC1, CLC2, CLC3, CLC4
    (4(1X,I5), 6(1X,I5.5)
    where:
    PRCP = precipitation amount (millimeters), multiplied by 1000
    SLVP = sea level pressure (millibars), multiplied by 10
    PRES = station pressure (millibars), multiplied by 10
    CLHT = cloud ceiling height (kilometers), multiplied by 10
    TSKC = sky cover, total//opaque (tenths//tenths)
    C2C3 = sky cover, 2//3 layers (tenths//tenths)
    CLCn = sky condition//coverage, layer n = 1,2,3,4 (- -//tenths)

    The third record of a surface observation is written as follows:
    CLT1, CLT2, CLT3, CLT4, PWTH, HZVS, TMPD, TMPW, DPTP, RHUM, WDIR, WSPD
    (8X, 5(1X,I5.5), 7(1X,I5),2X)
    where:
    CLTn = cloud type//height, n=1,2,3,4 (- -//kilometers), multiplied by 10
    PWTH = present weather, liquid//frozen (no units, see codes below)
    HZVS = horizontal visibility (kilometers), multiplied by 10
    TMPD = dry bulb temperature (C), multiplied by 10
    TMPW = wet bulb temperature (C), multiplied by 10
    DPTP = dew-point temperature (C), multiplied by 10
    RHUM = relative humidity (percent)
    WDIR = wind direction (tens of degrees from north)
    WSPD = wind speed (meters/second), multiplied by 10


'''

import json
import os
import logging
import datetime
import math
from cStringIO import StringIO

import numpy


class WRFtoAERMOD(object):
    def __init__(self, config):
        self.output_path = config['output_path']
        
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
        
        self.vert_pressure = numpy.array([])
        self.vert_seapressure = numpy.array([])
        self.vert_temp = numpy.array([])
        self.vert_windir = numpy.array([])
        self.vert_windspeed = numpy.array([])
        self.vert_elevation = numpy.array([])
        self.vert_dewtemp = numpy.array([])
        self.vert_height = numpy.array([])
        
        self.sfc_pressure = numpy.array([])
        self.sfc_seapressure = numpy.array([])
        self.sfc_temp = numpy.array([])
        self.sfc_dewtemp = numpy.array([])
        self.sfc_relhumid = numpy.array([])
        self.sfc_windir = numpy.array([])
        self.sfc_windspeed = numpy.array([])
        
        self.start_time = datetime.datetime(year=config['start_time']['year'],
                                            month=config['start_time']['month'],
                                            day=config['start_time']['day'],
                                            hour=config['start_time']['hour'],
                                            minute=config['start_time']['minute'],
                                            second=config['start_time']['second'])
        self.interval = datetime.timedelta(seconds=60*60)
        self.timezone = config['timezone']
        
        self.time_length = config['time_length']
        self.zsize = config['zsize']
        self.station_elevation = 0.0
        
        self.station_id = config['location']['id']
        self.lat, self.lon = clean_latlon(config['location']['lat'], config['location']['lon'])
        if self.lat > 0:
            self.lat_str = '%.2fN' % self.lat
        else:
            self.lat_str = '%.2fS' % abs(self.lat)
        if self.lon > 0:
            self.lon_str = '%.2fE' % self.lon
        else:
            self.lon_str = '%.2fW' % abs(self.lon)
    
    def get_numeric_list(self, file_path):
        output = []
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    num = float(line.strip())
                except ValueError:
                    continue
                
                output.append(num)
        output_arr = numpy.array(output)
        return output_arr
    
    def read_data(self):
        logger = logging.getLogger('runner')
        
        self.vert_pressure = self.get_numeric_list(self.vert_pressure_path)
        self.vert_seapressure = self.get_numeric_list(self.vert_seapressure_path)
        self.vert_temp = self.get_numeric_list(self.vert_temp_path)
        self.vert_windir = self.get_numeric_list(self.vert_windir_path)
        self.vert_windspeed = self.get_numeric_list(self.vert_windspeed_path)
        self.vert_elevation = self.get_numeric_list(self.vert_elevation_path)
        self.vert_dewtemp = self.get_numeric_list(self.vert_dewtemp_path)
        self.vert_height = self.get_numeric_list(self.vert_height_path)
        
        # reshape vertical data
        self.vert_pressure = self.vert_pressure.reshape((self.time_length, self.zsize))
        self.vert_seapressure = self.vert_seapressure.reshape((self.time_length, self.zsize))
        self.vert_temp = self.vert_temp.reshape((self.time_length, self.zsize))
        self.vert_windir = self.vert_windir.reshape((self.time_length, self.zsize))
        self.vert_windspeed = self.vert_windspeed.reshape((self.time_length, self.zsize))
        self.vert_elevation = self.vert_elevation.reshape((self.time_length, self.zsize))
        self.vert_dewtemp = self.vert_dewtemp.reshape((self.time_length, self.zsize))
        self.vert_height = self.vert_height.reshape((self.time_length, self.zsize))
        logger.info('new_arr: %s', self.vert_pressure)
        
        self.sfc_pressure = self.get_numeric_list(self.sfc_pressure_path)
        self.sfc_seapressure = self.get_numeric_list(self.sfc_seapressure_path)
        self.sfc_temp = self.get_numeric_list(self.sfc_temp_path)
        self.sfc_dewtemp = self.get_numeric_list(self.sfc_dewtemp_path)
        self.sfc_relhumid = self.get_numeric_list(self.sfc_relhumid_path)
        self.sfc_windir = self.get_numeric_list(self.sfc_windir_path)
        self.sfc_windspeed = self.get_numeric_list(self.sfc_windspeed_path)
        
        try:
            self.station_elevation = self.vert_elevation[0][0]
        except Exception, e:
            logger.error('cannot obtain station elevation: %s', e)
        logger.info('elev: %s', self.station_elevation)
    
    def save(self, fd):
        logger = logging.getLogger('runner')
        
        fd.write('*%A  UPPERAIR \n')
        fd.write('*@A     LOCATION %d %s %s %d %.2f \n' % (self.station_id, self.lon_str, self.lat_str, self.timezone, self.station_elevation))
        fd.write('*%ASURFACE \n')
        fd.write('*@A     LOCATION %d %s %s %d %.2f \n' % (self.station_id, self.lon_str, self.lat_str, self.timezone, self.station_elevation))
        fd.write('*** EOH: END OF MERGE HEADERS \n')
        
        # for each day
        #   write upper air header
        #   for each hour
        #      save hourly upper air data
        #   write surface air data
        #   for each hour
        #   save hourly surface air data
        
        start_time = self.start_time
        end_time = start_time + (self.time_length - 1) * self.interval
        logger.info('start: %s end: %s', start_time, end_time)
        delta_time = end_time - start_time
        n_day = delta_time.days + 1
        
        hour_i = 0
        current_time = start_time
        current_day = start_time.day
        
        for day_i in range(n_day + 1):
            if current_time > end_time:
                break
            
            logger.info('saving day: %s', day_i)
            next_day = current_time + datetime.timedelta(seconds=24*60*60)
            next_day = datetime.datetime(year=next_day.year,
                                         month=next_day.month,
                                         day=next_day.day)
            
            hour_left = int((next_day - current_time).total_seconds() / (60 * 60))
            if hour_left > (self.time_length - hour_i):
                hour_left = (self.time_length - hour_i)
            logger.info('%s, %d', hour_left, self.time_length - hour_i)
            
            year = current_time.year % 100
            month = current_time.month
            day = current_time.day
            j_day = get_julian_date(current_time)
            n_upper_air = hour_left
            start_upper_air = 0
            end_upper_air = hour_left
            n_surface_air = hour_left
            n_observe = 0
            n_etc = 0
            fd.write('%8i %8i %8i %8i %8i %8i %8i %8i %8i %8i\n' % (year, month, day, j_day,
                                                           n_upper_air,
                                                           start_upper_air,
                                                           end_upper_air,
                                                           n_surface_air,
                                                           n_observe,
                                                           n_etc))
            
            upper_air_buff = StringIO()
            surface_air_buff = StringIO()
            
            while True:
                if current_time > end_time:
                    break
                
                logger.info('hour: %d, current_time: %s current_day: %s', hour_i, current_time, current_day)
                # HACK: since AERMOD day start from 1:00 am, our time will be shifted by 1 hour
                # I don't know if this behavior is correct
                
                data_hour = current_time.hour + 1
                
                # upper air
                upper_air_buff.write('%8i %8i %8i %8i %8i\n' % (year, month, day, data_hour, self.zsize))
                
                # we need to save the data in 10 column format, so we need a tmp list
                tmp_list = []
                for z in range(self.zsize):
                    tmp_list.append((self.vert_pressure[hour_i][z] / 100.0) * 10)
                    tmp_list.append(self.vert_height[hour_i][z])
                    tmp_list.append((self.vert_temp[hour_i][z] - 273.15) * 10)
                    tmp_list.append((self.vert_dewtemp[hour_i][z] - 273.15) * 10)
                    
                    winddir = math.ceil(self.vert_windir[hour_i][z])
                    tmp_list.append(winddir)
                    
                    windspeed = self.vert_windspeed[hour_i][z]
                    if windspeed < 0.1:
                        windspeed = 0.1
                    windspeed = windspeed * 10
                    tmp_list.append(windspeed)
                    
                counter = 1
                for item in tmp_list:
                    upper_air_buff.write('%8i ' % item)
                    if counter == 10:
                        upper_air_buff.write('\n')
                        counter = 0
                    counter += 1
                upper_air_buff.write('\n')
                
                # surface air
                surface_air_buff.write('%8i %8i %8i %8i N\n' % (year, month, day, data_hour))
                
                # we need to save the data in 10 column format, so we need a tmp list
                tmp_list = []
                
                precipitation = -9 # don't know yet
                sea_level_pressure = self.sfc_seapressure[hour_i] * 10
                pressure = (self.sfc_pressure[hour_i] / 100) * 10
                cloud_ceiling_height = 300
                sky_cover = 0
                sky_cover_layer_2_3 = 9999
                sky_cond_1 = 300
                sky_cond_2 = 300
                sky_cond_3 = 300
                sky_cond_4 = 300
                cloud_type_1 = 300
                cloud_type_2 = 9999
                cloud_type_3 = 0
                cloud_type_4 = 99
                present_weather = 999
                horizontal_visibility = 99999
                dry_bulb_temp = ((self.sfc_temp[hour_i] - 273.15) * 10)
                wet_bult_temp = 999
                dew_temp = ((self.sfc_dewtemp[hour_i] - 273.15) * 10)
                rel_humidity = self.sfc_relhumid[hour_i]
                wind_dir = math.ceil(self.sfc_windir[hour_i] / 10)
                windspeed = self.sfc_windspeed[hour_i]
                if windspeed < 0.1:
                    windspeed = 0.1
                windspeed = windspeed * 10
                
                tmp_list.append(precipitation)
                tmp_list.append(sea_level_pressure)
                tmp_list.append(pressure)
                tmp_list.append(cloud_ceiling_height)
                tmp_list.append(sky_cover)
                tmp_list.append(sky_cover_layer_2_3)
                tmp_list.append(sky_cond_1)
                tmp_list.append(sky_cond_2)
                tmp_list.append(sky_cond_3)
                tmp_list.append(sky_cond_4)
                tmp_list.append(cloud_type_1)
                tmp_list.append(cloud_type_2)
                tmp_list.append(cloud_type_3)
                tmp_list.append(cloud_type_4)
                tmp_list.append(present_weather)
                tmp_list.append(horizontal_visibility)
                tmp_list.append(dry_bulb_temp)
                tmp_list.append(wet_bult_temp)
                tmp_list.append(dew_temp)
                tmp_list.append(rel_humidity)
                tmp_list.append(wind_dir)
                tmp_list.append(windspeed)
                
                counter = 1
                for item in tmp_list:
                    surface_air_buff.write('%8i ' % item)
                    if counter == 10:
                        surface_air_buff.write('\n')
                        counter = 0
                    counter += 1
                if (hour_i + 1) < self.time_length:
                    surface_air_buff.write('\n')
                
                hour_i += 1
                current_time += self.interval
                prev_day = current_day
                current_day = current_time.day
                if current_day != prev_day:
                    break
            
            fd.write(upper_air_buff.getvalue())
            fd.write(surface_air_buff.getvalue())
    
    def save_to_output(self):
        with open(self.output_path, 'w') as f:
            self.save(f)


def get_julian_date(time):
    return time.timetuple().tm_yday

def clean_lon(lon):
    '''
    Convert longitude so that it always between 180 to -180.
    '''
    if lon >= 180:
        if ((lon / 180.0) % 2) == 0:
            lon = lon % 360
        else:
            lon = (int(lon / 180.0) * (lon % 180)) - 180
    return lon

def clean_latlon(lat, lon):
    lon = clean_lon(lon)
    return lat, lon

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
    processor.save_to_output()
    

if __name__ == '__main__':
    # use config file path as command line argument
    import sys
    
    config_file = './config.json'
    #if len(sys.argv) < 2:
    #    exit(-1)
    #config_file = sys.argv[1]
    
    run(config_file)
    
    