"""
Utils for loading modules
"""

from importlib.util import spec_from_file_location, module_from_spec
import os
import subprocess as sp
import sys
import threading
from types import ModuleType
from typing import IO

from ..util import Logger

PIP_CMD = os.environ.get('PIP_CMD', 'pip')

# def send_get_request(url: str, timeout: float = 5.0) -> bytes:
#     """"""

def load_module(
    module_path: str,
    script: str,
    logger: Logger | None = None,
    silent: bool = False
) -> ModuleType:
    """
    Load a module by name
    """
    if silent:
        # Suppress all output
        def log(*_1, **_2):
            ...
    elif logger is not None:
        # Use logger
        log = logger.log
    else:
        # Use print
        def log(*args, level='INFO', **kwargs):
            print(f'[{level}]:', *args, **kwargs)

    # Add training module to path
    sys.path.append(module_path)

    # Install requirements if present
    requirements_file = os.path.join(module_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        log('Installing requirements...')
        with sp.Popen(
            args=[PIP_CMD, 'install', '-r', requirements_file],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            universal_newlines=True
        ) as pip_process:
            def reader(io: IO[str], level: str = 'INFO') -> None:
                for line in iter(io.readline, ''):
                    log(line, level=level, flush=True)
            stdout_thread = threading.Thread(
                target=reader,
                args=(pip_process.stdout,),
                kwargs={'level': 'INFO'}
            )
            stderr_thread = threading.Thread(
                target=reader,
                args=(pip_process.stderr,),
                kwargs={'level': 'ERROR'}
            )
            stdout_thread.start()
            stderr_thread.start()
            stdout_thread.join()
            stderr_thread.join()

            if pip_process.poll() != 0:
                raise ValueError(f'Failed to install requirements: {pip_process.stderr.read()}')
        log('Requirements installed!')

    # Load the module from the script
    log('Loading module...')
    module_spec = spec_from_file_location(
        'model_module',
        os.path.join(module_path, script)
    )
    if module_spec is None:
        raise ValueError(f'Could not load module "{script}"')
    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    log('Module loaded!')
    return module
