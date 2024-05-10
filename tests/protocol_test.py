# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

import mocket
import pytest

import adafruit_connection_manager


def test_get_https_no_ssl():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify not sending in a SSL context for a HTTPS call errors
    with pytest.raises(ValueError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_1, 443, "https:")
    assert "ssl_context must be provided if using ssl" in str(context)


def test_connect_https():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    mock_ssl_context = mocket.SSLContext()
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTPS call changes the port to 443
    connection_manager.get_socket(
        mocket.MOCK_HOST_1, 443, "https:", ssl_context=mock_ssl_context
    )
    mock_socket_1.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    mock_ssl_context.wrap_socket.assert_called_once()


def test_connect_http():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTP call does not change the port to 443
    connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    mock_socket_1.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
