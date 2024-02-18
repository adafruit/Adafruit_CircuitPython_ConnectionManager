# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" FakeSLLSocket Tests """

import mocket
import pytest

import adafruit_connection_manager


def test_connect_https():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    radio = mocket.MockRadio.ESP_SPIcontrol()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTPS call for a board without built in WiFi gets a _FakeSSLSocket
    socket = connection_manager.get_socket(
        mocket.MOCK_HOST_1, 443, "https:", ssl_context=ssl_context
    )
    assert socket != mock_socket_1
    assert socket._socket == mock_socket_1
    assert isinstance(socket, adafruit_connection_manager._FakeSSLSocket)


def test_connect_https_not_supported():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    radio = mocket.MockRadio.WIZNET5K()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTPS call for a board without built in WiFi and SSL support errors
    with pytest.raises(AttributeError) as context:
        connection_manager.get_socket(
            mocket.MOCK_HOST_1, 443, "https:", ssl_context=ssl_context
        )
    assert "This radio does not support TLS/HTTPS" in str(context)
