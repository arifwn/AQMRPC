
"""
Main conversion module
"""

import logging
import os

import numpy

import commons
import data_downscaler
from openpyxl.reader.excel import load_workbook

def opj(path):
    """Convert paths to the platform-specific separator"""
    st = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        st = '/' + st
    return st


class PayloadThreadProc(commons.BaseThreadProc):
    def __init__(self):
        commons.BaseThreadProc.__init__(self)
        self.save_path = ""
        self.eg = [] # per pollutant
        self.workbook = None
        self.width = 0 # grid dimension
        self.height = 0
        self.size_w = 0 # size of a grid in meter
        self.size_h = 0
        self.domain_emiss = [] # dimension: domain, y, x, pollutant
        self.data_list = [] # per pollutant
        self.conv_factor = []
        self.source_list = []
        self.pollutant_list = ['e_so2 ','e_no  ','e_ald ','e_hcho','e_ora2',
                'e_nh3 ','e_hc3 ','e_hc5 ','e_hc8 ', 
                'e_eth ','e_co  ','e_ol2 ','e_olt ','e_oli ','e_tol ','e_xyl ',
                'e_ket ','e_csl ','e_iso ','e_pm25i','e_pm25j', 
                'e_so4i','e_so4j','e_no3i','e_no3j','e_orgi','e_orgj','e_eci', 
                'e_ecj','e_pm10']
        self.additional_pollutan_list = [] # for custon pollutant id, not used for now
        self.pollutant_str = []

    def process_pollutant_list(self):
        logger = logging.getLogger('runner')
        logger.info('pollutant processing start')
        
        for source in self.source_list:
            logger.info('processing %s', source.pollutant)
            self.data_list.append([])
            self.conv_factor.append(source.conversion_factor)
            self.pollutant_str.append(source.pollutant)
            try:
                self.pollutant_list.index(source.pollutant)
            except:
                self.additional_pollutan_list.append(source.pollutant)
            
        logger.info('debug: Pollutant processing end')

    def load_worksheet_data(self):
        logger = logging.getLogger('runner')
        logger.info('worksheet processing start')
        
        sheet_names = self.workbook.get_sheet_names()
        
        for i, source in enumerate(self.source_list):
            logger.info('Reading data for %s from %s', source.pollutant, sheet_names[source.worksheet])
            sheet = self.workbook.worksheets[source.worksheet]
            range_x_str = "{0}{1}:{0}{2}".format(source.x_column, source.row_start, source.row_end)
            range_y_str = "{0}{1}:{0}{2}".format(source.y_column, source.row_start, source.row_end)
            range_lat_str = "{0}{1}:{0}{2}".format(source.lat_column, source.row_start, source.row_end)
            range_lon_str = "{0}{1}:{0}{2}".format(source.lon_column, source.row_start, source.row_end)
            range_emiss_str = "{0}{1}:{0}{2}".format(source.emission_column, source.row_start, source.row_end)
            cells_x = sheet.range(range_x_str)
            cells_y = sheet.range(range_y_str)
            cells_lat = sheet.range(range_lat_str)
            cells_lon = sheet.range(range_lon_str)
            cells_emiss = sheet.range(range_emiss_str)
            
            data_len = len(cells_x)
            logger.info('saving list data...')
            for j in range(data_len):
                tmp_x = cells_x[j][0].value
                tmp_y = cells_y[j][0].value
                tmp_lat = cells_lat[j][0].value
                tmp_lon = cells_lon[j][0].value
                tmp_conc = cells_emiss[j][0].value
                tmp_rowdata = data_downscaler.RowData(tmp_lat, tmp_lon, tmp_x, tmp_y, tmp_conc)
                self.data_list[i].append(tmp_rowdata)
            
            logger.info('sorting list data...')
            self.data_list[i].sort(data_downscaler.compare_rowdata_m)
        
        logger.info('worksheet processing end')
        
    def save_emission(self):
        logger = logging.getLogger('runner')
        logger.info('Emission save start')
        
        emission_name = ['e_so2 ','e_no  ','e_ald ','e_hcho','e_ora2',
                'e_nh3 ','e_hc3 ','e_hc5 ','e_hc8 ', 
                'e_eth ','e_co  ','e_ol2 ','e_olt ','e_oli ','e_tol ','e_xyl ',
                'e_ket ','e_csl ','e_iso ','e_pm25i','e_pm25j', 
                'e_so4i','e_so4j','e_no3i','e_no3j','e_orgi','e_orgj','e_eci', 
                'e_ecj','e_pm10']
        
        with open(self.save_path, 'w') as f:
            # for each pollutant
            for i, plt in enumerate(self.pollutant_str):
                
                # location card
                x = 0
                y = 0
                for source_id, row_data in enumerate(self.data_list[i]):
                    f.write("    SO LOCATION %s%05i AREA %5s %5s\n" % (plt, source_id, x * self.size_w, y * self.size_h));
                    x += 1
                    if x >= self.width:
                        x = 0
                        y += 1
                
                f.write("\n")
                
                # source parameter
                x = 0
                y = 0
                conversion_factor = self.conv_factor[i]
                for source_id, row_data in enumerate(self.data_list[i]):
                    emission_rate = row_data.data * conversion_factor # g / (second . m2)
                    release_height = 0
                    f.write("    SO SRCPARAM %s%05i %s %f %d %d\n" % (plt, source_id, 
                                                                emission_rate,
                                                                release_height,
                                                                self.size_w,
                                                                self.size_h));
                    x += 1
                    if x >= self.width:
                        x = 0
                        y += 1
                
        logger.info('Emission save end')
    
    def run(self):
        self.process_pollutant_list()
        self.load_worksheet_data()
        self.save_emission()
        self.done()
