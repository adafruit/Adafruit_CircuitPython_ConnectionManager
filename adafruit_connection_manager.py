# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2023 Justin Myers for Adafruit Industries
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

if not sys.implementation.name == "circuitpython":
    from ssl import SSLContext
    from types import ModuleType
    from typing import Any, Optional, Tuple, Union

    try:
        from typing import Protocol
    except ImportError:
        from typing_extensions import Protocol

    # Based on https://github.com/python/typeshed/blob/master/stdlib/_socket.pyi
    class CommonSocketType(Protocol):
        """Describes the common structure every socket type must have."""

        def send(self, data: bytes, flags: int = ...) -> None:
            """Send data to the socket. The meaning of the optional flags kwarg is
            implementation-specific."""

        def settimeout(self, value: Optional[float]) -> None:
            """Set a timeout on blocking socket operations."""

        def close(self) -> None:
            """Close the socket."""

    class CommonCircuitPythonSocketType(CommonSocketType, Protocol):
        """Describes the common structure every CircuitPython socket type must have."""

        def connect(
            self,
            address: Tuple[str, int],
            conntype: Optional[int] = ...,
        ) -> None:
            """Connect to a remote socket at the provided (host, port) address. The conntype
            kwarg optionally may indicate SSL or not, depending on the underlying interface.
            """

    class SupportsRecvWithFlags(Protocol):
        """Describes a type that posseses a socket recv() method supporting the flags kwarg."""

        def recv(self, bufsize: int = ..., flags: int = ...) -> bytes:
            """Receive data from the socket. The return value is a bytes object representing
            the data received. The maximum amount of data to be received at once is specified
            by bufsize. The meaning of the optional flags kwarg is implementation-specific.
            """

    class SupportsRecvInto(Protocol):
        """Describes a type that possesses a socket recv_into() method."""

        def recv_into(
            self, buffer: bytearray, nbytes: int = ..., flags: int = ...
        ) -> int:
            """Receive up to nbytes bytes from the socket, storing the data into the provided
            buffer. If nbytes is not specified (or 0), receive up to the size available in the
            given buffer. The meaning of the optional flags kwarg is implementation-specific.
            Returns the number of bytes received."""

    class CircuitPythonSocketType(
        CommonCircuitPythonSocketType,
        SupportsRecvInto,
        SupportsRecvWithFlags,
        Protocol,
    ):
        """Describes the structure every modern CircuitPython socket type must have."""

    class StandardPythonSocketType(
        CommonSocketType, SupportsRecvInto, SupportsRecvWithFlags, Protocol
    ):
        """Describes the structure every standard Python socket type must have."""

        def connect(self, address: Union[Tuple[Any, ...], str, bytes]) -> None:
            """Connect to a remote socket at the provided address."""

    SocketType = Union[
        CircuitPythonSocketType,
        StandardPythonSocketType,
    ]

    SocketpoolModuleType = ModuleType

    class InterfaceType(Protocol):
        """Describes the structure every interface type must have."""

        @property
        def TLS_MODE(self) -> int:  # pylint: disable=invalid-name
            """Constant representing that a socket's connection mode is TLS."""

    SSLContextType = Union[SSLContext, "_FakeSSLContext"]


class SocketGetOSError(OSError):
    """ConnectionManager Exception class."""


class SocketGetRuntimeError(RuntimeError):
    """ConnectionManager Exception class."""


class SocketConnectMemoryError(OSError):
    """ConnectionManager Exception class."""


class SocketConnectOSError(OSError):
    """ConnectionManager Exception class."""


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
        """connect wrapper to add non-standard mode parameter"""
        try:
            return self._socket.connect(address, self._mode)
        except RuntimeError as error:
            raise OSError(errno.ENOMEM) from error


class _FakeSSLContext:
    def __init__(self, iface: InterfaceType) -> None:
        self._iface = iface

    def wrap_socket(
        self, socket: CircuitPythonSocketType, server_hostname: Optional[str] = None
    ) -> _FakeSSLSocket:
        """Return the same socket"""
        # pylint: disable=unused-argument
        return _FakeSSLSocket(socket, self._iface.TLS_MODE)


def create_fake_ssl_context(
    socket_pool: SocketpoolModuleType, iface: Optional[InterfaceType] = None
) -> _FakeSSLContext:
    """Legacy API for creating a fake SSL context"""
    if not iface:
        # pylint: disable=protected-access
        iface = socket_pool._the_interface
    socket_pool.set_interface(iface)
    return _FakeSSLContext(iface)


class ConnectionManager:
    """Connection manager for sharing sockets."""

    def __init__(
        self,
        socket_pool: SocketpoolModuleType,
    ) -> None:
        self._socket_pool = socket_pool
        # Hang onto open sockets so that we can reuse them.
        self._open_sockets = {}
        self._socket_free = {}

    def _free_sockets(self) -> None:
        free_sockets = []
        for socket, val in self._socket_free.items():
            if val:
                free_sockets.append(socket)

        for socket in free_sockets:
            self.close_socket(socket)

    def free_socket(self, socket: SocketType) -> None:
        """Mark a socket as free so it can be reused if needed"""
        if socket not in self._open_sockets.values():
            raise RuntimeError("Socket not from session")
        self._socket_free[socket] = True

    def close_socket(self, socket: SocketType) -> None:
        """Close a socket"""
        socket.close()
        del self._socket_free[socket]
        key = None
        for k, value in self._open_sockets.items():
            if value == socket:
                key = k
                break
        if key:
            del self._open_sockets[key]

    # pylint: disable=too-many-locals,too-many-statements
    def get_socket(
        self,
        host: str,
        port: int,
        proto: str,
        *,
        timeout: float = 1,
        is_ssl: bool = False,
        ssl_context: Optional[SSLContextType] = None,
        max_retries: int = 5,
        exception_passthrough: bool = False,
    ) -> CircuitPythonSocketType:
        """Get socket and connect"""
        # pylint: disable=too-many-branches
        key = (host, port, proto)
        if key in self._open_sockets:
            socket = self._open_sockets[key]
            if self._socket_free[socket]:
                self._socket_free[socket] = False
                return socket

        if proto == "https:":
            is_ssl = True
        if is_ssl and not ssl_context:
            raise RuntimeError(
                "ssl_context must be set before using adafruit_requests for https"
            )

        addr_info = self._socket_pool.getaddrinfo(
            host, port, 0, self._socket_pool.SOCK_STREAM
        )[0]

        retry_count = 0
        socket = None
        last_exc = None
        last_exc_new_type = None
        while retry_count < max_retries and socket is None:
            if retry_count > 0:
                if any(self._socket_free.items()):
                    self._free_sockets()
                else:
                    raise RuntimeError("Sending request failed") from last_exc
            retry_count += 1

            try:
                socket = self._socket_pool.socket(addr_info[0], addr_info[1])
            except OSError as exc:
                last_exc_new_type = SocketGetOSError
                last_exc = exc
                continue
            except RuntimeError as exc:
                last_exc_new_type = SocketGetRuntimeError
                last_exc = exc
                continue

            connect_host = addr_info[-1][0]
            if is_ssl:
                socket = ssl_context.wrap_socket(socket, server_hostname=host)
                connect_host = host
            socket.settimeout(timeout)  # socket read timeout

            try:
                socket.connect((connect_host, port))
            except MemoryError as exc:
                last_exc_new_type = SocketConnectMemoryError
                last_exc = exc
                socket.close()
                socket = None
            except OSError as exc:
                last_exc_new_type = SocketConnectOSError
                last_exc = exc
                socket.close()
                socket = None

        if socket is None:
            if exception_passthrough:
                raise last_exc_new_type("Repeated socket failures") from last_exc
            raise RuntimeError("Repeated socket failures") from last_exc

        self._open_sockets[key] = socket
        self._socket_free[socket] = False
        return socket


_global_connection_manager = None  # pylint: disable=invalid-name


def get_connection_manager(socket_pool: SocketpoolModuleType) -> None:
    """Get the ConnectionManager singleton"""
    global _global_connection_manager  # pylint: disable=global-statement
    if _global_connection_manager is None:
        _global_connection_manager = ConnectionManager(socket_pool)
    return _global_connection_manager
