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
import ConfigParser
from opportunistikapacity import GeographicTrace,ContactTrace
import communications

name_configuration_file='opportunistiKapacity.cfg'
sample_configuration="""
[contact-trace]
mobility = human

[mobility-trace]
distance_calculation = euclidean
column_delimiter = 
file_parsing = time dummy id x y

[communications]
min_rssi = -87
frequency = 5180
Wifi5_goodput_bottleneck = 24.267885
"""

if __name__ == '__main__':
    """
    Check if configuration is present.
    """
    cfg = ConfigParser.ConfigParser()
    try:
        with open(name_configuration_file) as f:
            cfg.read(f)
    except IOError:
        print("This is the first run. Writing default configuration file %s." % name_configuration_file)
        with open(name_configuration_file,'w') as handle_config:
            handle_config.write(sample_configuration)
            handle_config.close()
    cfg.read(name_configuration_file)
    """
    cfg.add_section('Communications')
    cfg.set('Communications', 'min_rssi', '-87')
    """
    """
    Check if args are correct
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset",type=argparse.FileType('r'),help="Location of the trace file.")
    parser.add_argument("propagation_model",type=str,help="Signal loss model name. Available choices: %s" % str(communications.propagation_models_names).strip('[]'))
    parser.add_argument("modulation_scheme",type=str,help="Modulation scheme name. Available choices: %s" % str(communications.modulation_schemes_names).strip('[]'))
    parser.add_argument("trace_kind",type=str,help="Two kinds of traces supported: 'mobility' (spatial coordinates) or 'contact' (duration of contacts).")
    parser.parse_args()

    
    dataset=sys.argv[1]
    propagation_name=sys.argv[2]
    modulation_name=sys.argv[3]
    trace_kind=sys.argv[4]
    
    propagation=False
    modulation=False
    no_positions=False
    for p in communications.propagation_models:
        if p.func_name == propagation_name:
            propagation=p
            break
    if not propagation:
        print("Error, propagation not found.")
        print("Available propagations: "+str((communications.propagation_models_names)))
        sys.exit(2)

    for m in communications.modulation_schemes:
        if m.func_name == modulation_name:
            modulation=m
            break
    if not modulation:
        print("Error, modulation not found.")
        print("Available modulations: "+str((communications.modulation_schemes_names)))
        sys.exit(3)

    #A this point, everything should be set up to run.
    cfg.write(open(name_configuration_file,'w'))
    if trace_kind == "mobility":
        trace=GeographicTrace(dataset,propagation,modulation)
        all_contacts=trace.get_capacity()
    elif trace_kind == "contact":
        trace=ContactTrace(dataset,propagation, modulation, "human")
        all_contacts=trace.get_capacity()
    else:
        print("The trace kind '%s' is unknown or not supported." % trace_kind)
        sys.exit(7)
    output_dir="./results/"
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    if not os.path.exists(output_dir+dataset.split("/")[0]):
        os.mkdir(output_dir+dataset.split("/")[0])
    with open(output_dir
              +  dataset.split("/")[0] + "/"
              + 'contacts_%s_%s.json' % (propagation_name, modulation_name),
              'w') as fp:
        json.dump(all_contacts, fp, ensure_ascii=False, indent=4)
    sys.exit()
