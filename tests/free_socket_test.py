# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Free Socket Tests """

import mocket
import pytest

import adafruit_connection_manager


def test_free_socket():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate socket is tracked and not available
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    key = (mocket.MOCK_HOST_1, 80, "http:", None)
    assert socket == mock_socket_1
    assert socket in connection_manager._available_socket
    assert connection_manager._available_socket[socket] is False
    assert key in connection_manager._open_sockets

    # validate socket is tracked and is available
    connection_manager.free_socket(socket)
    assert socket in connection_manager._available_socket
    assert connection_manager._available_socket[socket] is True
    assert key in connection_manager._open_sockets


def test_free_socket_not_managed():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate not managed socket errors
    with pytest.raises(RuntimeError) as context:
        connection_manager.free_socket(mock_socket_1)
    assert "Socket not managed" in str(context)


def test_free_sockets():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate socket is tracked and not available
    socket_1 = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket_1 == mock_socket_1
    assert socket_1 in connection_manager._available_socket
    assert connection_manager._available_socket[socket_1] is False

    socket_2 = connection_manager.get_socket(mocket.MOCK_HOST_2, 80, "http:")
    assert socket_2 == mock_socket_2

    # validate socket is tracked and is available
    connection_manager.free_socket(socket_1)
    assert socket_1 in connection_manager._available_socket
    assert connection_manager._available_socket[socket_1] is True

    # validate socket is no longer tracked
    connection_manager._free_sockets()
    assert socket_1 not in connection_manager._available_socket
    assert socket_2 in connection_manager._available_socket
    mock_socket_1.close.assert_called_once()


def test_get_key_for_socket():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate tracked socket has correct key
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    key = (mocket.MOCK_HOST_1, 80, "http:", None)
    assert connection_manager._get_key_for_socket(socket) == key


def test_get_key_for_socket_not_managed():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate untracked socket has no key
    assert connection_manager._get_key_for_socket(mock_socket_1) is None
