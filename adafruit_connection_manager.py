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
    from typing import Optional, Tuple

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
            raise OSError(errno.ENOMEM) from error


class _FakeSSLContext:
    def __init__(self, iface: InterfaceType) -> None:
        self._iface = iface

    # pylint: disable=unused-argument
    def wrap_socket(
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
_global_socketpools = {}
_global_ssl_contexts = {}


def get_radio_socketpool(radio):
    """Helper to get a socket pool for common boards

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

        _global_socketpools[class_name] = pool
        _global_ssl_contexts[class_name] = ssl_context

    return _global_socketpools[class_name]


def get_radio_ssl_context(radio):
    """Helper to get ssl_contexts for common boards

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
    """Connection manager for sharing open sockets (aka connections)."""

    def __init__(
        self,
        socket_pool: SocketpoolModuleType,
    ) -> None:
        self._socket_pool = socket_pool
        # Hang onto open sockets so that we can reuse them.
        self._available_socket = {}
        self._open_sockets = {}

    def _free_sockets(self, force: bool = False) -> None:
        available_sockets = []
        for socket, free in self._available_socket.items():
            if free or force:
                available_sockets.append(socket)

        for socket in available_sockets:
            self.close_socket(socket)

    def _get_key_for_socket(self, socket):
        try:
            return next(
                key for key, value in self._open_sockets.items() if value == socket
            )
        except StopIteration:
            return None

    @property
    def open_sockets(self) -> int:
        """Get the count of open sockets"""
        return len(self._open_sockets)

    @property
    def freeable_open_sockets(self) -> int:
        """Get the count of freeable open sockets"""
        return len(
            [socket for socket, free in self._available_socket.items() if free is True]
        )

    def close_socket(self, socket: SocketType) -> None:
        """Close a previously opened socket."""
        if socket not in self._open_sockets.values():
            raise RuntimeError("Socket not managed")
        key = self._get_key_for_socket(socket)
        socket.close()
        del self._available_socket[socket]
        del self._open_sockets[key]

    def free_socket(self, socket: SocketType) -> None:
        """Mark a previously opened socket as available so it can be reused if needed."""
        if socket not in self._open_sockets.values():
            raise RuntimeError("Socket not managed")
        self._available_socket[socket] = True

    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
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
        """Get a new socket and connect"""
        if session_id:
            session_id = str(session_id)
        key = (host, port, proto, session_id)
        if key in self._open_sockets:
            socket = self._open_sockets[key]
            if self._available_socket[socket]:
                self._available_socket[socket] = False
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

        try_count = 0
        socket = None
        last_exc = None
        while try_count < 2 and socket is None:
            try_count += 1
            if try_count > 1:
                if any(
                    socket
                    for socket, free in self._available_socket.items()
                    if free is True
                ):
                    self._free_sockets()
                else:
                    break

            try:
                socket = self._socket_pool.socket(addr_info[0], addr_info[1])
            except OSError as exc:
                last_exc = exc
                continue
            except RuntimeError as exc:
                last_exc = exc
                continue

            if is_ssl:
                socket = ssl_context.wrap_socket(socket, server_hostname=host)
                connect_host = host
            else:
                connect_host = addr_info[-1][0]
            socket.settimeout(timeout)  # socket read timeout

            try:
                socket.connect((connect_host, port))
            except MemoryError as exc:
                last_exc = exc
                socket.close()
                socket = None
            except OSError as exc:
                last_exc = exc
                socket.close()
                socket = None

        if socket is None:
            raise RuntimeError(f"Error connecting socket: {last_exc}") from last_exc

        self._available_socket[socket] = False
        self._open_sockets[key] = socket
        return socket


# global helpers


def connection_manager_close_all(
    socket_pool: Optional[SocketpoolModuleType] = None, release_references: bool = False
) -> None:
    """Close all open sockets for pool"""
    if socket_pool:
        socket_pools = [socket_pool]
    else:
        socket_pools = _global_connection_managers.keys()

    for pool in socket_pools:
        connection_manager = _global_connection_managers.get(pool, None)
        if connection_manager is None:
            raise RuntimeError("SocketPool not managed")

        connection_manager._free_sockets(force=True)  # pylint: disable=protected-access

        if release_references:
            radio_key = None
            for radio_check, pool_check in _global_socketpools.items():
                if pool == pool_check:
                    radio_key = radio_check
                    break

            if radio_key:
                if radio_key in _global_socketpools:
                    del _global_socketpools[radio_key]

                if radio_key in _global_ssl_contexts:
                    del _global_ssl_contexts[radio_key]

            if pool in _global_connection_managers:
                del _global_connection_managers[pool]


def get_connection_manager(socket_pool: SocketpoolModuleType) -> ConnectionManager:
    """Get the ConnectionManager singleton for the given pool"""
    if socket_pool not in _global_connection_managers:
        _global_connection_managers[socket_pool] = ConnectionManager(socket_pool)
    return _global_connection_managers[socket_pool]
