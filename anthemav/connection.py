"""Module containing the connection wrapper for the AVR interface."""
import asyncio
import contextlib
import enum
import logging
import socket
from collections.abc import Awaitable
from typing import Callable
from .protocol import AVR

UpdateCallback = Callable[[str], None]
ConnectionLostCallback = Callable[[], Awaitable[None]]

__all__ = [
    "Connection",
    "ConnectionState",
    "UpdateCallback",
    "ConnectionLostCallback",
]


class ConnectionState(enum.Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CLOSED = "closed"


class Connection:
    """Connection handler to maintain network connection for AVR Protocol."""

    def __init__(self) -> None:
        """Instantiate the Connection object."""
        self.log = logging.getLogger(__name__)
        self.host = ""
        self.port = 0
        self._retry_interval = 1.0
        self._initial_retry_interval = 1.0
        self._retry_count = 0
        self._closed = False
        self._closing = False
        self._halted = False
        self._auto_reconnect = False
        self.protocol = None
        self._state = ConnectionState.DISCONNECTED
        self._connection_timeout = 10.0
        self._command_timeout = 5.0
        self._reconnect_task = None

    @classmethod
    async def create(
        cls,
        host: str = "localhost",
        port: int = 14999,
        auto_reconnect: bool = True,
        protocol_class: type[asyncio.Protocol] = AVR,
        update_callback: UpdateCallback | None = None,
        connection_timeout: float = 10.0,
        command_timeout: float = 5.0,
    ) -> "Connection":
        """Initiate a connection to a specific device.

        :param host: Hostname or IP address of the device
        :param port: TCP port number of the device
        :param auto_reconnect: Should the Connection try to automatically reconnect?
        :param protocol_class: Protocol class to use (default: AVR)
        :param update_callback: Called whenever AVR state data changes
        :param connection_timeout: Timeout in seconds for connection attempts
        :param command_timeout: Timeout in seconds for command responses

        :raises ValueError: If timeout values are not positive
        """
        if port < 0:
            raise ValueError(f"Invalid port value: {port}")
        if connection_timeout <= 0:
            raise ValueError("connection_timeout must be positive")
        if command_timeout <= 0:
            raise ValueError("command_timeout must be positive")

        conn = cls()
        conn.host = host
        conn.port = port
        conn._auto_reconnect = auto_reconnect
        conn._connection_timeout = connection_timeout
        conn._command_timeout = command_timeout

        async def connection_lost() -> None:
            """Callback for protocol when connection is lost."""
            if conn._auto_reconnect and not conn._closing:
                conn._reconnect_task = asyncio.create_task(conn.reconnect())

        conn.protocol = protocol_class(
            connection_lost_callback=connection_lost,
            update_callback=update_callback,
        )

        if auto_reconnect:
            await conn.reconnect()

        return conn

    @property
    def transport(self):
        """Return the transport object."""
        return self.protocol.transport if self.protocol else None

    @property
    def state(self) -> ConnectionState:
        """Return the current connection state."""
        return self._state

    def _get_running_loop(self) -> asyncio.AbstractEventLoop:
        """Get the running event loop."""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            self.log.error("No running event loop found")
            raise

    async def _create_connection_with_timeout(self) -> None:
        """Create connection with timeout."""
        try:
            loop = self._get_running_loop()
            await asyncio.wait_for(
                loop.create_connection(
                    lambda: self.protocol,
                    self.host,
                    self.port
                ),
                timeout=self._connection_timeout
            )
            self.log.debug(
                "Connection established to %s:%d within %.1fs",
                self.host,
                self.port,
                self._connection_timeout
            )
        except asyncio.TimeoutError:
            self.log.error(
                "Connection timeout after %.1fs connecting to %s:%d",
                self._connection_timeout,
                self.host,
                self.port
            )
            raise
        except OSError as e:
            self.log.error(
                "Connection failed to %s:%d: %s",
                self.host,
                self.port,
                e
            )
            raise

    def _configure_transport(self, transport: asyncio.Transport) -> None:
        """Configure transport with TCP keepalive."""
        sock = transport.get_extra_info('socket')
        if sock is not None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            if hasattr(socket, 'TCP_KEEPIDLE'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            if hasattr(socket, 'TCP_KEEPINTVL'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, 'TCP_KEEPCNT'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

            self.log.debug("TCP keepalive enabled for %s:%d", self.host, self.port)

    def _cancel_reconnect_task(self) -> None:
        """Cancel any pending reconnect task."""
        if self._reconnect_task and not self._reconnect_task.done():
            self.log.debug("Cancelling reconnect task")
            self._reconnect_task.cancel()
            self._reconnect_task = None

    def _calculate_retry_interval(self, attempt: int) -> float:
        """Calculate retry interval with exponential backoff.
        
        :param attempt: Number of consecutive failures
        :return: Retry interval in seconds (capped at 60)
        """
        return min(60, (1.5 ** attempt) * self._initial_retry_interval)

    def _reset_retry(self) -> None:
        """Reset retry state on successful connection."""
        self._retry_interval = self._initial_retry_interval
        self._retry_count = 0

    def _increase_retry(self) -> None:
        """Increase retry interval using exponential backoff."""
        self._retry_count += 1
        self._retry_interval = self._calculate_retry_interval(self._retry_count)

    async def reconnect(self) -> None:
        """Connect to the host and keep the connection open."""
        while True:
            try:
                if self._halted:
                    await asyncio.sleep(2)
                else:
                    self._state = ConnectionState.CONNECTING
                    self.log.debug(
                        "Connecting to Anthem AVR at %s:%d", self.host, self.port
                    )
                    await self._create_connection_with_timeout()
                    self._configure_transport(self.protocol.transport)
                    self._state = ConnectionState.CONNECTED
                    self._reset_retry()
                    return

            except (OSError, asyncio.TimeoutError):
                self._state = ConnectionState.DISCONNECTED
                self._increase_retry()
                interval = self._retry_interval
                self.log.warning("Connecting failed, retrying in %i seconds", int(interval))

                if not self._auto_reconnect or self._closing:
                    self.log.debug("Auto-reconnect disabled or closing, stopping retry attempts")
                    raise

                await asyncio.sleep(interval)

    def close(self) -> None:
        """Close the connection without reconnecting."""
        self.log.debug("Closing connection to AVR")
        self._closing = True
        self._state = ConnectionState.CLOSED
        self._cancel_reconnect_task()
        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def halt(self) -> None:
        """Halt the connection until resume() is called."""
        self.log.warning("Halting connection to AVR")
        self._halted = True
        self._state = ConnectionState.DISCONNECTED
        self._cancel_reconnect_task()
        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def resume(self) -> None:
        """Resume the connection after halt."""
        self.log.warning("Resuming connection to AVR")
        self._halted = False

    async def __aenter__(self) -> "Connection":
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and cleanup resources."""
        reconnect_task = self._reconnect_task
        self.close()
        if reconnect_task:
            with contextlib.suppress(asyncio.CancelledError):
                await reconnect_task

    @property
    def dump_conndata(self) -> str:
        """Debug dump of connection attributes."""
        return ", ".join(f"{k}: {v}" for k, v in vars(self).items())
