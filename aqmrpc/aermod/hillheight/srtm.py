
import zipfile
import numpy
import Image

def read_srtm(zip_path):
    zip_file = zipfile.ZipFile(zip_path, 'r')
    zip_file_name = zip_file.namelist()[0]
    hgt_string = zip_file.read(zip_file_name)
    zip_file.close()
    return numpy.flipud(((numpy.fromstring(string=hgt_string, dtype='int16')).byteswap()).reshape(1201,1201))

def save_image(srtm_data, target):
    im = Image.new('RGB', srtm_data.shape)
    
    w, h = srtm_data.shape	
    for lat in xrange(w):
        for lon in xrange(h):
            height = srtm_data[lat][lon]
            hue = (float(height) / 2000.0) * 200
            color_r = hue + 55
            color_g = hue + 55
            color_b = hue + 55
            if height == 0:
                color_b = 200
            
            if color_r > 255:
                color_r = 255
            if color_g > 255:
                color_g = 255
            if color_b > 255:
                color_b = 255
            
            im.putpixel((lon, (h - 1) - lat), (int(color_r), int(color_g), int(color_b)))
    im.save(target)

if __name__ == '__main__':
    target_path = 'srtm/S06E105.hgt.zip'
    hgt = read_srtm(target_path)  
    
    print "S06E105", hgt[0][0]
    print "S06E106", hgt[0][1200]
    print "S05E105", hgt[1200][0]
    print "S05E106", hgt[1200][1200]
    
    save_image(hgt, 'test.png')
    