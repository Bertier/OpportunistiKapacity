#!/usr/bin/python
"""
Calculate the contact data-exchange through integral linear interpolation.
"""
import sys
import os
from decimal import Decimal
import numpy as np
import json
import argparse
from opportunistikapacity import GeographicTrace,ContactTrace
import ModelNearbyWoWMoM

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset",type=argparse.FileType('r'))
    parser.add_argument("propagation_model")
    parser.add_argument("modulation_scheme")
    parser.parse_args()

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

    output_dir="./results/"

    #trace=GeographicTrace(dataset,propagation,modulation)
    #all_contacts=trace.get_capacity()
    trace=ContactTrace(dataset,propagation, modulation, "human")
    all_contacts=trace.get_capacity()
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    if not os.path.exists(output_dir+dataset.split("/")[0]):
        os.mkdir(output_dir+dataset.split("/")[0])
    with open(output_dir
              + 'contacts_%s_%s.json' % (propagation_name, modulation_name),
              'w') as fp:
        json.dump(all_contacts, fp, ensure_ascii=False, indent=4)
    sys.exit()
