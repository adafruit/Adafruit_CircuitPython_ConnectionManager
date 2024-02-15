# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

import mocket
import pytest

import adafruit_connection_manager

IP = "1.2.3.4"
HOST1 = "wifitest.adafruit.com"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_close_socket():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate socket is tracked
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    key = (HOST1, 80, "http:", None)
    assert socket == mock_socket_1
    assert socket in connection_manager._available_socket
    assert key in connection_manager._open_sockets

    # validate socket is no longer tracked
    connection_manager.close_socket(socket)
    assert socket not in connection_manager._available_socket
    assert key not in connection_manager._open_sockets


def test_close_socket_not_managed():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate not managed socket errors
    with pytest.raises(RuntimeError) as context:
        connection_manager.close_socket(mock_socket_1)
    assert "Socket not managed" in str(context)
