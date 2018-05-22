# -*- coding: utf-8 -*-
"""
Created on Fri May 11 15:32:17 2018

@author: ge72tih
"""

import os, sys
import numpy as np
sys.path.append(r"H:\TUM-PC\Dokumente\Projects\campbell_diagram\ansys_apdl_wrapper\ansys_apdl_wrapper")

from ansys_apdl_wrapper import pyAPDL

local_folder = os.getcwd()
base_file_path = r'ansys_apdl_warpper\base_files'
filename = 'base_apdl_script.dat'
filepath = os.path.join(local_folder,base_file_path,filename)
temp_folder_prefix = 'rot_'

apdl = pyAPDL(filepath,temp_folder_prefix)
apdl.set_ansys_apdl_path(r'C:\Program Files\ANSYS Student\v182\ansys\bin\winx64\ansys182.exe')

def calc_freq(rot_speed):
    
    var_dict = {}
    var_dict['apdl_pre_file'] = 'prep_case1'
    var_dict['file_directory'] = base_file_path
    var_dict['number_of_harmonics'] = 2
    var_dict['number_of_modes'] = 4
    var_dict['rotational_speed'] = rot_speed

    folder = os.path.join(local_folder,'simulations3')

    apdl.update_input_variables(var_dict)
    apdl.write_apdl_script(folder,rot_speed)

    
    apdl.run_simulation()

    f = apdl.read_frequencies()
    return f

rot_list = np.arange(50,100,50)
freq_list = []
for rot in rot_list:
    freq = calc_freq(rot)
    freq_list.append(freq)