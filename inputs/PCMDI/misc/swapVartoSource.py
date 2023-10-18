import json


pin = '/p/user_pub/PCMDIobs/catalogue/pcmdiobs_monthly_catalogue_v20200416.json'

f = open(pin)
d = json.load(f)
vs = d.keys()
sources = []

for v in vs:
  source_tmp = d[v].keys() 
  for s in source_tmp: 
    if s not in sources and s not in ['default','alternate1']: sources.append(s)


print(sources)

