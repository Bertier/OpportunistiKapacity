#!/usr/bin/python3
"""
Calculate the contact data-exchange through integral linear interpolation.
"""
import sys
from decimal import Decimal

from scipy.integrate import quad
from scipy import spatial
from datetime import datetime
import json
from .datasetparser import MobilityParser, ContactParser
from .communications import *

name_configuration_file = 'opportunistiKapacity.cfg'


class GeographicTrace(object):

    def __init__(self, dataset, propagation, modulation):
        """

        :param dataset: File object of the mobility trace.
        :param propagation: Name of propagation (a.k.a. path loss) to be used.
        :param modulation: Name of the modulation scheme to be used.
        """
        self.propagation = propagation
        self.modulation = modulation
        self.rssi_func = np.vectorize(DISTANCE_TO_RSSI)
        self.bps_func = np.vectorize(RSSI_TO_BPS)
        self.dataset = dataset
        cfg = configparser.ConfigParser()
        cfg.read(name_configuration_file)
        # Infer the regular expression from the configuration file.
        self.distance_method = cfg.get('mobility-trace', 'distance_calculation', fallback='euclidean')


    def linear(self, x, a, b):
        return a * x + b

    def integrate(self, ya, yb, granularity):
        """

        :param point a:
        :param point b:
        :return: The quantity of data sent.
        """

        a = yb - ya / granularity
        b = ya  # would be ya - a * xa, but xa=0
        data_contact, error_integration = quad(
            self.linear, 0, granularity, args=(a, b))
        return data_contact

    def get_capacity(self):
        """Returns all contacts with their duration and estimated capacity.

        :return: Returns a dictionary holding all the terminated contacts information.\n
         The key is a format 'contact:node1-node2;time:timestart-timeend'.
         The value is the capacity, in MBytes.
        """
        old_edges = set()
        active_contacts_data = {}
        active_contacts_start = {}
        terminated_contacts = {}
        dataiterator = MobilityParser(self.dataset)
        for times, id_nodes, posx_nodes, posy_nodes in dataiterator:
            time = np.float(times[0])
            # Get the current position of all nodes from the data iteration
            position_nodes = np.array((posx_nodes, posy_nodes)).astype(float).T
            # Calculate the distance between nodes
            distance_between_nodes = spatial.distance.cdist(
                position_nodes, position_nodes, metric=self.distance_method)
            # See if nodes are able to exchange at a link speed > 0
            throughput_between_nodes = RSSI_TO_BPS(
                DISTANCE_TO_RSSI(
                    distance_between_nodes,
                    pathloss=self.propagation),
                modulation_scheme=self.modulation)
            throughput_between_nodes *= np.tri(
                throughput_between_nodes.shape[0], throughput_between_nodes.shape[1], -1)
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
            There are 3 possibilities.
            1) The contact is new at this instant, we add it to our dictionary of active contacts
            2) The contact existed, we simply increment the contact capacity since it lasted longer
            3) The contact does not exist anymore, we remove it from the current contacts and count it as terminated
            """
            # If it is in the current contact, and did not exist is the
            # previous contacts, it is new.
            for edge in instant_edges - old_edges:
                ya = 0
                yb = instant_goodput[edge]
                active_contacts_data[edge] = self.integrate(ya, yb, dataiterator.granularity)
                active_contacts_start[edge] = time - dataiterator.granularity

            # If it existed both in previous and current contacts, simply
            # update the capacity.
            for edge in instant_edges & old_edges:
                # this is a previously established contact
                ya = old_graph[edge]
                yb = instant_goodput[edge]
                active_contacts_data[edge] += self.integrate(ya, yb, dataiterator.granularity)

            # If there are contact that previously existed and are not found in
            # the current one, consider it terminated.
            for edge in old_edges - instant_edges:
                # this is the end of the contact
                ya = old_graph[edge]
                yb = 0
                final_edge_key = "contact:%s;time:%.2f-%.2f" %  (
                    edge, active_contacts_start[edge], time)
                terminated_contacts[final_edge_key] = active_contacts_data[edge] + \
                                                      self.integrate(ya, yb, dataiterator.granularity)
                del active_contacts_data[edge]
                del active_contacts_start[edge]
            print(time)
            old_edges = instant_edges
            old_graph = instant_goodput

        return terminated_contacts


class ContactTrace(object):
    def __init__(self, dataset, propagation, modulation, data_kind):
        """

        :param dataset: File object of the contact trace.
        :param propagation: Name of propagation (a.k.a. path loss) to be used.
        :param modulation: Name of the modulation scheme to be used.
        """
        folder_ressources = "./ressources/proba_duration_capacity"
        self.propagation = propagation
        self.modulation = modulation
        self.dataset = dataset
        cfg = configparser.ConfigParser()
        cfg.read(name_configuration_file)
        data_kind = cfg.get('contact-trace', 'mobility', fallback='human')
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
                                                         propagation.__name__,
                                                         modulation.__name__)
        try:
            precomputed_file_handle = open(precomputed_file_name, "r")
            self.presampled_contacts = json.load(precomputed_file_handle)
        except BaseException:
            print("Cannot open the file '%s'" % precomputed_file_name)
            sys.exit(6)
        self.sampling_granularity = np.absolute(
            eval(list(self.presampled_contacts.keys())[0]))
        # Simply unpack the elements from the sampled datasets found in the
        # json file.
        self.contact_time_to_throughput_probability = {}
        for time_key in self.presampled_contacts:
            self.contact_time_to_throughput_probability[time_key] = list(zip(
                *self.presampled_contacts[time_key]))
        self.number_samples = len(self.contact_time_to_throughput_probability)

    def get_capacity(self):
        """Returns all contacts with their duration and estimated capacity.

        :return: Returns a dictionary holding all the terminated contacts information.\n
         The key is a format 'contact:node1-node2;time:timestart-timeend'.
         The value is the capacity, in MBytes.
        """
        terminated_contacts = {}
        for id1, id2, time_start_raw, time_end_raw in ContactParser(
                self.dataset):
            # todo: take time format in consideration. For now just make the
            # difference and assume unix timestamp.
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
