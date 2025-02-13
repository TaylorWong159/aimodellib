"""
Training module executor
"""

import asyncio
import os
import sys

#pylint: disable=import-error
from .util.types import TrainingModule, Logger
from .util.logging import PrintLogger
from .util.asyncutils import star_create_task
from .loading import load_module

PIP_CMD = os.environ.get('PIP_CMD', 'pip')

def _train(
    training_module: TrainingModule,
    model_dir: str,
    *training_args: str,
    tensor_board_enabled: bool = False,
    tensor_board_dir: str = 'tb_logs',
    logger: Logger = PrintLogger()
) -> None:
    # Execute the training script
    logger.log('Training...')
    try:
        training_module.train(
            model_dir,
            *training_args,
            tensor_board_enabled=tensor_board_enabled,
            tensor_board_dir=tensor_board_dir,
            logger=logger
        )
        logger.log('Training completed!')
    except asyncio.CancelledError:
        logger.log('Training cancelled!')
    except Exception as e: #pylint: disable=broad-exception-caught
        logger.log(f'Training failed: {e}')
        raise e

def main(
    args: list[str],
    logger: Logger = PrintLogger(),
    return_future: bool = False,
    tensor_board_enabled: bool = False,
    tensor_board_dir: str = 'tb_logs'
) -> asyncio.Future[None] | None:
    """
    Start training
    """
    # Parse args
    if len(args) < 3:
        logger.log(
            'Usage: python train.py <training_module> <training_entry_point> <artifacts_dir> '
            '[training_args...]'
        )
        return None
    logger.log('Train args:', *args)
    module_path, train_script, model_dir, *training_args = args
    module_path = os.path.abspath(module_path)

    # Load the module
    logger.log('Loading module...')
    training_module: TrainingModule = load_module(module_path, train_script, logger=logger)
    if not TrainingModule.validate(training_module):
        raise ValueError('Invalid training module')
    logger.log('Module loaded!')

    # Execute the training script
    if return_future:
        return star_create_task(
            _train,
            training_module,
            model_dir,
            *training_args,
            tensor_board_enabled=tensor_board_enabled,
            tensor_board_dir=tensor_board_dir,
            logger=logger
        )
    _train(
        training_module,
        model_dir,
        *training_args,
        tensor_board_enabled=tensor_board_enabled,
        tensor_board_dir=tensor_board_dir,
        logger=logger
    )
    return None

if __name__ == '__main__':
    main(sys.argv[1:])
