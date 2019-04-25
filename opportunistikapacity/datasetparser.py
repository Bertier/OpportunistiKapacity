#!/usr/bin/python3
from decimal import Decimal
import sys
import re
import numpy as np
import configparser

name_configuration_file = 'opportunistiKapacity.cfg'

"""
LIST OF REGEX TO PARSE FILES
"""
float_re = r'[-+]?[0-9]*\.?[0-9]+'
int_re = r'[-+]?[0-9]*'
string_re = r'\S+'
any_re = r'.+?'

dummy_re = any_re

time_re = r'(?P<time>%s)' % float_re
id_node_re = r'(?P<id_node>%s)' % string_re
pos_x_re = r'(?P<pos_x>%s)' % float_re
pos_y_re = r'(?P<pos_y>%s)' % float_re
mobility_params = {
    "time": time_re,
    "dummy": dummy_re,
    "x": pos_x_re,
    "y": pos_y_re,
    "id": id_node_re
}

id1_node_re = r'(?P<id1_node>%s)' % string_re
id2_node_re = r'(?P<id2_node>%s)' % string_re
start_re = r'(?P<start>%s)' % float_re
end_re = r'(?P<end>%s)' % float_re
contact_params = {
    "dummy": dummy_re,
    "start": start_re,
    "end": end_re,
    "id1": id1_node_re,
    "id2": id2_node_re
}


class MobilityParser(object):

    def __init__(self, dataset):
        """Creates an iterator over a mobility dataset file. Each iteration returns the group of nodes existing during the snapshot.

        :param dataset: File object of the mobility trace.
        """
        # Load the configuration file
        cfg = configparser.ConfigParser()
        cfg.read(name_configuration_file)
        # Infer the regular expression from the configuration file.
        raw_file_format = cfg.get('mobility-trace', 'file_parsing', fallback='time id x y')
        column_delimiter = cfg.get('mobility-trace', 'column_delimiter', fallback='')
        if not len(column_delimiter):
            column_delimiter='\s'
        pre_regex_format = ("^%s*{" % column_delimiter) + ("}%s+{" % column_delimiter).join(
            raw_file_format.split()) + "}"
        self.line_regex = re.compile(r'%s' % pre_regex_format.format(**mobility_params))
        # Get the first timestamp of the file.
        self.file_handle = dataset
        first_line = self.file_handle.readline()
        first_match = self.line_regex.search(first_line)
        if first_match is None:
            print(("First line of dataset is: %s \n" % first_line +
                  "This does not match the pattern '%s'. Please verify syntax." % raw_file_format))
            sys.exit(9)

        self.time = Decimal(self.line_regex.search(self.file_handle.readline()).group('time'))
        # Loop to find the second timestamp, then reset cursor in file.
        for line in self.file_handle:
            current_time = Decimal(self.line_regex.search(line).group('time'))
            if current_time != self.time:
                self.granularity = np.float(current_time - self.time)
                break
        self.file_handle.seek(0)
        self.previous = []
        self.line_number = 1

    def __iter__(self):
        return self

    def __next__(self):
        current = [self.previous[:]] if len(self.previous) else []
        for line in self.file_handle:
            self.line_number += 1
            fields = self.line_regex.search(line)
            if fields is None:
                print("Error in dataset file at line %d. Please check format." % self.line_number)
                sys.exit(10)
            current_fields = [fields.group('time'), fields.group('id_node'), fields.group('pos_x'),
                              fields.group('pos_y')]
            current_time = Decimal(current_fields[0])
            if current_time != self.time:
                self.time = current_time
                self.previous = current_fields
                break
            else:
                current.append(current_fields)
        if self.previous == current[0]:
            raise StopIteration
        return np.array(current).T


class ContactParser(object):

    def __init__(self, dataset):
        """Creates an iterator over a contact dataset file. Each iteration returns a single contact.

        :param dataset: Creates an iterator over a contact dataset file.
        """
        self.file_handle = dataset
        cfg = configparser.ConfigParser()
        cfg.read(name_configuration_file)
        raw_file_format = cfg.get('contact-trace', 'file_parsing', fallback='id1 id2 start end')
        column_delimiter = cfg.get('contact-trace', 'column_delimiter', fallback='\s')
        pre_regex_format = ("^%s*{" % column_delimiter) + ("}%s+{" % column_delimiter).join(
            raw_file_format.split()) + "}"
        self.line_regex = re.compile(r'%s' % pre_regex_format.format(**contact_params))
        self.line = 1
        self.file_handle.seek(0)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.file_handle.readline()
        self.line += 1
        if len(line):
            fields = self.line_regex.search(line)
            if fields is None:
                print("Error in dataset file at line %d. Please check format." % self.line_number)
                sys.exit(10)
            else:
                return [fields.group('id1_node'), fields.group('id2_node'), fields.group('start'), fields.group('end')]
        else:
            raise StopIteration

