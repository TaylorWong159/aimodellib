"""
utility functions
"""
import asyncio
from threading import Thread
from time import sleep
from typing import Callable, Literal

import boto3
from requests import request

S3_CLIENT = boto3.client('s3')

def get_file(path: str) -> bytes:
    """
    Get a file's contents from the local file system, S3, or an HTTP(S) Server

    Args:
        path (str): The path to the file. If no protocol is indicated by the path then it is assumed
        to be a local file path (ex. <protocol>://<uri> or <uri>)

    Raises:
        ValueError: If the protocol is not supported
    """
    protocol, uri = path.split('://', 1) if '://' in path else ('file', path)
    protocol = protocol.lower()
    if protocol == 'file':
        with open(uri, 'rb') as file:
            return file.read()
    if protocol in ['http', 'https']:
        return request('GET', path, timeout=10).content
    if protocol == 's3':
        bucket, key = uri.split('/', 1)
        return S3_CLIENT.get_object(Bucket=bucket, Key=key)['Body'].read()

    raise ValueError(f'Unsupported protocol "{protocol}"')

def save_file(path: str, contents: bytes, content_type: str = 'application/octet-stream') -> None:
    """
    Save a file's contents to the local file system, S3, or an HTTP(S) server

    Args:
        path (str): The path to the file. If no protocol is indicated by the path then it is assumed
        to be a local file path (ex. <protocol>://<uri> or <uri>)
        contents (bytes): The file's contents
        content_type (optional str default: 'application/octet-stream'): The MIME content type of
        the file for use in the HTTP(S) request

    Raises:
        ValueError: If the protocol is not supported
    """
    protocol, uri = path.split('://', 1) if '://' in path else ('file', path)
    protocol = protocol.lower()
    if protocol == 'file':
        with open(uri, 'wb') as file:
            file.write(contents)
            return
    if protocol in ['http', 'https']:
        try:
            res = request(
                'POST',
                path,
                headers={'Content-Type': content_type},
                data=contents,
                timeout=10,
            )
        except TimeoutError:
            request(
                'PUT',
                path,
                headers={'Content-Type': content_type},
                data=contents,
                timeout=10,
            )
            return
        else:
            if not res.ok:
                request(
                    'PUT',
                    path,
                    headers={'Content-Type': content_type},
                    data=contents,
                    timeout=10,
                )
            return
    if protocol == 's3':
        bucket, key = uri.split('/', 1)
        return S3_CLIENT.put_object(Bucket=bucket, Key=key, Body=contents)

    raise ValueError(f'Unsupported protocol "{protocol}"')

class Timeout:
    """
    Class that will run callbacks after a specified timeout

    This class can be used in three modes:
    - ASYNCIO: The callbacks will be run in a separate task
    - THREAD: The callbacks will be run in a separate thread
    - BLOCK: The callbacks will be run in the main thread, blocking until the timeout expires
    """
    def __init__(
        self,
        timeout: float,
        mode: Literal['ASYNCIO', 'THREAD', 'BLOCK'] = 'BLOCK'
    ) -> None:
        self._timeout = timeout
        self._callbacks: list[Callable[[None], None]] = []
        self._mode: Literal['ASYNCIO', 'THREAD', 'BLOCK'] = mode
        self._thread: Thread | None = None
        self._task: asyncio.Task | None = None
        self._is_active: bool = False
        self._cancelled: bool = False

    def __del__(self) -> None:
        if self._thread is not None:
            self._thread.join()
        if self._task is not None:
            self._task.cancel()

    def add_callback(self, callback: Callable[[None], None]) -> None:
        """
        Add a callback function to be run after the timeout

        Args:
            callback (Callable[[None], None]): The callback function to add
        """
        self._callbacks.append(callback)

    def clear_callbacks(self) -> None:
        """
        Clear all callbacks
        """
        self._callbacks.clear()

    def _call_callbacks(self) -> None:
        print('Timeout expired') # TODO: Remove test print
        if not self._cancelled:
            for callback in self._callbacks:
                callback()

    async def _arun(self) -> None:
        await asyncio.sleep(self._timeout)
        self._call_callbacks()
        self._is_active = False

    def _run(self) -> None:
        sleep(self._timeout)
        self._call_callbacks()
        self._is_active = False

    def start(
        self,
        raise_error: bool = True,
        mode: Literal['ASYNCIO', 'THREAD', 'BLOCK'] | None = None
    ) -> None:
        """
        Start the timeout

        Args:
            raise_error (optional bool default: True): If true, raise an error if the timeout is
            already active, otherwise this call will be ignored
            mode (optional Literal['ASYNCIO', 'THREAD', 'BLOCK']): If not None, override the mode
            specified in the constructor
        """
        if self._is_active:
            if raise_error:
                raise ValueError('Timeout already active')
            else:
                return
        self._is_active = True
        self._cancelled = False

        # Start the timeout in whatever mode was specified
        use_mode = mode or self._mode
        if use_mode == 'ASYNCIO':
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                raise ValueError('ASYNCIO mode requires an active event loop') from None
            self._task = asyncio.create_task(self._arun())
        elif use_mode == 'THREAD':
            self._thread = Thread(target=self._run)
            self._thread.start()
        elif use_mode == 'BLOCK':
            self._run()
        else:
            raise ValueError(f'Unsupported mode "{use_mode}"')

    def cancel(self) -> None:
        """
        Cancel the timeout
        """
        if self._is_active:
            self._cancelled = True
