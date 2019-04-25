# OpportunistiKapacity
A python library to turn mobility traces into opportunistic contact capacity. 
This library aims to simplify the calculation of total network data capacity, more precisely in the context of contact networks. 
## Basic run using wrapper
You must provide at least **4** parameters for the software to run:

 1. The trace kind
 2. The trace path
 3. A propagation model
 4. A modulation scheme

If these arguments are known, you can run the script:
`./OKwrapper.py trace_kind dataset propagation_model modulation_scheme`

## Supported traces

This library only considers two types of datasets. Both are text-based. 
### Mobility trace
The `mobility` trace kind is a format where all existing nodes have their geographical coordinates updated at each snapshot. For example:  

    0.0 	a	 50479.67 	54248.598
    0.0 	b 	47721.375 	54930.71
    0.0 	c 	48519.473 	55673.586
    0.0 	d 	48798.016 	54503.477
    0.0 	e 	50233.27 	55252.617
    1.0 	a 	50479.684 	54248.62
    1.0 	b 	47722.023 	54930.7
    1.0 	c 	48518.676 	55675.266
    1.0 	d 	48798.703 	54505.332
    1.0 	e 	50235.68 	55251.816 
The above snippet has four columns, from left to right: time, node id, x coordinate, y coordinate. Publishing traces in such a format is a common practice within mobility simulation studies (e.g., [TAPASCologne](http://kolntrace.project.citi-lab.fr/)).
### Contact trace
The `contact` trace kind is a format describing a contact duration between two nodes, regardless of when the contact actually happened.

    1	2	1156084891	1156084895	
    2	3	1156085092	1156085159	
    4	2	1156085110	1156085118	
    5	8	1156085190	1156085191	
    4	2	1156085219	1156085302	
The above snippet has four columns, from left to right: id node 1, id node 2, start contact, end contact.

## Propagation models
The propagation models, found in the `communications` module, calculate the signal loss according to the distance between the receiver and transmitter. So far we include the following path loss models:

 - Freespace (`freespace_loss`)
 - Log-distance (`logDistance_loss`)
 - Two-Ray ground reflection (`twoRay_loss`)

## Modulation schemes

The modulation schemes, found in the `communications` module, set a data rate for a given RSSI between two nodes. So far, we propose the following path loss models (explained thoroughly in our paper):

 - `Wifi5_empirical_goodput`
 - `Wifi5_stepwise_max`
 - `Wifi5_stepwise_linear_adjusted`
 - `Wifi5_stepwise_fit`
 
# Module and classes

The module is separated in 3 files:

 - `communications` everything function to do with the translation of distance into a throughput estimation.
 - `datasetparser`: provides two classes, (`ContactParser`, `MobilityParser`) to iterate over a dataset file. 
 - `contactcalculator`, provides the two classes (`GeographicTrace`, `ContactTrace`) to calculate the contact capacity.
 
 