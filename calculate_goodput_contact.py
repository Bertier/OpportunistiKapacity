#!/usr/bin/python
"""
Calculate the contact data-exchange through integral linear interpolation.
"""
import networkx as nx
import numpy as np
from scipy.integrate import quad
import ModelNearbyWoWMoM
import json
import sys
import pickle
import os
from decimal import Decimal
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
#attempt to open the dataset
if os.path.isfile(dataset):
    file_handle=open(dataset,"r")
    first_line=file_handle.readline().split()
    time=Decimal(first_line[0])
    file_handle.seek(0)
else:
    print("Error, '%s' is not a file or does not exist."%dataset)
    sys.exit(1)

propagation=False
modulation=False
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


    
directory="../../data/pickle_graphs/"
output_dir="../../data/contacts_capacity/"
#test_range=[14400,79200] # toute la journee
#test_range=[30000,31200] # peak
#test_range=[39600,54000] # mid-day
#test_range=[5000,15000] # night




xa=ds.time_granularity
xb=ds.time_granularity*2
time_granularity=ds.time_granularity
def linear(x, a, b):
    return a*x + b
def integrate(ya,yb):
    a=(yb-ya)/(ds.time_granularity)
    b=ya-a*xa
    data_contact,error_integration = quad(linear, xa, xb, args=(a,b))
    return data_contact

    
current_contacts={}
current_contacts_start={}
terminated_contacts={}

for time in np.arange(test_range[0],test_range[1],ds.time_granularity):
    current_graph={}
    for edge,distance in pickle.load(open(directory + "%s_%s.pkl" % (dataset,time), 'rb') ).items():
        #value_goodput=RSSI_TO_BPS(freespace_Rx(distance,10))
        rssi=ModelNearbyWoWMoM.DISTANCE_TO_RSSI(distance,pathloss=propagation)
        value_goodput=ModelNearbyWoWMoM.RSSI_TO_BPS(rssi,modulation_scheme=modulation)
        if value_goodput > 0:
            current_graph[edge]=value_goodput
            
    current_edges=set(current_graph.keys())
    if time != test_range[0]:
        for edge in current_edges - old_edges:
            #this is a new contact
            current_distance=current_graph[edge]
            yb=current_graph[edge]
            ya=0
            current_contacts[edge]=integrate(ya,yb)
            current_contacts_start[edge]=time-ds.time_granularity
        for edge in current_edges & old_edges:
            #this is a previously established contact
            current_distance=current_graph[edge]
            previous_distance=old_graph[edge]
            yb=current_graph[edge]
            ya=old_graph[edge]
            current_contacts[edge]+=integrate(ya,yb)
        for edge in old_edges - current_edges:
            #this is the end of the contact
            ya=old_graph[edge]
            yb=0
            previous_distance=old_graph[edge]
            final_edge_key="contact:%s;time:%s-%s" % (edge,current_contacts_start[edge],time)
            terminated_contacts[final_edge_key]=current_contacts[edge] + integrate(ya,yb)
            del current_contacts[edge]
            del current_contacts_start[edge]
    else:
        for edge in current_edges:
            #this is a new contact
            current_distance=current_graph[edge]
            rssi=ModelNearbyWoWMoM.DISTANCE_TO_RSSI(distance,pathloss=propagation)
            yb=ModelNearbyWoWMoM.RSSI_TO_BPS(rssi,modulation_scheme=modulation)
            ya=0
            current_contacts[edge]=integrate(ya,yb)
            current_contacts_start[edge]=time
    old_edges=current_edges
    old_graph=current_graph
    print time, len(current_contacts),len(terminated_contacts)



with open(output_dir+'contacts_data_nearby_%s_%s_%s_%s_%s.json' % (test_range[0],test_range[1],dataset,propagation_name,modulation_name), 'w') as fp:
    json.dump(terminated_contacts, fp)
    #print "writing disabled for test. Uncomment line in code to enable writing output."
sys.exit()
