# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Get socketpool and ssl_context Tests """

import ssl
from unittest import mock

import mocket
import pytest

import adafruit_connection_manager


def test_get_radio_socketpool_wifi(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert isinstance(socket_pool, mocket.MocketPool)


def test_get_radio_socketpool_esp32spi(  # pylint: disable=unused-argument
    adafruit_esp32spi_socket_module,
):
    radio = mocket.MockRadio.ESP_SPIcontrol()
    socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool.__name__ == "adafruit_esp32spi_socket"


def test_get_radio_socketpool_wiznet5k(  # pylint: disable=unused-argument
    adafruit_wiznet5k_socket_module,
):
    radio = mocket.MockRadio.WIZNET5K()
    with mock.patch("sys.implementation", return_value=[9, 0, 0]):
        socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool.__name__ == "adafruit_wiznet5k_socket"


def test_get_radio_socketpool_unsupported():
    radio = mocket.MockRadio.Unsupported()
    with pytest.raises(AttributeError) as context:
        adafruit_connection_manager.get_radio_socketpool(radio)
    assert "Unsupported radio class" in str(context)


def test_get_radio_socketpool_returns_same_one(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    socket_pool_1 = adafruit_connection_manager.get_radio_socketpool(radio)
    socket_pool_2 = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool_1 == socket_pool_2


def test_get_radio_ssl_context_wifi(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    ssl_contexts = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_contexts, ssl.SSLContext)


def test_get_radio_ssl_context_esp32spi(  # pylint: disable=unused-argument
    adafruit_esp32spi_socket_module,
):
    radio = mocket.MockRadio.ESP_SPIcontrol()
    ssl_contexts = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_contexts, adafruit_connection_manager._FakeSSLContext)


def test_get_radio_ssl_context_wiznet5k(  # pylint: disable=unused-argument
    adafruit_wiznet5k_socket_module,
):
    radio = mocket.MockRadio.WIZNET5K()
    with mock.patch("sys.implementation", return_value=[9, 0, 0]):
        ssl_contexts = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_contexts, adafruit_connection_manager._FakeSSLContext)


def test_get_radio_ssl_context_unsupported():
    radio = mocket.MockRadio.Unsupported()
    with pytest.raises(AttributeError) as context:
        adafruit_connection_manager.get_radio_ssl_context(radio)
    assert "Unsupported radio class" in str(context)


def test_get_radio_ssl_context_returns_same_one(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    ssl_contexts_1 = adafruit_connection_manager.get_radio_ssl_context(radio)
    ssl_contexts_2 = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert ssl_contexts_1 == ssl_contexts_2
