
import os
import subprocess
from shutil import copyfile
import pandas as pd
import copy 

code_labels = [ 'variables',
                'static_prep',
                'static_solu',
                'static_post',
                'modal_prep',
                'modal_solu',
                'modal_post']


class pyAPDL():
    def __init__(self,filepath=None,temp_folder_prefix='temp_'):
        ''' This class can read, modify and write apdl scripts
            The filepath is a base apdl script that will be modified

            The filepath must contain some labels in order to split the 
            script in small parts. The labels are:

            '!$variables$',
            '!$static_prep$',
            '!$static_solu$',
            '!$static_post$',
            '!$modal_prep$',
            '!$modal_solu$',
            '!$modal_post$'

        '''

        self.codelines_dict = {}
        self.filepath = filepath
        self.temp_folder_prefix = temp_folder_prefix
        self.results_dict = {}

        if filepath is not None:
            self.split_base_file_in_dict(filepath)

    def split_base_file_in_dict(self,filepath):
        
        f = open(filepath)

        for label in code_labels:
            self.codelines_dict[label] = []

        num_of_labels = len(code_labels)
        label_counter = 0
        for line in f.readlines():
            if label_counter<num_of_labels:
                is_label = line.find( code_labels[label_counter])
                if is_label>0:
                    code_label = code_labels[label_counter]
                    label_counter += 1
            
            if line!='\n':
                self.codelines_dict[code_label].append(line)

    def update_input_variables(self,var_dict):
        ''' This method create a new dict "self.updated_codelines_dict" 
        with the updated variables based on var_dict which contain keys with variables 
        names and values with variables values.

        argument:
            var_dict : dict
                dict which contain keys with variables names and values with variables values.

            self.codelines_dict : dict
                internal object variable with a dict of the APDL command lines

        return 
            self.updated_codelines_dict : dict
                dict with APDL command lines with updated variables

        '''

        self.var_dict = var_dict
        self.updated_codelines_dict = copy.deepcopy(self.codelines_dict)
        var_lines_dict = self.updated_codelines_dict['variables']
        for var_key in var_dict:
            for i,line in enumerate(var_lines_dict):
                is_label = line.find(var_key)
                if is_label>0:
                    val = var_dict[var_key]
                    if isinstance(val,str):
                        #new_str = val.replace('\\\\','\\') # replace python path to windows path
                        new_line = line.replace('$' + var_key + '$',"'" + val + "'")
                    else:
                        new_line = line.replace('$' + var_key + '$',str(val) )

                    var_lines_dict[i] = new_line
        
        return self.updated_codelines_dict 

    def write_apdl_script(self,folder_path=None, id=0, filename='apdl_macro.dat', write_post=True):

        if folder_path is None:
            folder_path = os.getcwd()
        
        temp_path = os.path.join(folder_path,self.temp_folder_prefix + str(id))

        try:
            os.stat(folder_path)
        except:
            os.mkdir(folder_path) 

        try:
            os.stat(temp_path)
        except:
            os.mkdir(temp_path)  
        
        macro_file_path = os.path.join(temp_path,'apdl_macro.dat')
        macro_file = open(macro_file_path,'w')

        codelines_dict = self.updated_codelines_dict
        for label_code in codelines_dict:
            if label_code=='modal_post' or label_code=='static_post':
                if write_post:
                    for line in codelines_dict[label_code]:
                        macro_file.write(line)
            else:
                for line in codelines_dict[label_code]:
                    macro_file.write(line)

        macro_file.close()
        self.temp_path = temp_path
        self.macro_file_path = macro_file_path
        return temp_path, macro_file_path

    def set_ansys_apdl_path(self, ansys_apdl_path):
        self.ansys_apdl_path = ansys_apdl_path
    
    def run_simulation(self, macro_path=None , out_name ='solve.out', np=1):

        if macro_path is None:
            macro_path = self.macro_file_path

        # copying pre proc file to run locaction
        prep_file = os.path.join(self.var_dict['file_directory'],self.var_dict['apdl_pre_file'] + '.dat')
        new_prep_file =os.path.join(self.temp_path, self.var_dict['apdl_pre_file'] + '.dat')
        copyfile(prep_file,new_prep_file)

        run_file_path = os.path.join(self.temp_path,'run_apdl.bat')
        command_line = '"' + self.ansys_apdl_path + '"'
        command_line += ' -b -i '
        command_line += '"' + macro_path + '"'
        command_line += ' -o ' + out_name
        command_line += ' -np ' + str(np)


        run_file = open(run_file_path,'w')
        run_file.write(command_line)
        run_file.close()


        try:
            local_folder = os.getcwd()
            os.chdir(self.temp_path)
            subprocess.call(run_file_path)
            os.chdir(local_folder)
            return os.listdir(self.temp_path)            

        except:
            print('Error during the simulation.')
            return None


    def read_result(self,filename,directory=None):

        if directory is None:
            directory = self.temp_path
        
        filepath = os.path.join(directory,filename)            
        df = pd.read_csv(filepath,header=0,sep='\s+')

        self.results_dict['filename'] = df
        return df

    def read_frequencies(self,filename_prefix='Frequency_harm_',ext='.txt'):

        num_harmonics = self.var_dict['number_of_harmonics'] 
        num_modes = self.var_dict['number_of_modes'] 
        self.freq_dict = {}
        self.freq_list = []
             
        for h_index in range(num_harmonics+1):
            filename = filename_prefix + str(h_index+1) + ext
            df = self.read_result(filename)
            df_key= df.columns[0]
            freq_list = df[df_key].tolist()
            self.freq_dict[h_index] = freq_list
            self.freq_list.extend(freq_list)

        return self.freq_list


if __name__=='__main__':
    base_file_path = r'H:\TUM-PC\Dokumente\Projects\campbell_diagram'
    filename = 'base_apdl_script.dat'
    filepath = os.path.join(base_file_path,filename)
    f = open(filepath)

    temp_folder_prefix = 'rot_'

    apdl = pyAPDL(filepath,temp_folder_prefix)

    var_dict = {}
    var_dict['apdl_pre_file'] = 'prep_case1'
    var_dict['file_directory'] = r'H:\TUM-PC\Dokumente\Projects\campbell_diagram'
    var_dict['number_of_harmonics'] = 2
    var_dict['number_of_modes'] = 4
    var_dict['rotational_speed'] = 20

    folder = r'H:\TUM-PC\Dokumente\Projects\campbell_diagram'

    apdl.update_input_variables(var_dict)
    apdl.write_apdl_script(folder)

    apdl.set_ansys_apdl_path(r'C:\Program Files\ANSYS Student\v182\ansys\bin\winx64\ansys182.exe')
    apdl.run_simulation()
    freq1 = apdl.read_result('Frequency_harm_1.txt')

    f = apdl.read_frequencies()

    a = 1

