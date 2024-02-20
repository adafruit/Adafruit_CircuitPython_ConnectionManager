# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Setup Tests """

import sys

import mocket


# pylint: disable=unused-argument
def set_interface(iface):
    """Helper to set the global internet interface"""


socketpool_module = type(sys)("socketpool")
socketpool_module.SocketPool = mocket.MocketPool
sys.modules["socketpool"] = socketpool_module

esp32spi_module = type(sys)("adafruit_esp32spi")
esp32spi_socket_module = type(sys)("adafruit_esp32spi_socket")
esp32spi_socket_module.set_interface = set_interface
sys.modules["adafruit_esp32spi"] = esp32spi_module
sys.modules["adafruit_esp32spi.adafruit_esp32spi_socket"] = esp32spi_socket_module

wiznet5k_module = type(sys)("adafruit_wiznet5k")
wiznet5k_socket_module = type(sys)("adafruit_wiznet5k_socket")
wiznet5k_socket_module.set_interface = set_interface
sys.modules["adafruit_wiznet5k"] = wiznet5k_module
sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socket"] = wiznet5k_socket_module
