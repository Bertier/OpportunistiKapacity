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
from DatasetReader import DatasetReader
from scipy import spatial
    
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
output_dir="./res"

#TODO: get granularity from dataset
time_granularity=0.6
xa=time_granularity
xb=time_granularity*2

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
rssi_func=np.vectorize(ModelNearbyWoWMoM.DISTANCE_TO_RSSI)
bps_func=np.vectorize(ModelNearbyWoWMoM.RSSI_TO_BPS)
old_edges=set()

#for time in np.arange(test_range[0],test_range[1],ds.time_granularity):
for time,id_nodes,posx_nodes,posy_nodes in DatasetReader(dataset):
    #Get the current position of all nodes
    position_nodes=np.array((posx_nodes,posy_nodes)).astype(float).T
    #Find which nodes are able to exchange data
    distance_between_nodes = spatial.distance.cdist(position_nodes,position_nodes)
    throughput_between_nodes= bps_func(rssi_func(distance_between_nodes,pathloss=propagation),\
                                      modulation_scheme=modulation)
    throughput_between_nodes *= np.tri(throughput_between_nodes.shape[0],throughput_between_nodes.shape[1],-1)
    #np.fill_diagonal(throughput_between_nodes,0)
    current_edges_indexes=np.where(throughput_between_nodes > 0)
    instant_goodput=[]
    if len(current_edges_indexes[0]):
        for k in range(current_edges_indexes[0]):
            node_1=id_nodes[current_edges_indexes[0][k]]
            node_2=id_nodes[current_edges_indexes[1][k]]
            edge_key="-".join(sorted([node_1,node_2]))
            instant_goodput[edge_key]=throughput_between_nodes[current_edges_indexes[0][k],\
                                                          current_edges_indexes[1][k]]
    current_edges=set(instant_goodput.keys()) if len(instant_goodput) else set()
    """
    There are 3 possbilities.
    1) The contact is new at this instant, we add it to our dictionnary of contacts
    2) The contact existed, we simply increment the contact capacity since it lasted longer
    3) The contact does not exist anymore, we remove it from the current contacts and count it as terminated
    """
    #If it is in the current contact, and did not exist is the previous contacts, it is new.
    for edge in current_edges - old_edges:
        current_distance=current_graph[edge]
        yb=current_graph[edge]
        ya=0
        current_contacts[edge]=integrate(ya,yb)
        current_contacts_start[edge]=time-ds.time_granularity

    #If it existed both in previous and current contacts, simply update the capacity.
    for edge in current_edges & old_edges:
        #this is a previously established contact
        current_distance=current_graph[edge]
        previous_distance=old_graph[edge]
        yb=current_graph[edge]
        ya=old_graph[edge]
        current_contacts[edge]+=integrate(ya,yb)

    #If there are contact that previously existed and are not found in the current one, consider it terminated.
    for edge in old_edges - current_edges:
        #this is the end of the contact
        ya=old_graph[edge]
        yb=0
        previous_distance=old_graph[edge]
        final_edge_key="contact:%s;time:%s-%s" % (edge,current_contacts_start[edge],time)
        terminated_contacts[final_edge_key]=current_contacts[edge] + integrate(ya,yb)
        del current_contacts[edge]
        del current_contacts_start[edge]
    
    old_edges=current_edges
    old_graph=current_graph
    print time, len(current_contacts),len(terminated_contacts)



with open(output_dir+'contacts_data_nearby_%s_%s_%s_%s_%s.json' % (test_range[0],test_range[1],dataset,propagation_name,modulation_name), 'w') as fp:
    json.dump(terminated_contacts, fp)
    #print "writing disabled for test. Uncomment line in code to enable writing output."
sys.exit()
