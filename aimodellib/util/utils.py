"""
utility functions
"""

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
        return request('GET', uri, timeout=10).content
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
                uri,
                headers={'Content-Type': content_type},
                data=contents,
                timeout=10,
            )
        except TimeoutError:
            request(
                'PUT',
                uri,
                headers={'Content-Type': content_type},
                data=contents,
                timeout=10,
            )
            return
        else:
            if not res.ok:
                request(
                    'PUT',
                    uri,
                    headers={'Content-Type': content_type},
                    data=contents,
                    timeout=10,
                )
            return
    if protocol == 's3':
        bucket, key = uri.split('/', 1)
        return S3_CLIENT.put_object(Bucket=bucket, Key=key, Body=contents)

    raise ValueError(f'Unsupported protocol "{protocol}"')
