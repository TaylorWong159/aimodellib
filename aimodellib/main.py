"""
Entry point for all aimodellib scripts
"""

import sys

#pylint: disable=import-error
from .pack import main as package
from .serve import main as serve
from .train import main as train

def main() -> None:
    """
    Entry point for all aimodellib scripts
    """
    mode, *args = sys.argv[1:]
    if mode == 'package':
        package(args)
    elif mode == 'serve':
        serve(args)
    elif mode == 'train':
        train(args)
    else:
        raise ValueError(f'Invalid mode: {mode}')

if __name__ == '__main__':
    main()
