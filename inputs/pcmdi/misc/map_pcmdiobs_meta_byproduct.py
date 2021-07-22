import json

fi = 'pcmdiobs_timeSeries_info_v20200206.json'

d = json.load(open(fi))

prods = []

print(d.keys())

var = d.keys()
check = {}
mapped = {}
for v in var:
   prodv = d[v].keys() 

   for p in prodv:
     if p not in prods and p not in ['default','alternate1']: prods.append(p)

for p in prods:
  check[p] = []
  mapped[p] = {} 
  for v in var:
   try:
      t = d[v][p]
      print(v,' ',p,'   works')
      check[p].append(v)      
   except:
      pass

for p in check.keys():
  vs = check[p]

  for v in vs: 
    mapped[p][v] = d[v][p]

json_name = 'test.json'

json.dump(mapped, open(json_name, 'w'), sort_keys=True, indent=4,
          separators=(',', ': '))

