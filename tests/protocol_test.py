# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

import mocket
import pytest

import adafruit_connection_manager

IP = "1.2.3.4"
HOST1 = "wifitest.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_get_https_no_ssl():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify not sending in a SSL context for a HTTPS call errors
    with pytest.raises(AttributeError) as context:
        connection_manager.get_socket(HOST1, 443, "https:")
    assert "ssl_context must be set" in str(context)


def test_connect_https():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.return_value = mock_socket_1

    ssl = mocket.SSLContext()
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTPS call changes the port to 443
    connection_manager.get_socket(HOST1, 443, "https:", ssl_context=ssl)
    mock_socket_1.connect.assert_called_once_with((HOST1, 443))


def test_connect_http():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTP call does not change the port to 443
    connection_manager.get_socket(HOST1, 80, "http:")
    mock_socket_1.connect.assert_called_once_with((IP, 80))
