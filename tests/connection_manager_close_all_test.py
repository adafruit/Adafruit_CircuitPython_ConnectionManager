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
    assert connection_manager_1.managed_socket_count == 0
    assert connection_manager_1.available_socket_count == 0
    connection_manager_2 = adafruit_connection_manager.get_connection_manager(
        mock_pool_2
    )
    assert connection_manager_2.managed_socket_count == 0
    assert connection_manager_2.available_socket_count == 0
    assert len(adafruit_connection_manager._global_connection_managers) == 2

    socket_1 = connection_manager_1.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_1.managed_socket_count == 1
    assert connection_manager_1.available_socket_count == 0
    assert connection_manager_2.managed_socket_count == 0
    assert connection_manager_2.available_socket_count == 0
    socket_2 = connection_manager_2.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_2.managed_socket_count == 1
    assert connection_manager_2.available_socket_count == 0

    adafruit_connection_manager.connection_manager_close_all()
    assert connection_manager_1.managed_socket_count == 0
    assert connection_manager_1.available_socket_count == 0
    assert connection_manager_2.managed_socket_count == 0
    assert connection_manager_2.available_socket_count == 0
    socket_1.close.assert_called_once()
    socket_2.close.assert_called_once()


def test_connection_manager_close_all_single():
    mock_pool_1 = mocket.MocketPool()
    mock_pool_2 = mocket.MocketPool()
    assert mock_pool_1 != mock_pool_2

    connection_manager_1 = adafruit_connection_manager.get_connection_manager(
        mock_pool_1
    )
    assert connection_manager_1.managed_socket_count == 0
    assert connection_manager_1.available_socket_count == 0
    connection_manager_2 = adafruit_connection_manager.get_connection_manager(
        mock_pool_2
    )
    assert connection_manager_2.managed_socket_count == 0
    assert connection_manager_2.available_socket_count == 0
    assert len(adafruit_connection_manager._global_connection_managers) == 2

    socket_1 = connection_manager_1.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_1.managed_socket_count == 1
    assert connection_manager_1.available_socket_count == 0
    assert connection_manager_2.managed_socket_count == 0
    assert connection_manager_2.available_socket_count == 0
    socket_2 = connection_manager_2.get_socket(mocket.MOCK_HOST_1, 80, "http:")
    assert connection_manager_2.managed_socket_count == 1
    assert connection_manager_2.available_socket_count == 0

    adafruit_connection_manager.connection_manager_close_all(mock_pool_1)
    assert connection_manager_1.managed_socket_count == 0
    assert connection_manager_1.available_socket_count == 0
    assert connection_manager_2.managed_socket_count == 1
    assert connection_manager_2.available_socket_count == 0
    socket_1.close.assert_called_once()
    socket_2.close.assert_not_called()


def test_connection_manager_close_all_untracked():
    mock_pool_1 = mocket.MocketPool()
    with pytest.raises(RuntimeError) as context:
        adafruit_connection_manager.connection_manager_close_all(mock_pool_1)
    assert "SocketPool not managed" in str(context)


def test_connection_manager_close_all_single_release_references_false(  # pylint: disable=unused-argument
    circuitpython_socketpool_module, adafruit_esp32spi_socketpool_module
):
    radio_wifi = mocket.MockRadio.Radio()
    radio_esp = mocket.MockRadio.ESP_SPIcontrol()

    socket_pool_wifi = adafruit_connection_manager.get_radio_socketpool(radio_wifi)
    socket_pool_esp = adafruit_connection_manager.get_radio_socketpool(radio_esp)

    ssl_context_wifi = adafruit_connection_manager.get_radio_ssl_context(radio_wifi)
    ssl_context_esp = adafruit_connection_manager.get_radio_ssl_context(radio_esp)

    connection_manager_wifi = adafruit_connection_manager.get_connection_manager(
        socket_pool_wifi
    )
    connection_manager_esp = adafruit_connection_manager.get_connection_manager(
        socket_pool_esp
    )

    assert socket_pool_wifi != socket_pool_esp
    assert ssl_context_wifi != ssl_context_esp
    assert connection_manager_wifi != connection_manager_esp

    adafruit_connection_manager.connection_manager_close_all(
        socket_pool_wifi, release_references=False
    )

    assert socket_pool_wifi in adafruit_connection_manager._global_socketpools.values()
    assert socket_pool_esp in adafruit_connection_manager._global_socketpools.values()

    assert ssl_context_wifi in adafruit_connection_manager._global_ssl_contexts.values()
    assert ssl_context_esp in adafruit_connection_manager._global_ssl_contexts.values()

    assert (
        socket_pool_wifi
        in adafruit_connection_manager._global_connection_managers.keys()
    )
    assert (
        socket_pool_esp
        in adafruit_connection_manager._global_connection_managers.keys()
    )


def test_connection_manager_close_all_single_release_references_true(  # pylint: disable=unused-argument
    circuitpython_socketpool_module, adafruit_esp32spi_socketpool_module
):
    radio_wifi = mocket.MockRadio.Radio()
    radio_esp = mocket.MockRadio.ESP_SPIcontrol()

    socket_pool_wifi = adafruit_connection_manager.get_radio_socketpool(radio_wifi)
    socket_pool_esp = adafruit_connection_manager.get_radio_socketpool(radio_esp)

    ssl_context_wifi = adafruit_connection_manager.get_radio_ssl_context(radio_wifi)
    ssl_context_esp = adafruit_connection_manager.get_radio_ssl_context(radio_esp)

    connection_manager_wifi = adafruit_connection_manager.get_connection_manager(
        socket_pool_wifi
    )
    connection_manager_esp = adafruit_connection_manager.get_connection_manager(
        socket_pool_esp
    )

    assert socket_pool_wifi != socket_pool_esp
    assert ssl_context_wifi != ssl_context_esp
    assert connection_manager_wifi != connection_manager_esp

    adafruit_connection_manager.connection_manager_close_all(
        socket_pool_wifi, release_references=True
    )

    assert (
        socket_pool_wifi not in adafruit_connection_manager._global_socketpools.values()
    )
    assert socket_pool_esp in adafruit_connection_manager._global_socketpools.values()

    assert (
        ssl_context_wifi
        not in adafruit_connection_manager._global_ssl_contexts.values()
    )
    assert ssl_context_esp in adafruit_connection_manager._global_ssl_contexts.values()

    assert (
        socket_pool_wifi
        not in adafruit_connection_manager._global_connection_managers.keys()
    )
    assert (
        socket_pool_esp
        in adafruit_connection_manager._global_connection_managers.keys()
    )
