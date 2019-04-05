#!/usr/bin/python
import os
from decimal import Decimal
import sys
import re
import numpy as np
import ConfigParser
name_configuration_file='opportunistiKapacity.cfg'

"""
LIST OF REGEX TO PARSE FILES
"""
float_re=u'[-+]?[0-9]*\.?[0-9]+'
int_re=r'[-+]?[0-9]*'
string_re=r'\S+'
any_re=r'.+?'

time_re=r'(?P<time>%s)' % float_re
dummy_re= any_re
id_node_re=r'(?P<id_node>%s)' % string_re
pos_x_re=r'(?P<pos_x>%s)' % float_re
pos_y_re=r'(?P<pos_y>%s)' % float_re

mobility_params={
    "time":time_re,
    "dummy": dummy_re,
    "x":pos_x_re,
    "y":pos_y_re,
    "id":id_node_re
}

class DatasetReader(object):
    """
    Iterator over mobility datasets.
    Mobility datasets
    """
    def __init__(self, dataset, start=-1,end=-1,field_separator=' '):
        if not os.path.isfile(dataset):
            print("Error, '%s' is not a file or does not exist." % dataset)
            sys.exit(0)
        #Load the configuration file
        cfg = ConfigParser.ConfigParser()
        cfg.read(name_configuration_file)
        #Infer the regular expression from the configuration file.
        raw_file_format=cfg.get('mobility-trace', 'file_parsing')
        column_delimiter=cfg.get('mobility-trace','column_delimiter') if len(cfg.get('mobility-trace','column_delimiter')) else '\s'
        pre_regex_format="^{" + ("}%s+{" % column_delimiter).join(raw_file_format.split()) + "}"
        self.line_regex=re.compile(r'%s'% pre_regex_format.format(**mobility_params))
        #Get the first timestamp of the file.
        self.file_handle=open(dataset,"r")
        first_match=self.line_regex.search(self.file_handle.readline())
        if first_match is None:
            print("Dataset file does not match the pattern %s with delimiter. Please check file." % raw_file_format)
            sys.exit(9)
            
        self.time=Decimal(self.line_regex.search(self.file_handle.readline()).group('time'))
        #Loop to find the second timestamp, then reset cursor in file.
        for line in self.file_handle:
            current_time=Decimal(self.line_regex.search(line).group('time'))
            if current_time != self.time:
                granularity=current_time - self.time
                break
        self.file_handle.seek(0)
        self.previous=[]
        self.line_number=1
    def __iter__(self):
        return self

    def next(self):
        current = [self.previous[:]] if len(self.previous) else []
        for line in self.file_handle:
            self.line_number+=1
            fields=self.line_regex.search(line)
            if fields is None:
                print("Error in dataset file at line %d. Please check format." % self.line_number)
                sys.exit(10)
            current_fields=[fields.group('time'),fields.group('id_node'),fields.group('pos_x'),fields.group('pos_y')]
            current_time=Decimal(current_fields[0])
            if current_time != self.time:
                self.time=current_time
                self.previous=current_fields
                break
            else:
                current.append(current_fields)
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
