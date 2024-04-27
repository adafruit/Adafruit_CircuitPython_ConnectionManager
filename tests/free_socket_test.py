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
    assert connection_manager.managed_socket_count == 0
    assert connection_manager.available_socket_count == 0

    # validate socket is tracked and not available
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    key = (mocket.MOCK_HOST_1, 80, "http:", None)
    assert socket == mock_socket_1
    assert socket not in connection_manager._available_sockets
    assert key in connection_manager._managed_socket_by_key
    assert connection_manager.managed_socket_count == 1
    assert connection_manager.available_socket_count == 0

    # validate socket is tracked and is available
    connection_manager.free_socket(socket)
    assert socket in connection_manager._available_sockets
    assert key in connection_manager._managed_socket_by_key
    assert connection_manager.managed_socket_count == 1
    assert connection_manager.available_socket_count == 1


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
    assert connection_manager.managed_socket_count == 0
    assert connection_manager.available_socket_count == 0

    # validate socket is tracked and not available
    socket_1 = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket_1 == mock_socket_1
    assert socket_1 not in connection_manager._available_sockets
    assert connection_manager.managed_socket_count == 1
    assert connection_manager.available_socket_count == 0

    socket_2 = connection_manager.get_socket(mocket.MOCK_HOST_2, 80, "http:")
    assert socket_2 == mock_socket_2
    assert connection_manager.managed_socket_count == 2
    assert connection_manager.available_socket_count == 0

    # validate socket is tracked and is available
    connection_manager.free_socket(socket_1)
    assert socket_1 in connection_manager._available_sockets
    assert connection_manager.managed_socket_count == 2
    assert connection_manager.available_socket_count == 1

    # validate socket is no longer tracked
    connection_manager._free_sockets()
    assert socket_1 not in connection_manager._available_sockets
    assert socket_2 not in connection_manager._available_sockets
    mock_socket_1.close.assert_called_once()
    assert connection_manager.managed_socket_count == 1
    assert connection_manager.available_socket_count == 0
