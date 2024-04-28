# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Close Socket Tests """

import mocket
import pytest

import adafruit_connection_manager


def test_close_socket():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate socket is tracked
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    key = (mocket.MOCK_HOST_1, 80, "http:", None)
    assert socket == mock_socket_1
    assert socket not in connection_manager._available_sockets
    assert key in connection_manager._managed_socket_by_key

    # validate socket is no longer tracked
    connection_manager.close_socket(socket)
    assert socket not in connection_manager._available_sockets
    assert key not in connection_manager._managed_socket_by_key


def test_close_socket_not_managed():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # validate not managed socket errors
    with pytest.raises(RuntimeError) as context:
        connection_manager.close_socket(mock_socket_1)
    assert "Socket not managed" in str(context)
