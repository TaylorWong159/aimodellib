"""
manifest utils
"""

from typing import Any

from ..util.types import Logger

def json_typeof(val: Any, default: str | None = None) -> str:
    """
    Get the JSON data type of a value

    Args:
        val (Any): The value to check
        default (optional str | None default: None): The default value to return if the value is not
        a valid JSON. If None then an error is raised

    Returns:
        str: The JSON data type of the value

    Raises:
        ValueError: If the value is not a valid JSON type and no default is provided
    """
    if isinstance(val, bool):
        dtype = 'boolean'
    elif isinstance(val, (int, float)):
        dtype = 'number'
    elif isinstance(val, str):
        dtype = 'string'
    elif isinstance(val, list):
        dtype = 'array'
    elif isinstance(val, dict):
        dtype = 'object'
    elif val is None:
        dtype = 'null'
    else:
        if default is not None:
            return default
        raise ValueError(f'Object of type "{type(val)}" is not a valid JSON type')
    return dtype

# Dict of valid manifest arguments, valid types, and default values
# For required args use a default value that is an invalid type (ex. None if 'null' is not valid)
MANIFEST_ARGS: dict[str, tuple[str, tuple[type], Any]] = {
    'training_script': ('trainingScript', ('string', 'null'), None),
    'serving_script': ('servingScript', ('string', 'null'), None),
    'module': ('module', ('string',), ''),
    'log_dir': ('logDirectory', ('string',), 'logs'),
    'log_name_fmt': ('logNamingFormat', ('string',), '%Y-%m-%dT%H-%M-%S.log'),
    'enable_tb': ('enableTensorboard', ('boolean',), False),
    'tb_log_dir': ('tensorboardDirectory', ('string',), 'tb_logs')
}

def validate_manifest(
    manifest: dict[str, Any],
    logger: Logger | None = None
) -> dict[str, Any] | None:
    """
    Validate a manifest JSON dictionary

    Args:
        manifest (dict[str, Any]): The manifest to validate
        logger (optional Logger | None default: None): The logger to use for logging errors and
        warnings

    Returns:
        dict[str, Any] | None: The validated manifest stripped of unrecognized arguments or None if
        the manifest is invalid
    """
    log = logger.log if logger is not None else lambda *_args, **_kwargs: None
    res: dict[str, Any] = {}
    for arg, (arg_name, arg_t, default) in MANIFEST_ARGS.items():
        val = manifest.get(arg_name, default)
        val_t = json_typeof(val, '<unknown>')
        if val_t not in arg_t:
            log(
                f'Manifest argument "{arg_name}" with value "{val}" has invalid type "{val_t}". '
                f'Expected: {" | ".join(arg_t)}',
                level=Logger.ERROR
            )
            return None
        res[arg] = val
    arg_names = {arg_name for arg_name, *_ in MANIFEST_ARGS.values()}
    for arg in manifest:
        if arg not in arg_names:
            log(f'Unrecognized argument "{arg}"', level=Logger.WARNING)
    return res
