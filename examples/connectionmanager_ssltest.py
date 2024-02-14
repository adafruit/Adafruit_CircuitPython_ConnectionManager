# SPDX-FileCopyrightText: Copyright (c) 2024 Justin Myers
#
# SPDX-License-Identifier: Unlicense

import time
import wifi

import adafruit_connection_manager


adafruit_groups = [
    {
        "heading": "Common hosts",
        "description": "These are common hosts users hit.",
        "success": "yes",
        "fail": "no",
        "subdomains": [
            {"host": "api.fitbit.com"},
            {"host": "api.github.com"},
            {"host": "api.thingspeak.com"},
            {"host": "api.twitter.com"},
            {"host": "discord.com"},
            {"host": "id.twitch.tv"},
            {"host": "oauth2.googleapis.com"},
            {"host": "opensky-network.org"},
            {"host": "www.adafruit.com"},
            {"host": "www.googleapis.com"},
            {"host": "youtube.googleapis.com"},
        ],
    },
    {
        "heading": "Known problem hosts",
        "description": "These are hosts we have run into problems in the past.",
        "success": "yes",
        "fail": "no",
        "subdomains": [
            {"host": "valid-isrgrootx2.letsencrypt.org"},
        ],
    },
]

badssl_groups = [
    {
        "heading": "Certificate Validation (High Risk)",
        "description": (
            "If your browser connects to one of these sites, it could be very easy for an attacker "
            "to see and modify everything on web sites that you visit."
        ),
        "success": "no",
        "fail": "yes",
        "subdomains": [
            {"subdomain": "expired"},
            {"subdomain": "wrong.host"},
            {"subdomain": "self-signed"},
            {"subdomain": "untrusted-root"},
        ],
    },
    {
        "heading": "Interception Certificates (High Risk)",
        "description": (
            "If your browser connects to one of these sites, it could be very easy for an attacker "
            "to see and modify everything on web sites that you visit. This may be due to "
            "interception software installed on your device."
        ),
        "success": "no",
        "fail": "yes",
        "subdomains": [
            {"subdomain": "superfish"},
            {"subdomain": "edellroot"},
            {"subdomain": "dsdtestprovider"},
            {"subdomain": "preact-cli"},
            {"subdomain": "webpack-dev-server"},
        ],
    },
    {
        "heading": "Broken Cryptography (Medium Risk)",
        "description": (
            "If your browser connects to one of these sites, an attacker with enough resources may "
            "be able to see and/or modify everything on web sites that you visit. This is because "
            "your browser supports connections settings that are outdated and known to have "
            "significant security flaws."
        ),
        "success": "no",
        "fail": "yes",
        "subdomains": [
            {"subdomain": "rc4"},
            {"subdomain": "rc4-md5"},
            {"subdomain": "dh480"},
            {"subdomain": "dh512"},
            {"subdomain": "dh1024"},
            {"subdomain": "null"},
        ],
    },
    {
        "heading": "Legacy Cryptography (Moderate Risk)",
        "description": (
            "If your browser connects to one of these sites, your web traffic is probably safe "
            "from attackers in the near future. However, your connections to some sites might "
            "not be using the strongest possible security. Your browser may use these settings in "
            "order to connect to some older sites."
        ),
        "success": "maybe",
        "fail": "yes",
        "subdomains": [
            {"subdomain": "tls-v1-0", "port": 1010},
            {"subdomain": "tls-v1-1", "port": 1011},
            {"subdomain": "cbc"},
            {"subdomain": "3des"},
            {"subdomain": "dh2048"},
        ],
    },
    {
        "heading": "Domain Security Policies",
        "description": (
            "These are special tests for some specific browsers. These tests may be able to tell "
            "whether your browser uses advanced domain security policy mechanisms (HSTS, HPKP, SCT"
            ") to detect illegitimate certificates."
        ),
        "success": "maybe",
        "fail": "yes",
        "subdomains": [
            {"subdomain": "revoked"},
            {"subdomain": "pinning-test"},
            {"subdomain": "no-sct"},
        ],
    },
    {
        "heading": "Secure (Uncommon)",
        "description": (
            "These settings are secure. However, they are less common and even if your browser "
            "doesn't support them you probably won't have issues with most sites."
        ),
        "success": "yes",
        "fail": "maybe",
        "subdomains": [
            {"subdomain": "1000-sans"},
            {"subdomain": "10000-sans"},
            {"subdomain": "sha384"},
            {"subdomain": "sha512"},
            {"subdomain": "rsa8192"},
            {"subdomain": "no-subject"},
            {"subdomain": "no-common-name"},
            {"subdomain": "incomplete-chain"},
        ],
    },
    {
        "heading": "Secure (Common)",
        "description": (
            "These settings are secure and commonly used by sites. Your browser will need to "
            "support most of these in order to connect to sites securely."
        ),
        "success": "yes",
        "fail": "no",
        "subdomains": [
            {"subdomain": "tls-v1-2", "port": 1012},
            {"subdomain": "sha256"},
            {"subdomain": "rsa2048"},
            {"subdomain": "ecc256"},
            {"subdomain": "ecc384"},
            {"subdomain": "extended-validation"},
            {"subdomain": "mozilla-modern"},
        ],
    },
]

pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_contexts(wifi.radio)
connection_manager = adafruit_connection_manager.get_connection_manager(pool)


def check_group(groups, group_name):
    print(f"\nRunning {group_name}")
    for group in groups:
        print(f'\n - {group["heading"]}')
        success = group["success"]
        fail = group["fail"]
        for subdomain in group["subdomains"]:
            if "host" in subdomain:
                host = subdomain["host"]
            else:
                host = f'{subdomain["subdomain"]}.badssl.com'
            port = subdomain.get("port", 443)
            exc = None
            start_time = time.monotonic()
            try:
                socket = connection_manager.get_socket(
                    host, port, "https:", is_ssl=True, ssl_context=ssl_context
                )
                connection_manager.close_socket(socket)
            except RuntimeError as e:
                exc = e
            duration = time.monotonic() - start_time

            if fail == "yes" and exc and "Failed SSL handshake" in str(exc):
                result = "passed"
            elif success == "yes" and exc is None:
                result = "passed"
            else:
                result = f"error - success:{success}, fail:{fail}, exc:{exc}"

            print(f"   - {host}:{port} took {duration:.2f} seconds | {result}")


check_group(adafruit_groups, "Adafruit")
check_group(badssl_groups, "BadSSL")
