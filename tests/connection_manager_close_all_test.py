# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Get Connection Manager Tests """

import mocket
import pytest

import adafruit_connection_manager


def test_connection_manager_close_all_all():
    mock_pool_1 = mocket.MocketPool()
    mock_pool_2 = mocket.MocketPool()
    assert mock_pool_1 != mock_pool_2

    connection_manager_1 = adafruit_connection_manager.get_connection_manager(
        mock_pool_1
    )
    assert connection_manager_1.open_sockets == 0
    assert connection_manager_1.freeable_open_sockets == 0
    connection_manager_2 = adafruit_connection_manager.get_connection_manager(
        mock_pool_2
    )
    assert connection_manager_2.open_sockets == 0
    assert connection_manager_2.freeable_open_sockets == 0
    assert len(adafruit_connection_manager._global_connection_managers) == 2

    socket_1 = connection_manager_1.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_1.open_sockets == 1
    assert connection_manager_1.freeable_open_sockets == 0
    assert connection_manager_2.open_sockets == 0
    assert connection_manager_2.freeable_open_sockets == 0
    socket_2 = connection_manager_2.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_2.open_sockets == 1
    assert connection_manager_2.freeable_open_sockets == 0

    adafruit_connection_manager.connection_manager_close_all()
    assert connection_manager_1.open_sockets == 0
    assert connection_manager_1.freeable_open_sockets == 0
    assert connection_manager_2.open_sockets == 0
    assert connection_manager_2.freeable_open_sockets == 0
    socket_1.close.assert_called_once()
    socket_2.close.assert_called_once()


def test_connection_manager_close_all_single():
    mock_pool_1 = mocket.MocketPool()
    mock_pool_2 = mocket.MocketPool()
    assert mock_pool_1 != mock_pool_2

    connection_manager_1 = adafruit_connection_manager.get_connection_manager(
        mock_pool_1
    )
    assert connection_manager_1.open_sockets == 0
    assert connection_manager_1.freeable_open_sockets == 0
    connection_manager_2 = adafruit_connection_manager.get_connection_manager(
        mock_pool_2
    )
    assert connection_manager_2.open_sockets == 0
    assert connection_manager_2.freeable_open_sockets == 0
    assert len(adafruit_connection_manager._global_connection_managers) == 2

    socket_1 = connection_manager_1.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_1.open_sockets == 1
    assert connection_manager_1.freeable_open_sockets == 0
    assert connection_manager_2.open_sockets == 0
    assert connection_manager_2.freeable_open_sockets == 0
    socket_2 = connection_manager_2.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_2.open_sockets == 1
    assert connection_manager_2.freeable_open_sockets == 0

    adafruit_connection_manager.connection_manager_close_all(mock_pool_1)
    assert connection_manager_1.open_sockets == 0
    assert connection_manager_1.freeable_open_sockets == 0
    assert connection_manager_2.open_sockets == 1
    assert connection_manager_2.freeable_open_sockets == 0
    socket_1.close.assert_called_once()
    socket_2.close.assert_not_called()


def test_connection_manager_close_all_untracked():
    mock_pool_1 = mocket.MocketPool()
    with pytest.raises(RuntimeError) as context:
        adafruit_connection_manager.connection_manager_close_all(mock_pool_1)
    assert "SocketPool not managed" in str(context)
