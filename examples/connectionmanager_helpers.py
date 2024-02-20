# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import os

import adafruit_requests
import wifi

import adafruit_connection_manager

TEXT_URL = "http://wifitest.adafruit.com/testwifi/index.html"

wifi_ssid = os.getenv("CIRCUITPY_WIFI_SSID")
wifi_password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

radio = wifi.radio
while not radio.connected:
    radio.connect(wifi_ssid, wifi_password)

# get the pool and ssl_context from the helpers:
pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)

# get request session
requests = adafruit_requests.Session(pool, ssl_context)

# make request
print("-" * 40)
print(f"Fetching from {TEXT_URL}")

response = requests.get(TEXT_URL)
response_text = response.text
response.close()

print(f"Text Response {response_text}")
print("-" * 40)
