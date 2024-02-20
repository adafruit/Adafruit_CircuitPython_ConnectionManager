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
