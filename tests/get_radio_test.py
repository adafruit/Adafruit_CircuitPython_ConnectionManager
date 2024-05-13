# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Get socketpool and ssl_context Tests """

import ssl
from unittest import mock

import mocket
import pytest

import adafruit_connection_manager


def test__get_radio_hash_key():
    radio = mocket.MockRadio.Radio()
    assert adafruit_connection_manager._get_radio_hash_key(radio) == hash(radio)


def test__get_radio_hash_key_not_hashable():
    radio = mocket.MockRadio.Radio()

    with mock.patch("builtins.hash", side_effect=TypeError()):
        assert adafruit_connection_manager._get_radio_hash_key(radio) == "Radio"


def test_get_radio_socketpool_wifi(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert isinstance(socket_pool, mocket.MocketPool)
    assert socket_pool in adafruit_connection_manager._global_socketpools.values()


def test_get_radio_socketpool_esp32spi(  # pylint: disable=unused-argument
    adafruit_esp32spi_socketpool_module,
):
    radio = mocket.MockRadio.ESP_SPIcontrol()
    socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool.__name__ == "adafruit_esp32spi_socketpool"
    assert socket_pool in adafruit_connection_manager._global_socketpools.values()


def test_get_radio_socketpool_wiznet5k(  # pylint: disable=unused-argument
    adafruit_wiznet5k_socketpool_module,
):
    radio = mocket.MockRadio.WIZNET5K()
    with mock.patch("sys.implementation", return_value=[9, 0, 0]):
        socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool.__name__ == "adafruit_wiznet5k_socketpool"
    assert socket_pool in adafruit_connection_manager._global_socketpools.values()


def test_get_radio_socketpool_cpython():
    radio = adafruit_connection_manager.CPythonNetwork()
    socket_pool = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool.__name__ == "socket"
    assert socket_pool in adafruit_connection_manager._global_socketpools.values()


def test_get_radio_socketpool_unsupported():
    radio = mocket.MockRadio.Unsupported()
    with pytest.raises(ValueError) as context:
        adafruit_connection_manager.get_radio_socketpool(radio)
    assert "Unsupported radio class" in str(context)


def test_get_radio_socketpool_returns_same_one(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    socket_pool_1 = adafruit_connection_manager.get_radio_socketpool(radio)
    socket_pool_2 = adafruit_connection_manager.get_radio_socketpool(radio)
    assert socket_pool_1 == socket_pool_2
    assert socket_pool_1 in adafruit_connection_manager._global_socketpools.values()


def test_get_radio_ssl_context_wifi(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_context, ssl.SSLContext)
    assert ssl_context in adafruit_connection_manager._global_ssl_contexts.values()


def test_get_radio_ssl_context_esp32spi(  # pylint: disable=unused-argument
    adafruit_esp32spi_socketpool_module,
):
    radio = mocket.MockRadio.ESP_SPIcontrol()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_context, adafruit_connection_manager._FakeSSLContext)
    assert ssl_context in adafruit_connection_manager._global_ssl_contexts.values()


def test_get_radio_ssl_context_wiznet5k(  # pylint: disable=unused-argument
    adafruit_wiznet5k_socketpool_module,
):
    radio = mocket.MockRadio.WIZNET5K()
    with mock.patch("sys.implementation", return_value=[9, 0, 0]):
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_context, adafruit_connection_manager._FakeSSLContext)
    assert ssl_context in adafruit_connection_manager._global_ssl_contexts.values()


def test_get_radio_ssl_context_cpython():
    radio = adafruit_connection_manager.CPythonNetwork()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert isinstance(ssl_context, ssl.SSLContext)
    assert ssl_context in adafruit_connection_manager._global_ssl_contexts.values()


def test_get_radio_ssl_context_unsupported():
    radio = mocket.MockRadio.Unsupported()
    with pytest.raises(ValueError) as context:
        adafruit_connection_manager.get_radio_ssl_context(radio)
    assert "Unsupported radio class" in str(context)


def test_get_radio_ssl_context_returns_same_one(  # pylint: disable=unused-argument
    circuitpython_socketpool_module,
):
    radio = mocket.MockRadio.Radio()
    ssl_context_1 = adafruit_connection_manager.get_radio_ssl_context(radio)
    ssl_context_2 = adafruit_connection_manager.get_radio_ssl_context(radio)
    assert ssl_context_1 == ssl_context_2
    assert ssl_context_1 in adafruit_connection_manager._global_ssl_contexts.values()
