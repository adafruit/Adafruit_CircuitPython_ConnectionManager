# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Setup Tests """

import sys

import mocket
import pytest


# pylint: disable=unused-argument
def set_interface(iface):
    """Helper to set the global internet interface"""


@pytest.fixture
def circuitpython_socketpool_module():
    socketpool_module = type(sys)("socketpool")
    socketpool_module.SocketPool = mocket.MocketPool
    sys.modules["socketpool"] = socketpool_module
    yield
    del sys.modules["socketpool"]


@pytest.fixture
def adafruit_esp32spi_socket_module():
    esp32spi_module = type(sys)("adafruit_esp32spi")
    esp32spi_socket_module = type(sys)("adafruit_esp32spi_socket")
    esp32spi_socket_module.set_interface = set_interface
    sys.modules["adafruit_esp32spi"] = esp32spi_module
    sys.modules["adafruit_esp32spi.adafruit_esp32spi_socket"] = esp32spi_socket_module
    yield
    del sys.modules["adafruit_esp32spi"]
    del sys.modules["adafruit_esp32spi.adafruit_esp32spi_socket"]


@pytest.fixture
def adafruit_wiznet5k_socket_module():
    wiznet5k_module = type(sys)("adafruit_wiznet5k")
    wiznet5k_socket_module = type(sys)("adafruit_wiznet5k_socket")
    wiznet5k_socket_module.set_interface = set_interface
    wiznet5k_socket_module.SOCK_STREAM = 0x21
    sys.modules["adafruit_wiznet5k"] = wiznet5k_module
    sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socket"] = wiznet5k_socket_module
    yield
    del sys.modules["adafruit_wiznet5k"]
    del sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socket"]


@pytest.fixture
def adafruit_wiznet5k_with_ssl_socket_module():
    wiznet5k_module = type(sys)("adafruit_wiznet5k")
    wiznet5k_socket_module = type(sys)("adafruit_wiznet5k_socket")
    wiznet5k_socket_module.set_interface = set_interface
    wiznet5k_socket_module.SOCK_STREAM = 1
    sys.modules["adafruit_wiznet5k"] = wiznet5k_module
    sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socket"] = wiznet5k_socket_module
    yield
    del sys.modules["adafruit_wiznet5k"]
    del sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socket"]


@pytest.fixture(autouse=True)
def reset_connection_manager(monkeypatch):
    monkeypatch.setattr(
        "adafruit_connection_manager._global_connection_managers",
        {},
    )
    monkeypatch.setattr(
        "adafruit_connection_manager._global_socketpools",
        {},
    )
    monkeypatch.setattr(
        "adafruit_connection_manager._global_ssl_contexts",
        {},
    )
