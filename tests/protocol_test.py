# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

import mocket
import pytest
import adafruit_connection_manager

IP = "1.2.3.4"
HOST = "wifitest.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_get_https_no_ssl():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    connection_manager = adafruit_connection_manager.ConnectionManager(pool)
    with pytest.raises(AttributeError):
        connection_manager.get_socket(HOST, 443, "https:")


def test_connect_https():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    ssl = mocket.SSLContext()

    connection_manager = adafruit_connection_manager.ConnectionManager(pool)
    connection_manager.get_socket(HOST, 443, "https:", ssl_context=ssl)

    sock.connect.assert_called_once_with((HOST, 443))


def test_connect_http():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    connection_manager = adafruit_connection_manager.ConnectionManager(pool)
    connection_manager.get_socket(HOST, 80, "http:")

    sock.connect.assert_called_once_with((IP, 80))
