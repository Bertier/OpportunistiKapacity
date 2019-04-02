#!/usr/bin/python
"""
Calculate the contact data-exchange through integral linear interpolation.
"""
import sys
import os
from decimal import Decimal
import numpy as np
import json
from opportunistikapacity import GeographicTrace
import ModelNearbyWoWMoM

if len(sys.argv) < 4:
    print "Error: not enough arguments."
    print "Usage: %s file_dataset propagation_model modulation_scheme" % sys.argv[0]
    exit(1)

"""
For now, the dataset's format should be
time dummy ID x y
"""
dataset=sys.argv[1]
propagation_name=sys.argv[2]
modulation_name=sys.argv[3]

propagation=False
modulation=False
no_positions=False
for p in ModelNearbyWoWMoM.propagation_models:
    if p.func_name == propagation_name:
        propagation=p
        break
if not propagation:
    print("Error, propagation not found.")
    print("Available propagations: "+str((ModelNearbyWoWMoM.propagation_models_names)))
    sys.exit(2)

for m in ModelNearbyWoWMoM.modulation_schemes:
    if m.func_name == modulation_name:
        modulation=m
        break
if not modulation:
    print "Error, modulation not found."
    print("Available modulations: "+str((ModelNearbyWoWMoM.modulation_schemes_names)))
    sys.exit(3)
    
output_dir="./res/"

trace=GeographicTrace(dataset,propagation,modulation)
all_contacts=trace.get_capacity()
if not os.path.exists(output_dir):
    os.mkdir(output_dir) 
with open(output_dir
          + 'contacts_data_nearby_%s_%s_%s.json' % (dataset, propagation_name, modulation_name),
          'w') as fp:
    json.dump(all_contacts, fp,ensure_ascii=False,indent=4)
sys.exit()
