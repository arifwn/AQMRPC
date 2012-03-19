'''

'''
import os
import glob
import subprocess

from django.template import Context, Template

from aqmrpc import settings

class GradsController(object):
    '''provides api to control GrADS plotting'''
    
    def __init__(self, working_dir, base_gs_str):
        self.working_dir = working_dir
        self.grads_bin = settings.GRADS_BIN
        
        r_path = os.path.dirname(__file__)
        self.base_gs_str = base_gs_str
        self.stdout = os.path.join(self.working_dir, 'grads_stdout.txt')
        self.stderr = os.path.join(self.working_dir, 'grads_stderr.txt')
    
    def run(self, ctl_file, output_dir):
        
        # prepare gs template
        gs_tmp = Template(self.base_gs_str)
        gs = gs_tmp.render(Context({'ctl_file': ctl_file,
                                    'output_dir': output_dir}))
        gs_path = os.path.join(self.working_dir, 'target.gs')
        with open(gs_path, 'w') as gs_file:
            gs_file.write(gs)
        
        
        # prepare output directory
        try:
            os.stat(output_dir)
        except OSError:
            os.mkdir(output_dir)
        
        # empty the output directory
        files = glob.glob(os.path.join(output_dir, '*'))
        for f in files:
            try:
                os.remove(f)
            except OSError:
                pass
        
        # run the gs script
        f_stdout = open(self.stdout, 'a')
        f_stderr = open(self.stderr, 'a')
        
        subprocess.call([self.grads_bin, '-blc', gs_path],
                        cwd=self.working_dir, stdout=f_stdout,
                        stderr=f_stderr)
        f_stdout.close()
        f_stderr.close()
    
    def plot(self, ctl_files):
        
        for i, ctl_file in enumerate(ctl_files):
            # check whether the file really exist
            try:
                os.stat(ctl_file)
            except OSError:
                continue
            
            output_dir = os.path.join(self.working_dir, 'render_%02d' % (i+1))
            self.run(ctl_file, output_dir)
            
    
