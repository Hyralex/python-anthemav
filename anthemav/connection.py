"""Module containing the connection wrapper for the AVR interface."""
import asyncio
import enum
import logging
import socket
import time
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import Callable
from .protocol import AVR

# Type aliases for callbacks
UpdateCallback = Callable[[str], None]
ConnectionLostCallback = Callable[[], Awaitable[None]]

__all__ = [
    "Connection",
    "ConnectionState",
    "ConnectionInfo",
    "ConnectionConfig",
    "UpdateCallback",
    "ConnectionLostCallback",
]


class ConnectionState(enum.Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CLOSED = "closed"


@dataclass
class ConnectionInfo:
    """Connection information and statistics."""
    state: ConnectionState
    host: str
    port: int
    connected_at: float | None
    last_received_at: float | None
    reconnect_attempts: int
    current_retry_interval: float

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self.state == ConnectionState.CONNECTED

    @property
    def time_since_last_data(self) -> float | None:
        """Time since last data received."""
        if self.last_received_at is None:
            return None
        return time.time() - self.last_received_at


@dataclass
class ConnectionConfig:
    """Connection configuration."""
    host: str = "localhost"
    port: int = 14999
    auto_reconnect: bool = True
    connection_timeout: float = 10.0
    command_timeout: float = 5.0
    keepalive_interval: int = 30
    keepalive_count: int = 3
    buffer_max_size: int = 8192

    def __post_init__(self):
        """Validate configuration."""
        if self.connection_timeout <= 0:
            raise ValueError("connection_timeout must be positive")
        if self.command_timeout <= 0:
            raise ValueError("command_timeout must be positive")
        if self.port < 1 or self.port > 65535:
            raise ValueError("port must be between 1 and 65535")


class Connection:
    """Connection handler to maintain network connection for AVR Protocol."""

    def __init__(self) -> None:
        """Instantiate the Connection object."""
        self.log: logging.Logger = logging.getLogger(__name__)
        self.host: str = ""
        self.port: int = 0
        self._retry_interval: float = 1
        self._initial_retry_interval: float = 1
        self._retry_count: int = 0
        self._closed: bool = False
        self._closing: bool = False
        self._halted: bool = False
        self._auto_reconnect: bool = False
        self.protocol: asyncio.Protocol = None
        self._state: ConnectionState = ConnectionState.DISCONNECTED
        self._connection_timeout: float = 10.0
        self._command_timeout: float = 5.0
        self._reconnect_task: asyncio.Task | None = None

    @classmethod
    async def create(
        cls,
        host: str = "localhost",
        port: int = 14999,
        auto_reconnect: bool = True,
        loop: asyncio.AbstractEventLoop | None = None,
        protocol_class: type[asyncio.Protocol] = AVR,
        update_callback: UpdateCallback | None = None,
        connection_timeout: float = 10.0,
        command_timeout: float = 5.0,
    ) -> "Connection":
        """Initiate a connection to a specific device.

        Here is where we supply the host and port and callback callables we
        expect for this AVR class object.

        :param host:
            Hostname or IP address of the device
        :param port:
            TCP port number of the device
        :param auto_reconnect:
            Should the Connection try to automatically reconnect if needed?
        :param loop:
            asyncio.loop for async operation
        :param update_callback"
            This function is called whenever AVR state data changes
        :param connection_timeout:
            Timeout in seconds for connection attempts (default: 10.0)
        :param command_timeout:
            Timeout in seconds for command responses (default: 5.0)

        :type host:
            str
        :type port:
            int
        :type auto_reconnect:
            boolean
        :type loop:
            asyncio.loop
        :type update_callback:
            callable
        :type connection_timeout:
            float
        :type command_timeout:
            float
        """
        assert port >= 0, f"Invalid port value: {port}"

        # Validate timeout values
        if connection_timeout <= 0:
            raise ValueError("connection_timeout must be positive")
        if command_timeout <= 0:
            raise ValueError("command_timeout must be positive")

        conn = cls()

        # Add deprecation warning for loop parameter
        if loop is not None:
            import warnings
            warnings.warn(
                "The 'loop' parameter is deprecated and will be ignored. "
                "The connection will use asyncio.get_running_loop() instead.",
                DeprecationWarning,
                stacklevel=2
            )

        conn.host = host
        conn.port = port
        conn._retry_interval = 1
        conn._initial_retry_interval = 1
        conn._retry_count = 0
        conn._closed = False
        conn._closing = False
        conn._halted = False
        conn._auto_reconnect = auto_reconnect
        conn._connection_timeout = connection_timeout
        conn._command_timeout = command_timeout
        conn._reconnect_task = None

        async def connection_lost() -> None:
            """Function callback for Protocoal class when connection is lost."""
            if conn._auto_reconnect and not conn._closing:
                conn._reconnect_task = asyncio.create_task(conn.reconnect())

        conn.protocol = protocol_class(
            connection_lost_callback=connection_lost,
            loop=loop,  # Pass through for backward compatibility
            update_callback=update_callback,
        )

        if auto_reconnect:
            await conn.reconnect()

        return conn

    @property
    def transport(self) -> asyncio.Transport | None:
        """Return pointer to the transport object.

        Use this property to obtain passthrough access to the underlying
        Protocol properties and methods.
        """
        return self.protocol.transport

    @property
    def state(self) -> ConnectionState:
        """Return the current connection state.

        :return: Current connection state
        :rtype: ConnectionState
        """
        return self._state

    def _get_running_loop(self) -> asyncio.AbstractEventLoop:
        """Get the running event loop safely.

        Returns the currently running event loop. If no loop is running,
        this will raise a RuntimeError.

        :return: The running event loop
        :rtype: asyncio.AbstractEventLoop
        :raises RuntimeError: If no event loop is running
        """
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            self.log.error("No running event loop found")
            raise

    async def _create_connection_with_timeout(self) -> None:
        """Create connection with timeout.

        Wraps the asyncio create_connection call with a timeout to prevent
        hanging on non-responsive hosts. Handles timeout and connection errors
        with full context logging.

        :raises asyncio.TimeoutError: If connection times out
        :raises OSError: If connection fails
        """
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
        """Configure transport with TCP keepalive.

        Enables TCP keepalive on the socket to detect dead connections.
        Sets platform-specific keepalive options when available.

        :param transport: The asyncio transport to configure
        :type transport: asyncio.Transport
        """
        sock = transport.get_extra_info('socket')
        if sock is not None:
            # Enable TCP keepalive
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            # Platform-specific keepalive configuration
            if hasattr(socket, 'TCP_KEEPIDLE'):
                # Linux/Unix: time before sending keepalive probes
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            if hasattr(socket, 'TCP_KEEPINTVL'):
                # Linux/Unix: interval between keepalive probes
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            if hasattr(socket, 'TCP_KEEPCNT'):
                # Linux/Unix: number of keepalive probes
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

            self.log.debug("TCP keepalive enabled for %s:%d", self.host, self.port)

    def _cancel_reconnect_task(self) -> None:
        """Cancel any pending reconnect task.

        Cancels the reconnect task if it exists and is not already done.
        This is called when closing or halting the connection to ensure
        no reconnection attempts continue.
        """
        if self._reconnect_task and not self._reconnect_task.done():
            self.log.debug("Cancelling reconnect task")
            self._reconnect_task.cancel()
            self._reconnect_task = None

    def _get_retry_interval(self) -> float:
        """Get the current retry interval.

        :return: Current retry interval in seconds
        :rtype: float
        """
        return self._retry_interval

    def _reset_retry_interval(self) -> None:
        """Reset retry interval to initial value on successful connection.

        Resets both the retry interval and the retry count to their initial
        values. This is called when a connection succeeds after retries.
        """
        self._retry_interval = self._initial_retry_interval
        self._retry_count = 0

    def _increase_retry_interval(self) -> None:
        """Increase retry interval using exponential backoff.

        Implements exponential backoff with the formula:
        interval = min(60, 1.5^N * initial_interval)

        where N is the number of consecutive failures. The maximum interval
        is capped at 60 seconds (1 minute).
        """
        self._retry_count += 1
        self._retry_interval = min(60, (1.5 ** self._retry_count) * self._initial_retry_interval)

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
                    self._reset_retry_interval()
                    return

            except (OSError, asyncio.TimeoutError):
                self._state = ConnectionState.DISCONNECTED
                self._increase_retry_interval()
                interval = self._get_retry_interval()
                self.log.warning("Connecting failed, retrying in %i seconds", interval)

                # Check auto_reconnect before retrying
                if not self._auto_reconnect or self._closing:
                    self.log.debug("Auto-reconnect disabled or closing, stopping retry attempts")
                    raise

                await asyncio.sleep(interval)

    def close(self) -> None:
        """Close the AVR device connection and don't try to reconnect."""
        self.log.debug("Closing connection to AVR")
        self._closing = True
        self._state = ConnectionState.CLOSED
        self._cancel_reconnect_task()
        if self.protocol.transport:
            self.protocol.transport.close()

    def halt(self) -> None:
        """Close the AVR device connection and wait for a resume() request."""
        self.log.warning("Halting connection to AVR")
        self._halted = True
        self._state = ConnectionState.DISCONNECTED
        self._cancel_reconnect_task()
        if self.protocol.transport:
            self.protocol.transport.close()

    def resume(self) -> None:
        """Resume the AVR device connection if we have been halted."""
        self.log.warning("Resuming connection to AVR")
        self._halted = False

    async def __aenter__(self) -> "Connection":
        """Enter async context manager.

        Returns the connection instance for use in async with statements.

        :return: The connection instance
        :rtype: Connection
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and cleanup resources.

        Ensures the connection is properly closed when exiting the context,
        whether normally or via exception. Cancels any pending reconnect tasks
        and waits for them to complete.

        :param exc_type: Exception type if an exception occurred
        :param exc_val: Exception value if an exception occurred
        :param exc_tb: Exception traceback if an exception occurred
        :return: None (does not suppress exceptions)
        :rtype: None
        """
        # Save task reference before close() sets it to None
        reconnect_task = self._reconnect_task
        self.close()
        # Wait for reconnect task to be cancelled if it exists
        if reconnect_task and not reconnect_task.done():
            try:
                await reconnect_task
            except asyncio.CancelledError:
                # Expected when we cancel the task
                pass
        return None

    @property
    def dump_conndata(self) -> str:
        """Developer tool for debugging forensics."""
        attrs = vars(self)
        return ", ".join("%s: %s" % item for item in attrs.items())
