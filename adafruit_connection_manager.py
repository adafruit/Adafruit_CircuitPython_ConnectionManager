# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_connection_manager`
================================================================================

A urllib3.poolmanager/urllib3.connectionpool-like library for managing sockets and connections


* Author(s): Justin Myers

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

"""

# imports

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ConnectionManager.git"

import errno
import sys

WIZNET5K_SSL_SUPPORT_VERSION = (9, 1)

# typing


if not sys.implementation.name == "circuitpython":
    from typing import List, Optional, Tuple

    from circuitpython_typing.socket import (
        CircuitPythonSocketType,
        InterfaceType,
        SocketpoolModuleType,
        SocketType,
        SSLContextType,
    )


# ssl and pool helpers


class _FakeSSLSocket:
    def __init__(self, socket: CircuitPythonSocketType, tls_mode: int) -> None:
        self._socket = socket
        self._mode = tls_mode
        self.settimeout = socket.settimeout
        self.send = socket.send
        self.recv = socket.recv
        self.close = socket.close
        self.recv_into = socket.recv_into

    def connect(self, address: Tuple[str, int]) -> None:
        """Connect wrapper to add non-standard mode parameter"""
        try:
            return self._socket.connect(address, self._mode)
        except RuntimeError as error:
            raise OSError(errno.ENOMEM, str(error)) from error


class _FakeSSLContext:
    def __init__(self, iface: InterfaceType) -> None:
        self._iface = iface

    def wrap_socket(  # pylint: disable=unused-argument
        self, socket: CircuitPythonSocketType, server_hostname: Optional[str] = None
    ) -> _FakeSSLSocket:
        """Return the same socket"""
        if hasattr(self._iface, "TLS_MODE"):
            return _FakeSSLSocket(socket, self._iface.TLS_MODE)

        raise AttributeError("This radio does not support TLS/HTTPS")


def create_fake_ssl_context(
    socket_pool: SocketpoolModuleType, iface: InterfaceType
) -> _FakeSSLContext:
    """Method to return a fake SSL context for when ssl isn't available to import

    For example when using a:

     * `Adafruit Ethernet FeatherWing <https://www.adafruit.com/product/3201>`_
     * `Adafruit AirLift – ESP32 WiFi Co-Processor Breakout Board
       <https://www.adafruit.com/product/4201>`_
     * `Adafruit AirLift FeatherWing – ESP32 WiFi Co-Processor
       <https://www.adafruit.com/product/4264>`_
    """
    socket_pool.set_interface(iface)
    return _FakeSSLContext(iface)


_global_connection_managers = {}
_global_key_by_socketpool = {}
_global_socketpools = {}
_global_ssl_contexts = {}


def get_radio_socketpool(radio):
    """Helper to get a socket pool for common boards.

    Currently supported:

     * Boards with onboard WiFi (ESP32S2, ESP32S3, Pico W, etc)
     * Using the ESP32 WiFi Co-Processor (like the Adafruit AirLift)
     * Using a WIZ5500 (Like the Adafruit Ethernet FeatherWing)
    """
    class_name = radio.__class__.__name__
    if class_name not in _global_socketpools:
        if class_name == "Radio":
            import ssl  # pylint: disable=import-outside-toplevel

            import socketpool  # pylint: disable=import-outside-toplevel

            pool = socketpool.SocketPool(radio)
            ssl_context = ssl.create_default_context()

        elif class_name == "ESP_SPIcontrol":
            import adafruit_esp32spi.adafruit_esp32spi_socket as pool  # pylint: disable=import-outside-toplevel

            ssl_context = create_fake_ssl_context(pool, radio)

        elif class_name == "WIZNET5K":
            import adafruit_wiznet5k.adafruit_wiznet5k_socket as pool  # pylint: disable=import-outside-toplevel

            # Note: At this time, SSL/TLS connections are not supported by older
            # versions of the Wiznet5k library or on boards withouut the ssl module
            # see https://docs.circuitpython.org/en/latest/shared-bindings/support_matrix.html
            ssl_context = None
            cp_version = sys.implementation[1]
            if pool.SOCK_STREAM == 1 and cp_version >= WIZNET5K_SSL_SUPPORT_VERSION:
                try:
                    import ssl  # pylint: disable=import-outside-toplevel

                    ssl_context = ssl.create_default_context()
                    pool.set_interface(radio)
                except ImportError:
                    # if SSL not on board, default to fake_ssl_context
                    pass

            if ssl_context is None:
                ssl_context = create_fake_ssl_context(pool, radio)

        else:
            raise AttributeError(f"Unsupported radio class: {class_name}")

        _global_key_by_socketpool[pool] = class_name
        _global_socketpools[class_name] = pool
        _global_ssl_contexts[class_name] = ssl_context

    return _global_socketpools[class_name]


def get_radio_ssl_context(radio):
    """Helper to get ssl_contexts for common boards.

    Currently supported:

     * Boards with onboard WiFi (ESP32S2, ESP32S3, Pico W, etc)
     * Using the ESP32 WiFi Co-Processor (like the Adafruit AirLift)
     * Using a WIZ5500 (Like the Adafruit Ethernet FeatherWing)
    """
    class_name = radio.__class__.__name__
    get_radio_socketpool(radio)
    return _global_ssl_contexts[class_name]


# main class


class ConnectionManager:
    """A library for managing sockets accross libraries."""

    def __init__(
        self,
        socket_pool: SocketpoolModuleType,
    ) -> None:
        self._socket_pool = socket_pool
        # Hang onto open sockets so that we can reuse them.
        self._available_sockets = set()
        self._key_by_managed_socket = {}
        self._managed_socket_by_key = {}

    def _free_sockets(self, force: bool = False) -> None:
        # cloning lists since items are being removed
        available_sockets = list(self._available_sockets)
        for socket in available_sockets:
            self.close_socket(socket)
        if force:
            open_sockets = list(self._managed_socket_by_key.values())
            for socket in open_sockets:
                self.close_socket(socket)

    def _get_connected_socket(  # pylint: disable=too-many-arguments
        self,
        addr_info: List[Tuple[int, int, int, str, Tuple[str, int]]],
        host: str,
        port: int,
        timeout: float,
        is_ssl: bool,
        ssl_context: Optional[SSLContextType] = None,
    ):
        try:
            socket = self._socket_pool.socket(addr_info[0], addr_info[1])
        except (OSError, RuntimeError) as exc:
            return exc

        if is_ssl:
            socket = ssl_context.wrap_socket(socket, server_hostname=host)
            connect_host = host
        else:
            connect_host = addr_info[-1][0]
        socket.settimeout(timeout)  # socket read timeout

        try:
            socket.connect((connect_host, port))
        except (MemoryError, OSError) as exc:
            socket.close()
            return exc

        return socket

    @property
    def available_socket_count(self) -> int:
        """Get the count of available (freed) managed sockets."""
        return len(self._available_sockets)

    @property
    def managed_socket_count(self) -> int:
        """Get the count of managed sockets."""
        return len(self._managed_socket_by_key)

    def close_socket(self, socket: SocketType) -> None:
        """
        Close a previously managed and connected socket.

        - **socket_pool** *(SocketType)* – The socket you want to close
        """
        if socket not in self._managed_socket_by_key.values():
            raise RuntimeError("Socket not managed")
        socket.close()
        key = self._key_by_managed_socket.pop(socket)
        del self._managed_socket_by_key[key]
        if socket in self._available_sockets:
            self._available_sockets.remove(socket)

    def free_socket(self, socket: SocketType) -> None:
        """Mark a managed socket as available so it can be reused."""
        if socket not in self._managed_socket_by_key.values():
            raise RuntimeError("Socket not managed")
        self._available_sockets.add(socket)

    def get_socket(
        self,
        host: str,
        port: int,
        proto: str,
        session_id: Optional[str] = None,
        *,
        timeout: float = 1,
        is_ssl: bool = False,
        ssl_context: Optional[SSLContextType] = None,
    ) -> CircuitPythonSocketType:
        """
        Get a new socket and connect.

        - **host** *(str)* – The host you are want to connect to: "www.adaftuit.com"
        - **port** *(int)* – The port you want to connect to: 80
        - **proto** *(str)* – The protocal you want to use: "http:"
        - **session_id** *(Optional[str])* – A unique Session ID, when wanting to have multiple open
          connections to the same host
        - **timeout** *(float)* – Time timeout used for connecting
        - **is_ssl** *(bool)* – If the connection is to be over SSL (auto set when proto is
          "https:")
        - **ssl_context** *(Optional[SSLContextType])* – The SSL context to use when making SSL
          requests
        """
        if session_id:
            session_id = str(session_id)
        key = (host, port, proto, session_id)
        if key in self._managed_socket_by_key:
            socket = self._managed_socket_by_key[key]
            if socket in self._available_sockets:
                self._available_sockets.remove(socket)
                return socket

            raise RuntimeError(f"Socket already connected to {proto}//{host}:{port}")

        if proto == "https:":
            is_ssl = True
        if is_ssl and not ssl_context:
            raise AttributeError(
                "ssl_context must be set before using adafruit_requests for https"
            )

        addr_info = self._socket_pool.getaddrinfo(
            host, port, 0, self._socket_pool.SOCK_STREAM
        )[0]

        first_exception = None
        result = self._get_connected_socket(
            addr_info, host, port, timeout, is_ssl, ssl_context
        )
        if isinstance(result, Exception):
            # Got an error, if there are any available sockets, free them and try again
            if self.available_socket_count:
                first_exception = result
                self._free_sockets()
                result = self._get_connected_socket(
                    addr_info, host, port, timeout, is_ssl, ssl_context
                )
        if isinstance(result, Exception):
            last_result = f", first error: {first_exception}" if first_exception else ""
            raise RuntimeError(
                f"Error connecting socket: {result}{last_result}"
            ) from result

        self._key_by_managed_socket[result] = key
        self._managed_socket_by_key[key] = result
        return result


# global helpers


def connection_manager_close_all(
    socket_pool: Optional[SocketpoolModuleType] = None, release_references: bool = False
) -> None:
    """
    Close all open sockets for pool, optionally release references.

    - **socket_pool** *(Optional[SocketpoolModuleType])* – A specifc SocketPool you want to close
      sockets for, leave blank for all SocketPools
    - **release_references** *(bool)* – Set to True if you want to also clear stored references to
      the SocketPool and SSL contexts
    """
    if socket_pool:
        socket_pools = [socket_pool]
    else:
        socket_pools = _global_connection_managers.keys()

    for pool in socket_pools:
        connection_manager = _global_connection_managers.get(pool, None)
        if connection_manager is None:
            raise RuntimeError("SocketPool not managed")

        connection_manager._free_sockets(force=True)  # pylint: disable=protected-access

        if not release_references:
            continue

        key = _global_key_by_socketpool.pop(pool)
        if key:
            _global_socketpools.pop(key, None)
            _global_ssl_contexts.pop(key, None)

        _global_connection_managers.pop(pool, None)


def get_connection_manager(socket_pool: SocketpoolModuleType) -> ConnectionManager:
    """
    Get the ConnectionManager singleton for the given pool.

    - **socket_pool** *(Optional[SocketpoolModuleType])* – The SocketPool you want the
      ConnectionManager for
    """
    if socket_pool not in _global_connection_managers:
        _global_connection_managers[socket_pool] = ConnectionManager(socket_pool)
    return _global_connection_managers[socket_pool]
