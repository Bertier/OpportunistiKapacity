#!/usr/bin/python3
"""
Helper functions to estimate the throughput according to distance.
"""
import numpy as np
from scipy.constants import speed_of_light
import configparser

name_configuration_file = 'opportunistiKapacity.cfg'

"""
CONSTANTS
"""
cfg = configparser.ConfigParser()
configuration = cfg.read(name_configuration_file)

min_rssi = cfg.getint('communications', 'min_rssi', fallback=87)
freq = cfg.getfloat('communications', 'frequency', fallback=5180) * 10 ** 6
wavelength = speed_of_light / freq


threshold_rssi = np.array(
    [0, -55, -57, -58, -59, -63, -67, -70, -72, -75, -min_rssi])
data_rate = [866, 780, 650, 585, 520, 390, 260, 195, 130, 65]

"""
BASIC FUNCTIONS
"""


def linear(rssi, a, b):
    return a * rssi + b


def Wifi5_goodput_bottleneck(rssi):
    """ Returns the maximum speed achieved experimentally
    :param rssi:
    :return: The goodput bottleneck. Maximum achieved goodput speed with OnePlus 5T phones.
    """
    return 24.267885


"""
PROPAGATION MODELS
Takes a distance, returns the loss in dBm.
"""


def freespace_loss(distance):
    """Returns the expected signal loss using the free-space loss model.
    :param distance: Distance in meters.
    :return: The signal loss in dBm.
    """
    loss = 20 * np.log10(4 * np.pi * distance / wavelength)
    return loss if loss > 0 else 0


def logDistance_loss(distance, alpha=3):
    """Returns the expected signal loss using the log-distance loss model.

    :param distance: Distance in meters.
    :param alpha: Attenuation exponent. Fixed to 3 by default.
    :return: The signal loss in dBm.
    """
    d0 = 1
    if distance > d0:
        loss = freespace_loss(d0) + 10 * alpha * np.log10(distance / d0)
        return loss if loss > 0 else 0
    else:
        return freespace_loss(distance)


def twoRay_loss(distance, epsilon_r=1.00673130, height=1.39):
    """Returns the expected signal loss using the two-ray ground reflection loss model.

    :param distance: Distance in meters.
    :param epsilon_r: Reflection coefficient.
    :param height: Height of devices from the ground.
    :return: The signal loss in dBm.
    """
    height_sender = height
    height_receiver = height
    d_reflection = np.sqrt(
        (distance ** 2) + (height_sender + height_receiver) ** 2)
    d_LoS = np.sqrt((distance ** 2) + (height_sender - height_receiver) ** 2)
    phi = 2 * np.pi * ((d_LoS - d_reflection) / wavelength)
    sin_theta = (height_sender + height_receiver) / d_reflection
    cos_theta = distance / d_reflection
    gamma = (sin_theta - np.sqrt(epsilon_r - cos_theta ** 2)) / \
            (sin_theta + np.sqrt(epsilon_r - cos_theta ** 2))
    loss_two_ray = 10 * np.log10((4 * np.pi * (distance / wavelength) * 1 / (
        np.sqrt(((1 + gamma * np.cos(phi)) ** 2 + gamma ** 2 * np.sin(phi) ** 2)))) ** 2)
    return loss_two_ray if loss_two_ray > 0 else 0


"""
MODULATION SCHEMES
Take the rssi as an argument, returns the expected throughput.
"""


def Wifi5_empirical_goodput(rssi):
    """Turns a signal strength into a goodput value.

    :param rssi: Expected signal strength (in dBm) between the two nodes.
    :return: Expected goodput for the given rssi.
    """
    rssi = np.absolute(rssi)
    """
    ]0,64] = Wifi5_goodput_bottleneck
    ]64,71] = -0.359363*x+42.356715
    ]71,82] = -0.791134*x+66.438033
    ]82,88] = -0.236949*x+21.128388
    """
    limits = [0, 64, 71, 82, min_rssi]
    funcs = [Wifi5_goodput_bottleneck, linear, linear, linear]
    args = [-1, [-0.359363, 42.356715],
            [-0.791134, 66.438033], [-0.236949, 21.128388]]
    if rssi > limits[-1]:
        return 0.0
    for j, lower in enumerate(limits):
        if lower < rssi <= limits[j + 1]:
            if hasattr(args[j], "__len__"):
                return funcs[j](rssi, *args[j]) * 8
            else:
                return funcs[j](rssi) * 8
    return "error"


def Wifi5_stepwise_max(rssi):
    """Turns a signal strength into a goodput value.

    :param rssi: Expected signal strength (in dBm) between the two nodes.
    :return: Expected goodput for the given rssi.
    """
    threshold_rssi = np.array(
        [0, -55, -57, -58, -59, -63, -67, -70, -72, -75, -min_rssi])
    data_rate = [
        866.0,
        780.0,
        650.0,
        585.0,
        520.0,
        390.0,
        260.0,
        195.0,
        130.0,
        65.0]
    if rssi >= 0:
        return data_rate[0]
    elif rssi < threshold_rssi[-1]:
        return 0.0
    else:
        return data_rate[np.where(threshold_rssi < rssi)[0][0] - 1]


def Wifi5_stepwise_linear_adjusted(rssi):
    """Turns a signal strength into a goodput value.

    :param rssi: Expected signal strength (in dBm) between the two nodes.
    :return: Expected goodput for the given rssi.
    """
    threshold_rssi = np.array(
        [0, -55, -57, -58, -59, -63, -67, -70, -72, -75, -min_rssi])
    data_rate = [
        866.0,
        780.0,
        650.0,
        585.0,
        520.0,
        390.0,
        260.0,
        195.0,
        130.0,
        65.0]
    if rssi >= 0:
        return data_rate[0]
    elif rssi < threshold_rssi[-1]:
        return 0.0
    elif np.where(threshold_rssi <= rssi)[0][0] - 1 == len(data_rate) - 1:
        return rssi * 4.33 + 390
    else:
        return data_rate[np.where(threshold_rssi < rssi)[0][0] - 1]


def Wifi5_stepwise_fit(rssi):
    """Turns a signal strength into a goodput value.

    :param rssi: Expected signal strength (in dBm) between the two nodes.
    :return: Expected goodput for the given rssi.
    """
    threshold_rssi = np.array(
        [0, -55, -57, -58, -59, -63, -67, -70, -72, -75, -min_rssi])
    data_rate = np.array([22.894102,
                          24.934630,
                          24.119049,
                          24.727494,
                          23.782886,
                          20.275357,
                          17.555846,
                          14.414938,
                          8.225040,
                          3.574197]) * 8
    if rssi >= 0:
        return data_rate[0]
    elif rssi <= threshold_rssi[-1]:
        return 0.0
    else:
        return data_rate[np.where(threshold_rssi < rssi)[0][0] - 1]


"""
HELPER FUNCTIONS
"""


def RSSI_TO_BPS(rssi, modulation_scheme=Wifi5_empirical_goodput):
    """Helper function to turn a list of rssi into a list of goodput.
    :param rssi: Rssi value (int or float) or list of rssi values.
    :param modulation_scheme: Chosen modulation scheme. Refer to array 'modulation_schemes'
    :return: Expected Mbits per second.
    """
    if isinstance(rssi, (list, tuple, np.ndarray)):
        res = []
        if isinstance(rssi, np.ndarray):
            original_shape = rssi.shape
            rssi = rssi.flatten()
        for r in rssi:
            res.append(modulation_scheme(r))
        if not isinstance(rssi, np.ndarray):
            return res
        else:
            return np.array(res).reshape(original_shape)
    elif isinstance(rssi, (float, int)):
        return modulation_scheme(rssi)
    else:
        raise ValueError("Data type not understood by model.")


def DISTANCE_TO_RSSI(distance, Tx=9.19, pathloss=freespace_loss):
    """Helper function to turn a distance into an expected RSSI.

    :param distance: Distance in meters.
    :param Tx: Emitting power.
    :param pathloss: Propagation model used (path loss).
    :return: The expected RSSI in dBm.
    """
    if isinstance(distance, (list, tuple, np.ndarray)):
        res = []
        if isinstance(distance, np.ndarray):
            original_shape = distance.shape
            distance = distance.flatten()
        for d in distance:
            res.append(Tx - pathloss(d))
        if not isinstance(distance, np.ndarray):
            return res
        else:
            return np.array(res).reshape(original_shape)
    elif isinstance(distance, (float, int)):
        return Tx - pathloss(distance)
    else:
        raise ValueError("Data type not understood by model")


propagation_models = [freespace_loss, logDistance_loss, twoRay_loss]
modulation_schemes = [
    Wifi5_empirical_goodput,
    Wifi5_stepwise_max,
    Wifi5_stepwise_linear_adjusted,
    Wifi5_stepwise_fit]
propagation_models_names = [
    freespace_loss.__name__,
    logDistance_loss.__name__,
    twoRay_loss.__name__]
modulation_schemes_names = [
    Wifi5_empirical_goodput.__name__,
    Wifi5_stepwise_max.__name__,
    Wifi5_stepwise_linear_adjusted.__name__,
    Wifi5_stepwise_fit.__name__]
