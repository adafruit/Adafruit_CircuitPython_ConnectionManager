# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Get Connection Manager Tests """

import mocket

import adafruit_connection_manager


def test_get_connection_manager():
    mock_pool = mocket.MocketPool()

    connection_manager_1 = adafruit_connection_manager.get_connection_manager(mock_pool)
    connection_manager_2 = adafruit_connection_manager.get_connection_manager(mock_pool)

    assert connection_manager_1 == connection_manager_2


def test_different_connection_manager_different_pool(  # pylint: disable=unused-argument
    circuitpython_socketpool_module, adafruit_esp32spi_socketpool_module
):
    radio_wifi = mocket.MockRadio.Radio()
    radio_esp = mocket.MockRadio.ESP_SPIcontrol()

    socket_pool_wifi = adafruit_connection_manager.get_radio_socketpool(radio_wifi)
    socket_pool_esp = adafruit_connection_manager.get_radio_socketpool(radio_esp)

    connection_manager_wifi = adafruit_connection_manager.get_connection_manager(
        socket_pool_wifi
    )
    connection_manager_esp = adafruit_connection_manager.get_connection_manager(
        socket_pool_esp
    )

    assert connection_manager_wifi != connection_manager_esp
