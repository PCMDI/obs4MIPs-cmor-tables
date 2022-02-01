import sys, os, json
import glob
from shutil import copyfile
import time

### 
# THIS CODE IS USED TO CHANGE A KEY(S) ACROSS ALL INPUT JSONS

lst = glob.glob('./*.json')

for l in lst:   #[0:2]:
## MV all FILE.json to FILE_cp.json 
 cpf = l.replace('.json','_cp.json')
 print(l,'  ', cpf)
 copyfile(l, cpf)
#os.rename(l,cpf)
 time.sleep(0.5)

# LOAD DICTIONARY CONTENTS 
 try:  
#for a in [1]:
   f =  open(l,'r')
   d = json.load(f)
   f.close()

###########
# THIS IS THE INFO THAT GETS MODIFIED
   d['outpath'] = '/p/user_pub/PCMDIobs/'
   d['curation_provenance'] = 'work-in-progress'
#  d['output_file_template'] = '<variable_id><frequency><source_id><variant_label><grid_label><version>'
#  d['_controlled_vocabulary_file'] = d['_control_vocabulary_file']

   d['output_file_template'] = "<variable_id><frequency><source_id><variant_label><grid_label>"
   d['output_path_template'] = "<activity_id>/<institution_id>/<source_id>/<frequency>/<variable_id>/<grid_label>/<version>" 
   d["variant_label"] = "PCMDI"
   d["product"] = "observations"
   d["activity_id"] = "obs4MIPs"
   d["license"] = "Data in this file processed for obs4MIPs by PCMDI and is for research purposes only."
   d["_AXIS_ENTRY_FILE"] = "obs4MIPs_coordinate.json"
   d["_FORMULA_VAR_FILE"] = "obs4MIPs_formula_terms.json"
   d["_controlled_vocabulary_file"] = "obs4MIPs_CV.json"
#  d["institution_id"] =  d["institution_id"] + '--PCMDI'
#  d["institution"] = 'tmp' 


#  try:
#   d.pop('_control_vocabulary_file')
#  except:
#   pass

###########
### SAVE CHANGED VALUES
   time.sleep(0.5)
   g =  open(l,'w+')
   print(l,' ', d.keys())
   print('---------------------------')
#  json.dumps(d,g)
#  json.dump(d,g,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
   json.dump(d,g,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'))
   g.close()
 except:
   print('failed with ', l)

os.popen('mv *cp.json older').readlines()

    



  
