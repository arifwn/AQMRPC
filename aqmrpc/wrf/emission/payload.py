
"""
Modul konversi utama
"""

import logging
import os

import numpy

import fortranfile
import data_downscaler
import namelist_reader
import domain_data
import pupynere
import commons
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
        self.save_dir = ""
        self.namelist = None
        self.maxdom = 0
        self.domains = []
        self.eg = [] # per pollutant
        self.workbook = None
        self.width = 0
        self.height = 0
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
    
    def load_namelist(self):
        logger = logging.getLogger('runner')
        logger.info('namelist processing start')
        logger.info('reading namelist...')
        self.maxdom = self.namelist.maxdom
        for i in range(self.maxdom):
            parent = self.namelist.parent_id[i] - 1
            domain = None
            logger.info('Reading domain %i', (i + 1))
            if i == 0:
                # top level domain
                domain = domain_data.TopDomain()
                domain.lat = self.namelist.ref_lat
                domain.lon = self.namelist.ref_lon
                domain.w   = self.namelist.e_we[0] - 1
                domain.h   = self.namelist.e_sn[0] - 1
                domain.dx  = self.namelist.dom_dx
                domain.dy  = self.namelist.dom_dy
                domain.process_boundary()
                logger.info('Top Domain')
            else:
                # TODO: sibling subdomain support
                logger.info('subDomain start, parent %i', parent)
                domain = domain_data.SubDomain(self.domains[parent], self.namelist.i_parent_start[i], 
                                               self.namelist.j_parent_start[i], 
                                               self.namelist.parent_grid_ratio[i])
                
                domain.w   = self.namelist.e_we[i] - 1
                domain.h   = self.namelist.e_sn[i] - 1
                domain.process_boundary()
                logger.info('debug: SubDomain end, parent %i', parent)
            
            self.domains.append(domain)
            
        logger.info('total domain: %i', len(self.domains))
        logger.info('namelist processing end')
        
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
        
    def create_emission_group(self):
        logger = logging.getLogger('runner')
        logger.info('Emission Group processing start')
        
        for n, data in enumerate(self.data_list):
            eg = data_downscaler.EmissGroup()
            eg.set_dimension(self.width, self.height)
            eg.conv_factor = self.conv_factor[n]
            i = 0
            for y in range(self.height):
                for x in range(self.width):
                    row_data = self.data_list[n][i]
                    tmp = data_downscaler.EmissData()
                    tmp.conc = row_data.data
                    tmp.lat = row_data.lat
                    tmp.lon = row_data.lon
                    tmp.x = row_data.x
                    tmp.y = row_data.y
                    eg.append_data(tmp)
                    i = i + 1
            
            eg.compute_boundary()
            self.eg.append(eg)            
        
        
        logger.info('Emission Group processing end')
    
    def compute_emission(self):
        logger = logging.getLogger('runner')
        logger.info('Emission interpolation start')
        
        for n_dom, domain in enumerate(self.domains):
            domain_dat = []
            for y in range(domain.h):
                y_dat = []
                for x in range(domain.w):
                    x_dat = []
                    ll, tr = domain.get_cell_boundary_latlon(x, y)
                    for n_eg, eg in enumerate(self.eg):
                        conc = eg.get_average_conc_latlon(ll, tr)
                        logger.info('Emission for Domain %i: %i,%i conc %f', n_dom+1, x, y, conc)
                        x_dat.append(conc)
                    y_dat.append(x_dat)
                domain_dat.append(y_dat)
            self.domain_emiss.append(domain_dat)
        
        logger.info('emission interpolation end')
    
    def save_emission(self):
        logger = logging.getLogger('runner')
        logger.info('Emission save start')
        
        emission_name = ['e_so2 ','e_no  ','e_ald ','e_hcho','e_ora2',
                'e_nh3 ','e_hc3 ','e_hc5 ','e_hc8 ', 
                'e_eth ','e_co  ','e_ol2 ','e_olt ','e_oli ','e_tol ','e_xyl ',
                'e_ket ','e_csl ','e_iso ','e_pm25i','e_pm25j', 
                'e_so4i','e_so4j','e_no3i','e_no3j','e_orgi','e_orgj','e_eci', 
                'e_ecj','e_pm10']
        
        n_emiss = len(emission_name)
        emission_name_str = ''
        for em in emission_name:
            emission_name_str += '%-9s' % em
        
        for n in range(self.maxdom):
            domain = self.domains[n]
            filename_1 = opj('{0}/wrfem_00to12z_d{1:0>2}'.format(self.save_dir, n+1))
            filename_2 = opj('{0}/wrfem_12to24z_d{1:0>2}'.format(self.save_dir, n+1))
            
            width = domain.w # e_we - 1 -> IX2
            height = domain.h # e_sn - 1 -> JX3
            n_layer = 1 # 0 < kemit < e_vert -> KX or z-level
            
            # file 1
            f = fortranfile.FortranFile(filename_1, endian='>', mode='w')
            f.writeInts([n_emiss])
            f.writeString(emission_name_str)
            
            for hour in range(1,13):
                f.writeInts([hour])
                for emission_num in range(1, n_emiss+1):
                    for p, plt in enumerate(self.pollutant_str):
                        logger.info('saving frame [1] %i %i %s', hour, emission_num, plt)
                        b = numpy.ndarray([], numpy.float32)
                        b.resize((width * n_layer * height,))
                        current_pollutant = self.pollutant_list[emission_num - 1]
                        if plt.lower() == current_pollutant.strip():
                            for z in range(n_layer):
                                for y in range(height):
                                    for x in range(width):
                                        factor = self.source_list[p].hourly_fluctuation[hour-1]
                                        b[x + (n_layer * width * y) + (width * z)] = self.domain_emiss[n][y][x][p] * factor
                                        # logger.info('saving %s; factor: %f; conc: %f', plt, factor, self.domain_emiss[n][y][x][p])
                        f.writeReals(b)
            f.close()
            
            
            # file 2
            f = fortranfile.FortranFile(filename_2, endian='>', mode='w')
            f.writeInts([n_emiss])
            f.writeString(emission_name_str)
            
            for hour in range(13, 25):
                f.writeInts([hour])
                for emission_num in range(1, n_emiss+1):
                    for p, plt in enumerate(self.pollutant_str):
                        logger.info('saving frame [2] %i %i %s', hour, emission_num, plt)
                        b = numpy.ndarray([], numpy.float32)
                        b.resize((width * n_layer * height,))
                        current_pollutant = self.pollutant_list[emission_num - 1]
                        if plt.lower() == current_pollutant.strip():
                            for z in range(n_layer):
                                for y in range(height):
                                    for x in range(width):
                                        factor = self.source_list[p].hourly_fluctuation[hour-1]
                                        b[x + (n_layer * width * y) + (width * z)] = self.domain_emiss[n][y][x][p] * factor
                                        # logger.info('saving %s; factor: %f; conc: %f', plt, factor, self.domain_emiss[n][y][x][p])
                        f.writeReals(b)
            f.close()
            
        logger.info('Emission save end')
    
    def run(self):
        self.load_namelist()
        self.process_pollutant_list()
        self.load_worksheet_data()
        self.create_emission_group()
        self.compute_emission()
        self.save_emission()
        self.done()
