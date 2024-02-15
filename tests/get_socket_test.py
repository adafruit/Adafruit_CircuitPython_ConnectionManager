# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

from unittest import mock

import mocket
import pytest

import adafruit_connection_manager

IP = "1.2.3.4"
HOST1 = "wifitest.adafruit.com"
HOST2 = "wifitest2.adafruit.com"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_get_socket():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get socket
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert socket == mock_socket_1


def test_get_socket_different_session():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get socket
    socket = connection_manager.get_socket(HOST1, 80, "http:", session_id="1")
    assert socket == mock_socket_1

    # get socket on different session
    socket = connection_manager.get_socket(HOST1, 80, "http:", session_id="2")
    assert socket == mock_socket_2


def test_get_socket_flagged_free():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get a socket and then mark as free
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert socket == mock_socket_1
    connection_manager.free_socket(socket)

    # get a socket for the same host, should be the same one
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert socket == mock_socket_1


def test_get_socket_not_flagged_free():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get a socket but don't mark as free
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert socket == mock_socket_1

    # get a socket for the same host, should be a different one
    with pytest.raises(RuntimeError) as context:
        socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert "Socket already connected" in str(context)


def test_get_socket_os_error():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        OSError("OSError"),
        mock_socket_1,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to get a socket that returns a OSError
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(HOST1, 80, "http:")
    assert "Error connecting socket: OSError" in str(context)


def test_get_socket_runtime_error():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        RuntimeError("RuntimeError"),
        mock_socket_1,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to get a socket that returns a RuntimeError
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(HOST1, 80, "http:")
    assert "Error connecting socket: RuntimeError" in str(context)


def test_get_socket_connect_memory_error():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]
    mock_socket_1.connect.side_effect = MemoryError("MemoryError")

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to connect a socket that returns a MemoryError
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(HOST1, 80, "http:")
    assert "Error connecting socket: MemoryError" in str(context)


def test_get_socket_connect_os_error():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]
    mock_socket_1.connect.side_effect = OSError("OSError")

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to connect a socket that returns a OSError
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(HOST1, 80, "http:")
    assert "Error connecting socket: OSError" in str(context)


def test_get_socket_runtime_error_ties_again_at_least_one_free():
    mock_pool = mocket.MocketPool()
    mock_pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    mock_socket_1 = mocket.Mocket(RESPONSE)
    mock_socket_2 = mocket.Mocket(RESPONSE)
    mock_pool.socket.side_effect = [
        mock_socket_1,
        RuntimeError(),
        mock_socket_2,
    ]

    free_sockets_mock = mock.Mock()
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)
    connection_manager._free_sockets = free_sockets_mock

    # get a socket and then mark as free
    socket = connection_manager.get_socket(HOST1, 80, "http:")
    assert socket == mock_socket_1
    connection_manager.free_socket(socket)
    free_sockets_mock.assert_not_called()

    # try to get a socket that returns a RuntimeError and at least one is flagged as free
    socket = connection_manager.get_socket(HOST2, 80, "http:")
    assert socket == mock_socket_2
    free_sockets_mock.assert_called_once()
