"""
Logging utilities
"""

import asyncio
from datetime import datetime as dt
import os
from typing import Any, Callable, Coroutine, Iterable

from .types import Logger
from .utils import Timeout

async def _run_async_callback(
    callback: Coroutine[Any, Any, None],
    suppress_errors: bool = False
) -> None:
    try:
        await callback
    except Exception as err: #pylint: disable=broad-exception-caught
        if not suppress_errors:
            raise err

class BufferedLogger(Logger):
    """
    Simple Logger that buffers logs until flushed then can call generic callbacks/asynchornous
    callbacks

    Args:
        default_log_level (optional str | None default: None): The default log level to use
        print_local (optional bool default: True): Whether to print logs locally (to stdout)
        buffer_size (optional int | None default: None): The number of logs to buffer before
        automatically flushing
        callbacks (optional Iterable[Callable[[str], None]] default: ()): Callbacks to call when a
        log is being emmited
        async_callbacks (optional Iterable[Callable[[str], Coroutine[Any, Any, None]]] default: ()):
        Asynchronous callbacks to schedule when a log is being emmited (if present an event loop
        must be running otherwise a RuntimeError will be raised)
        suppress_errors (optional bool default: False): If True errors/exceptions raised by
        callbacks will be suppressed. For synchronous callbacks this is required to ensure all
        callbacks are called. For asynchronous callbacks this just suppresses any error logs

    Raises:
        RuntimeError: If an asynchronous callback is provided but no running event loop is found
    """

    def __init__(
        self,
        default_log_level: str | None = None,
        print_local: bool = True,
        buffer_size: int | None = None,
        callbacks: Iterable[Callable[[str], None]] = (),
        async_callbacks: Iterable[Callable[[str], Coroutine[Any, Any, None]]] = (),
        suppress_errors: bool = False
    ) -> None:
        self._log_level: str | None = default_log_level
        self._print_local: bool = print_local
        self._logs: list[str] = []
        self._buffer_size: int | None = buffer_size
        self._callbacks: list[Callable[[str], None]] = [*callbacks]
        self._async_callbacks: list[Callable[[str], Coroutine[Any, Any, None]]] = [*async_callbacks]
        if len(self._async_callbacks) > 0:
            try:
                asyncio.get_running_loop()
            except RuntimeError as err:
                raise RuntimeError(
                    'One or more async callbacks were provided but no running event loop was found'
                ) from err
        self._suppress_errors: bool = suppress_errors


    def log(
        self,
        *msgs: Any,
        sep: str=' ',
        end='\n',
        level: str | None = None,
        flush: bool = False
    ) -> None:
        """
        Log a message

        Args:
            msgs (*str): The message to log
            sep (optional str default: ' '): The separator to use when joining the messages
            end (optional str default: '\n'): String to append to the end of the message
            level (optional str | None default: None): The log level of the message
            flush (optional bool default: False): Whether to flush the logs after logging the
            message
        """
        # Prepend log level if present or default log level is set
        log_level = level or self._log_level
        if log_level is not None:
            msg = f'[{log_level}]: {sep.join([str(msg) for msg in msgs])}{end}'
        else:
            msg = sep.join([str(msg) for msg in msgs]) + end
        # If logger is configured to print locally print to stdout
        if self._print_local:
            print(msg, end='')

        # Add the log to the buffer
        self._logs.append(msg)

        # Flush if necessary
        if flush or self._buffer_size is None or len(self._logs) >= self._buffer_size:
            self.flush()

    def flush(self, suppress_errors: bool | None = None) -> None:
        """
        Flush the logs (print all buffered logs and clear the buffer)

        Args:
            suppress_errors (optional bool | None default: None): If True errors/exceptions raised
            by callbacks will be suppressed. If not present the value set in the constructor will be
            used
        """
        suppress_errors = suppress_errors if suppress_errors is not None else self._suppress_errors
        for log in self._logs:
            for callback in self._callbacks:
                try:
                    callback(log)
                except Exception as err: #pylint: disable=broad-exception-caught
                    if not suppress_errors:
                        raise err
            for async_callback in self._async_callbacks:
                asyncio.create_task(_run_async_callback(async_callback(log), suppress_errors))
        self._logs.clear()

class PrintLogger(Logger):
    """
    Logger wrapper for native Python print
    """

    def __init__(self, default_log_level: str | None = None) -> None:
        self._default_log_level: str | None = default_log_level


    def log(
        self,
        *msgs: Any,
        sep: str=' ',
        end='\n',
        level: str | None = None,
        flush: bool = False
    ) -> None:
        """
        Log a message

        Args:
            msgs (*str): The message(s) to log
            sep (optional str default: ' '): The separator to use when joining the messages
            end (optional str default: '\n'): String to append to the end of the message
            level (optional str | None default: None): The log level of the message
            flush (optional bool default: False): Whether to flush the logs after logging the
            message
        """
        level = level or self._default_log_level
        log_level = '' if level is None else f'[{level}]: '
        print(log_level, *msgs, sep=sep, end=end, flush=flush)

    def flush(self, _suppress_errors: bool | None = None) -> None:
        """
        Flush the logs

        Args:
            suppress_errors (optional bool default: None): Whether to suppress errors that occur
            while flushing the logs
        """

class BatchFileLogger(BufferedLogger):
    """
    Logger that writes logs as files in batches
    """
    def __init__(
        self,
        log_dir: str,
        log_name_format: str = '%Y-%m-%dT%H-%M-%S.log',
        default_log_level: str | None = None,
        print_local: bool = True,
        buffer_size: int | None = None,
        suppress_errors: bool = False,
        use_async: bool = False,
        timeout: float = 10.0
    ) -> None:
        self._log_protocol, self._log_dir, *_ = (
            log_dir.split('://', 1) if '://' in log_dir else ('file', log_dir)
        )
        self._log_protocol = self._log_protocol.lower()
        if self._log_protocol == 'file':
            os.makedirs(self._log_dir, exist_ok=True)
        self._log_name_format = log_name_format
        self._use_async = use_async
        self._timeout = Timeout(
            timeout,
            'ASYNCIO' if use_async else 'THREAD'
        )
        self._timeout.add_callback(self.flush)

        super().__init__(
            default_log_level=default_log_level,
            print_local=print_local,
            buffer_size=buffer_size,
            suppress_errors=suppress_errors
        )

    def _gen_log_name(self) -> str:
        return dt.now().strftime(self._log_name_format)

    def log(
        self,
        *msgs: Any,
        sep: str=' ',
        end='\n',
        level: str | None = None,
        flush: bool = False
    ) -> None:
        super().log(*msgs, sep=sep, end=end, level=level, flush=flush)
        self._timeout.start(raise_error=False)

    def _log(self, log: str) -> None: # TODO: Implement logging to s3 and http
        """
        Log a message to a file
        """
        if self._log_protocol == 'file':
            # Save as file on local storage
            path = os.path.join(self._log_dir, self._gen_log_name())
            with open(path, 'w', encoding='utf-8') as log_file:
                log_file.write(log)
        elif self._log_protocol == 's3':
            # Save to an s3 bucket via boto3 (requires permisions to write to the bucket)
            _bucket, folder = self._log_dir.split('/', 1)
            sep = '/' if folder and not folder.endswith('/') else ''
            _key = f'{folder}{sep}{self._gen_log_name()}'
            raise NotImplementedError('S3 logging has not been implemented yet')
        elif self._log_protocol in ['http', 'https']:
            # Write to an http endpoint (requires the endpoint to be able to accept logs via POST)
            raise NotImplementedError('HTTP logging has not been implemented yet')

    def flush(self, suppress_errors: bool | None = None) -> None:
        """
        Flush the logs (print all buffered logs and clear the buffer)

        Args:
            suppress_errors (optional bool | None default: None): If True errors/exceptions raised
            by callbacks will be suppressed. If not present the value set in the constructor will be
            used
        """
        self._timeout.cancel()
        suppress_errors = suppress_errors if suppress_errors is not None else self._suppress_errors
        if len(self._logs) == 0:
            return
        log_batch = ''.join(self._logs)
        try:
            self._log(log_batch)
        except Exception as err: #pylint: disable=broad-exception-caught
            if not suppress_errors:
                raise err
        self._logs.clear()

class AsyncFileLogger(Logger):
    """
    Logger that asynchronously saves logs

    Args:
        default_log_level (optional str | None default: None): The default log level to use
    Raises:
        RuntimeError: If an asynchronous callback is provided but no running event loop is found
    """

    def __init__(
        self,
        default_log_level: str | None = None,
    ) -> None:
        self._default_log_level: str | None = default_log_level
        self._logs: asyncio.Queue[str] = asyncio.Queue()
        self._running: bool = False
        self._trampoline_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    def log(
        self,
        *msgs: Any,
        sep: str=' ',
        end='\n',
        level: str | None = None,
        **_kwargs
    ) -> None:
        """
        Log a message

        Args:
            msgs (*str): The message to log
            sep (optional str default: ' '): The separator to use when joining the messages
            end (optional str default: '\n'): String to append to the end of the message
            level (optional str | None default: None): The log level of the message
            flush (optional bool default: False): Whether to flush the logs after logging the
        """
        level = level or self._default_log_level
        log_level = f'[{level}]: ' if level is not None else ''
        self._logs.put_nowait(log_level + sep.join([str(msg) for msg in msgs]) + end)

    def flush(self, _suppress_errors: bool | None = None) -> None:
        """
        Flush the logs
        Note: Does nothing as logs are already being saved asynchronously
        """

    async def __aenter__(self) -> 'AsyncFileLogger':
        await self.start()
        return self

    async def __aexit__(self, *_) -> None:
        await self.stop()

    async def start(self) -> None:
        """
        Start saving logs
        """
        async with self._lock:
            if self._running:
                return
            self._running = True
            self._trampoline_task = asyncio.create_task(self._save_logs())

    async def stop(self, force: bool = False) -> None:
        """
        Stop saving logs

        Args:
            force (optional bool default: False): If True, stop saving logs immediately
        """
        async with self._lock:
            if not self._running:
                return
            self._running = False
            if force: # If force, cancel the saving task and wait for it to finish
                self._trampoline_task.cancel()
            await self._trampoline_task

    async def _save_logs(self) -> None:
        log = await self._logs.get()
        # Save the log
        # TODO: Implement log saving
        print(log)
        if self._running:
            self._trampoline_task = asyncio.create_task(self._save_logs())
