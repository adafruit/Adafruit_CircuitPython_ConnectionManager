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


class SocketPool:
    name = None

    def __init__(self, *args, **kwargs):
        pass

    @property
    def __name__(self):
        return self.name


class ESP32SPI_SocketPool(SocketPool):  # pylint: disable=too-few-public-methods
    name = "adafruit_esp32spi_socketpool"


class WIZNET5K_SocketPool(SocketPool):  # pylint: disable=too-few-public-methods
    name = "adafruit_wiznet5k_socketpool"


@pytest.fixture
def circuitpython_socketpool_module():
    socketpool_module = type(sys)("socketpool")
    socketpool_module.SocketPool = mocket.MocketPool
    sys.modules["socketpool"] = socketpool_module
    yield
    del sys.modules["socketpool"]


@pytest.fixture
def adafruit_esp32spi_socketpool_module():
    esp32spi_module = type(sys)("adafruit_esp32spi")
    esp32spi_socket_module = type(sys)("adafruit_esp32spi_socketpool")
    esp32spi_socket_module.SocketPool = ESP32SPI_SocketPool
    sys.modules["adafruit_esp32spi"] = esp32spi_module
    sys.modules["adafruit_esp32spi.adafruit_esp32spi_socketpool"] = (
        esp32spi_socket_module
    )
    yield
    del sys.modules["adafruit_esp32spi"]
    del sys.modules["adafruit_esp32spi.adafruit_esp32spi_socketpool"]


@pytest.fixture
def adafruit_wiznet5k_socketpool_module():
    wiznet5k_module = type(sys)("adafruit_wiznet5k")
    wiznet5k_socketpool_module = type(sys)("adafruit_wiznet5k_socketpool")
    wiznet5k_socketpool_module.SocketPool = WIZNET5K_SocketPool
    wiznet5k_socketpool_module.SOCK_STREAM = 0x21
    sys.modules["adafruit_wiznet5k"] = wiznet5k_module
    sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socketpool"] = (
        wiznet5k_socketpool_module
    )
    yield
    del sys.modules["adafruit_wiznet5k"]
    del sys.modules["adafruit_wiznet5k.adafruit_wiznet5k_socketpool"]


@pytest.fixture(autouse=True)
def reset_connection_manager(monkeypatch):
    monkeypatch.setattr(
        "adafruit_connection_manager._global_socketpool",
        {},
    )
    monkeypatch.setattr(
        "adafruit_connection_manager._global_ssl_contexts",
        {},
    )
