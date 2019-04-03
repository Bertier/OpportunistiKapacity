#!/usr/bin/python
import os
from decimal import Decimal
import sys
import numpy as np

class DatasetReader(object):
    def __init__(self, dataset, start=-1,end=-1,field_separator=' '):
        if not os.path.isfile(dataset):
            print("Error, '%s' is not a file or does not exist." % dataset)
            sys.exit(0)
         #Get the first timestamp of the file.
        self.file_handle=open(dataset,"r")
        self.field_separator=field_separator
        first_line=self.file_handle.readline().split(field_separator)
        self.time=Decimal(first_line[0])
        #Loop to find the second timestamp, then reset cursor in file.
        for line in self.file_handle:
            fields=line.split(" ")
            current_time=Decimal(fields[0])
            if current_time != self.time:
                granularity=current_time - self.time
                break
        self.file_handle.seek(0)
        self.previous=[]
    def __iter__(self):
        return self
    """
    For now, the dataset's format should be
    time dummy ID x y
    """
    def next(self):
        current = [self.previous[:]] if len(self.previous) else []
        for line in self.file_handle:
            fields=line.split(self.field_separator)
            current_time=Decimal(fields[0])
            if current_time != self.time:
                self.time=current_time
                self.previous=[fields[0],fields[2],fields[3],fields[4]]
                break
            else:
                current.append([fields[0],fields[2],fields[3],fields[4]])
        if self.previous == current[0]:
            raise StopIteration
        return np.array(current).T

    
class ContactReader(object):
    
    def __init__(self, dataset, start=-1,end=-1,field_separator=' '):
        if not os.path.isfile(dataset):
            print("Error, '%s' is not a file or does not exist." % dataset)
            sys.exit(0)
        self.file_handle=open(dataset,"r")
        self.field_separator=field_separator

    def __iter__(self):
        return self
    
    def next(self):
        #TODO: Field seperator fix
        fields=self.file_handle.readline().split()
        if len(fields):
            return fields[0:4]
        else:
            raise StopIteration
