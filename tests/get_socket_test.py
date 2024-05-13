# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Get Socket Tests """

from unittest import mock

import mocket
import pytest

import adafruit_connection_manager


def test_get_socket():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get socket
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1


def test_get_socket_different_session():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get socket
    socket = connection_manager.get_socket(
        mocket.MOCK_HOST_1, 80, "http:", session_id="1"
    )
    assert socket == mock_socket_1

    # get socket on different session
    socket = connection_manager.get_socket(
        mocket.MOCK_HOST_1, 80, "http:", session_id="2"
    )
    assert socket == mock_socket_2


def test_get_socket_flagged_free():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get a socket and then mark as free
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1
    connection_manager.free_socket(socket)

    # get a socket for the same host, should be the same one
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1


def test_get_socket_not_flagged_free():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # get a socket but don't mark as free
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1

    # get a socket for the same host, should be a different one
    with pytest.raises(RuntimeError) as context:
        socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert "An existing socket is already connected" in str(context)


def test_get_socket_os_error():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        OSError("OSError 1"),
        mock_socket_1,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to get a socket that returns a OSError
    with pytest.raises(OSError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert "OSError 1" in str(context)


def test_get_socket_runtime_error():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        RuntimeError("RuntimeError 1"),
        mock_socket_1,
    ]

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to get a socket that returns a RuntimeError
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert "RuntimeError 1" in str(context)


def test_get_socket_connect_memory_error():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]
    mock_socket_1.connect.side_effect = MemoryError("MemoryError 1")

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to connect a socket that returns a MemoryError
    with pytest.raises(MemoryError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert "MemoryError 1" in str(context)


def test_get_socket_connect_os_error():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        mock_socket_2,
    ]
    mock_socket_1.connect.side_effect = OSError("OSError 1")

    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # try to connect a socket that returns a OSError
    with pytest.raises(OSError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert "OSError 1" in str(context)


def test_get_socket_runtime_error_ties_again_at_least_one_free():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        RuntimeError(),
        mock_socket_2,
    ]

    free_sockets_mock = mock.Mock()
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)
    connection_manager._free_sockets = free_sockets_mock

    # get a socket and then mark as free
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1
    connection_manager.free_socket(socket)
    free_sockets_mock.assert_not_called()

    # try to get a socket that returns a RuntimeError and at least one is flagged as free
    socket = connection_manager.get_socket(mocket.MOCK_HOST_2, 80, "http:")
    assert socket == mock_socket_2
    free_sockets_mock.assert_called_once()


def test_get_socket_runtime_error_ties_again_only_once():
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_socket_2 = mocket.Mocket()
    mock_pool.socket.side_effect = [
        mock_socket_1,
        RuntimeError("RuntimeError 1"),
        RuntimeError("RuntimeError 2"),
        RuntimeError("RuntimeError 3"),
        mock_socket_2,
    ]

    free_sockets_mock = mock.Mock()
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)
    connection_manager._free_sockets = free_sockets_mock

    # get a socket and then mark as free
    socket = connection_manager.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert socket == mock_socket_1
    connection_manager.free_socket(socket)
    free_sockets_mock.assert_not_called()

    # try to get a socket that returns a RuntimeError twice
    with pytest.raises(RuntimeError) as context:
        connection_manager.get_socket(mocket.MOCK_HOST_2, 80, "http:")
    assert "RuntimeError 2" in str(context)
    free_sockets_mock.assert_called_once()


def test_fake_ssl_context_connect(  # pylint: disable=unused-argument
    adafruit_esp32spi_socketpool_module,
):
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1

    radio = mocket.MockRadio.ESP_SPIcontrol()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    # verify a HTTPS call gets a _FakeSSLSocket
    socket = connection_manager.get_socket(
        mocket.MOCK_HOST_1, 443, "https:", ssl_context=ssl_context
    )
    assert socket != mock_socket_1
    socket._socket.connect.assert_called_once()


def test_fake_ssl_context_connect_error(  # pylint: disable=unused-argument
    adafruit_esp32spi_socketpool_module,
):
    mock_pool = mocket.MocketPool()
    mock_socket_1 = mocket.Mocket()
    mock_pool.socket.return_value = mock_socket_1
    mock_socket_1.connect.side_effect = RuntimeError("RuntimeError 1")

    radio = mocket.MockRadio.ESP_SPIcontrol()
    ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)
    connection_manager = adafruit_connection_manager.ConnectionManager(mock_pool)

    with pytest.raises(OSError) as context:
        connection_manager.get_socket(
            mocket.MOCK_HOST_1, 443, "https:", ssl_context=ssl_context
        )
    assert "12" in str(context)
    assert "RuntimeError 1" in str(context)
