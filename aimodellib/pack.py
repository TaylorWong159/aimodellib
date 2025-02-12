"""
Packaging module for use with the ai_model_lib package
"""

import argparse
from io import BytesIO
import json
import os
import sys
import tarfile

from .manifest.utils import validate_manifest # pylint: disable=import-error

def main(args: list[str]) -> None:
    """
    Package a model module for training/deployment
    """
    # Parse args
    parser = argparse.ArgumentParser(description='Package the model for deployment')
    parser.add_argument(
        '--module-dir',
        help='The directory containing the model module',
        type=str,
        default=''
    )
    parser.add_argument(
        '--train-script',
        help='The path from the module dir to the training script',
        type=str,
        default='train.py'
    )
    parser.add_argument(
        '--serve-script',
        help='The path from the module dir to the serving script',
        type=str,
        default='serve.py'
    )
    parser.add_argument(
        '--log-name-format',
        help='The format for the log file name',
        type=str,
        default='%Y-%m-%dT%H-%M-%S.log'
    )
    parser.add_argument(
        '--log-dir',
        help='The directory to store logs',
        type=str,
        default='logs'
    )
    parser.add_argument(
        '--enable-tensorboard',
        help='Enable tensorboard logging',
        action='store_true'
    )
    parser.add_argument(
        '--tensorboard-dir',
        help='The directory to store tensorboard logs',
        type=str,
        default='tb_logs'
    )
    parser.add_argument(
        '--manifest-file',
        help='The path a the manifest file to use (overrides other options)',
        type=str
    )
    parser.add_argument(
        '--output', '-o',
        help='The path to save the packaged model',
        type=str,
        default='model.tar.gz'
    )
    args = parser.parse_args(args)

    # Extract arguments
    output_path: str = args.output
    manifest_file: str | None = args.manifest_file
    module_dir: str = args.module_dir
    if manifest_file is not None:
        if not os.path.exists(manifest_file):
            raise ValueError(f'Manifest file "{manifest_file}" does not exist')
        with open(manifest_file, 'r', encoding='utf-8') as file:
            manifest = validate_manifest(json.load(file))
        module_name = manifest['module']
    else:
        module_name = os.path.basename(os.path.abspath(module_dir))
        manifest = {
            'module': module_name,
            'trainingScript': args.train_script,
            'servingScript': args.serve_script,
            'logNamingFormat': args.log_name_format,
            'logDirectory': args.log_dir,
            'enableTensorboard': args.enable_tensorboard,
            'tensorboardDirectory': args.tensorboard_dir
        }

    # Validate the training script
    train_script_path = os.path.join(module_dir, manifest['trainingScript'])
    if not os.path.exists(train_script_path):
        raise ValueError(f'Unable to locate training script at "{train_script_path}"')


    serve_script_path = os.path.join(module_dir, manifest['servingScript'])
    if not os.path.exists(serve_script_path):
        raise ValueError(f'Unable to locate serveing script at "{serve_script_path}"')

    # Create the package
    with tarfile.open(output_path, 'w:gz') as package:
        package.add(module_dir, arcname=module_name)
        if manifest_file is not None:
            package.add(manifest_file, arcname='manifest.json')
        else:
            manifest_dump = json.dumps(manifest).encode('utf-8')
            info = tarfile.TarInfo('manifest.json')
            info.size = len(manifest_dump)
            with BytesIO() as bio:
                bio.write(manifest_dump)
                bio.seek(0)
                package.addfile(info, bio)

if __name__ == '__main__':
    main(sys.argv[1:])
