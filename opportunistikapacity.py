#!/usr/bin/python
"""
Calculate the contact data-exchange through integral linear interpolation.
"""
import sys
import os
from decimal import Decimal
import numpy as np
from scipy.integrate import quad
from scipy import spatial
from datetime import datetime
import json
import ConfigParser
from datasetparser import MobilityParser, ContactParser
import communications
name_configuration_file = 'opportunistiKapacity.cfg'


class GeographicTrace(object):
    # TODO: get granularity from dataset
    def __init__(self, dataset, propagation, modulation, start=-1, end=-1):
        self.propagation = propagation
        self.modulation = modulation
        self.time_granularity = 0.6
        self.xa = self.time_granularity
        self.xb = self.time_granularity * 2
        self.rssi_func = np.vectorize(communications.DISTANCE_TO_RSSI)
        self.bps_func = np.vectorize(communications.RSSI_TO_BPS)
        self.dataset = dataset

    def linear(self, x, a, b):
        return a * x + b

    def integrate(self, ya, yb):
        a = (yb - ya) / (self.time_granularity)
        b = ya - a * self.xa
        data_contact, error_integration = quad(
            self.linear, self.xa, self.xb, args=(a, b))
        return data_contact

    def get_capacity(self):
        old_edges = set()
        active_contacts_data = {}
        active_contacts_start = {}
        terminated_contacts = {}
        for times, id_nodes, posx_nodes, posy_nodes in MobilityParser(
                self.dataset):
            time = float(times[0])
            # Get the current position of all nodes
            position_nodes = np.array((posx_nodes, posy_nodes)).astype(float).T
            # Find which nodes are able to exchange data
            distance_between_nodes = spatial.distance.cdist(
                position_nodes, position_nodes)
            throughput_between_nodes = self.bps_func(
                self.rssi_func(
                    distance_between_nodes,
                    pathloss=self.propagation),
                modulation_scheme=self.modulation)
            throughput_between_nodes *= np.tri(
                throughput_between_nodes.shape[0], throughput_between_nodes.shape[1], -1)
            # np.fill_diagonal(throughput_between_nodes,0)
            instant_edges_indexes = np.where(throughput_between_nodes > 0)
            instant_goodput = {}
            if len(instant_edges_indexes[0]):
                for k in range(len(instant_edges_indexes[0])):
                    node_1 = id_nodes[instant_edges_indexes[0][k]]
                    node_2 = id_nodes[instant_edges_indexes[1][k]]
                    edge_key = "-".join(sorted([node_1, node_2]))
                    instant_goodput[edge_key] = throughput_between_nodes[instant_edges_indexes[0][k],
                                                                         instant_edges_indexes[1][k]]
            instant_edges = set(instant_goodput.keys()) if len(
                instant_goodput) else set()
            """
            There are 3 possbilities.
            1) The contact is new at this instant, we add it to our dictionnary of active contacts
            2) The contact existed, we simply increment the contact capacity since it lasted longer
            3) The contact does not exist anymore, we remove it from the current contacts and count it as terminated
            """
            # If it is in the current contact, and did not exist is the
            # previous contacts, it is new.
            for edge in instant_edges - old_edges:
                instant_distance = instant_goodput[edge]
                ya = 0
                yb = instant_goodput[edge]
                active_contacts_data[edge] = self.integrate(ya, yb)
                active_contacts_start[edge] = time - self.time_granularity

            # If it existed both in previous and current contacts, simply
            # update the capacity.
            for edge in instant_edges & old_edges:
                # this is a previously established contact
                instant_distance = instant_goodput[edge]
                previous_distance = old_graph[edge]
                ya = old_graph[edge]
                yb = instant_goodput[edge]
                active_contacts_data[edge] += self.integrate(ya, yb)

            # If there are contact that previously existed and are not found in
            # the current one, consider it terminated.
            for edge in old_edges - instant_edges:
                # this is the end of the contact
                ya = old_graph[edge]
                yb = 0
                previous_distance = old_graph[edge]
                final_edge_key = "contact:%s;time:%s-%s" % (
                    edge, active_contacts_start[edge], time)
                terminated_contacts[final_edge_key] = active_contacts_data[edge] + \
                    self.integrate(ya, yb)
                del active_contacts_data[edge]
                del active_contacts_start[edge]
            print time
            old_edges = instant_edges
            old_graph = instant_goodput

        return terminated_contacts


class ContactTrace(object):
    def __init__(self, dataset, propagation, modulation, data_kind):
        folder_ressources = "./ressources/proba_duration_capacity"
        self.propagation = propagation
        self.modulation = modulation
        self.dataset = dataset

        if data_kind == "human":
            data_source = "stockholm"
        elif data_kind == "vehicle":
            data_source = "luxembourg"
        else:
            print("Data kind '%s' not recognized.")
            sys.exit(5)
        precomputed_file_name = "%s/%s/%s_%s_%s.json" % (folder_ressources,
                                                         data_source,
                                                         data_source,
                                                         propagation.func_name,
                                                         modulation.func_name)
        try:
            precomputed_file_handle = open(precomputed_file_name, "r")
            self.presampled_contacts = json.load(precomputed_file_handle)
        except BaseException:
            print("Cannot open the file '%s'" % precomputed_file_name)
            sys.exit(6)
        self.sampling_granularity = np.absolute(
            eval(self.presampled_contacts.keys()[0]))
        # Simply unpack the elements from the sampled datasets found in the
        # json file.
        self.contact_time_to_throughput_probability = {}
        for time_key in self.presampled_contacts:
            self.contact_time_to_throughput_probability[time_key] = zip(
                *self.presampled_contacts[time_key])
        self.number_samples = len(self.contact_time_to_throughput_probability)

    def get_capacity(self):
        terminated_contacts = {}
        for id1, id2, time_start_raw, time_end_raw in ContactParser(
                self.dataset):
            # todo: take time format in consideration. For now just make the
            # difference.
            time_start = datetime.fromtimestamp(float(time_start_raw))
            time_end = datetime.fromtimestamp(float(time_end_raw))
            time_contact = time_end - time_start
            if time_contact.total_seconds() > 0:
                index_sampling = int(
                    (time_contact.total_seconds() //
                     self.sampling_granularity) *
                    self.sampling_granularity)
                if index_sampling > (
                        (self.number_samples - 1) * self.sampling_granularity):
                    index_sampling = (
                        self.number_samples - 1) * self.sampling_granularity
                formated_time_key = "%s-%s" % (index_sampling,
                                               index_sampling + self.sampling_granularity)
                throughput_values, probability_value = self.contact_time_to_throughput_probability[
                    formated_time_key]
                final_contact_key = "contact:%s-%s;time:%s-%s" % (
                    id1, id2, time_start_raw, time_end_raw)
                terminated_contacts[final_contact_key] = np.random.choice(
                    throughput_values, p=probability_value)
        return terminated_contacts
