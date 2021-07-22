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
   f =  open(l,'r')
   d = json.load(f)
   f.close()

###########
# THIS IS THE INFO THAT GETS MODIFIED
   d['outpath'] = '/p/user_pub/PCMDIobs/'
   d['activity_id'] = 'PCMDIobs2'
   d['curation_provenance'] = 'work-in-progress'
   d['output_file_template'] = '<variable_id><frequency><source_id><variant_label><grid_label><version>'
   d['_controlled_vocabulary_file'] = d['_control_vocabulary_file']

   d.pop('_control_vocabulary_file')

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

    



  
