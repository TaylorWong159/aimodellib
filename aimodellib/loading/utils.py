"""
Utils for loading modules
"""

from importlib.util import spec_from_file_location, module_from_spec
import os
import subprocess as sp
import sys

from ..util import Logger

PIP_CMD = os.environ.get('PIP_CMD', 'pip')

def load_module(
    module_path: str,
    script: str,
    logger: Logger | None = None,
    silent: bool = False
) -> None:
    """
    Load a module by name
    """
    log = logger.log if logger is not None else print if not silent else lambda *_1, **_2: None

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
            for line in iter(pip_process.stdout.readline, ''):
                log(line, end='')
            status_code = pip_process.wait()
            if status_code != 0:
                raise ValueError(f'Failed to install requirements: {pip_process.stderr.read()}')
        log('Requirements installed!')

    # Load the module from the script
    log('Loading module...')
    module_spec = spec_from_file_location(
        'model_module',
        os.path.join(module_path, script)
    )
    if module_spec is None:
        raise ValueError(f'Could not load training module "{script}"')
    module = module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    log('Module loaded!')
