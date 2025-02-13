"""
Types for the ai_model_lib package.
"""

from typing import Any, Protocol

class Logger(Protocol):
    """
    Generic logger interface containing a log method for logging/buffering messages and a flush
    method for flushing log buffers
    """

    ERROR: str = 'ERROR'
    INFO: str = 'INFO'
    WARNING: str = 'WARNING'
    DEBUG: str = 'DEBUG'

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
            msg (*str): The message(s) to log
            sep (optional str default: ' '): The separator to use when joining the messages
            end (optional str default: '\n'): String to append to the end of the message
            level (optional str | None default: None): The log level of the message
            flush (optional bool default: False): Whether to flush the logs after logging the
            message
        """

    def flush(self, suppress_errors: bool | None = None):
        """
        Flush the logs

        Args:
            suppress_errors (optional bool default: None): Whether to suppress errors that occur
            while flushing the logs
        """

#pylint: disable=undefined-variable
class InferenceModule[Model, Input, Output](Protocol):
    """
    A module that can be used to perform inference
    """

    def load(self, model_dir: str, logger: Logger | None = None) -> Model:
        """
        Load the model

        Args:
            model_dir (str): The path to the directory containing the model artifacts
            logger (Logger | None): A logger passed in to use for logging. If not present it should
            be assumed to be None

        Returns:
            Model: The model loaded from the artifacts
        """

    def deserialize(
        self,
        data: bytes,
        content_type: str = 'application/octet-stream',
        logger: Logger | None = None
    ) -> Input:
        """
        Deserialize input data

        Args:
            data (bytes): The input data to deserialize
            content_type (str): The content type of the
            input data. If not present it should be assumed to be application/octet-stream
            logger (Logger | None): A logger passed in to use for logging. If not present it should
            assumed to be None

        Returns:
            Input: The deserialized input data
        """

    def predict(self, data: Input, model: Model, logger: Logger | None = None) -> Output:
        """
        Perform inference

        Args:
            data (Input): The input data to perform inference on
            model (Model): The model to use for inference
            logger (Logger | None): A logger passed in to use for logging. If not present it should
            assumed to be None

        Returns:
            Output: The result of the inference
        """

    def serialize(
        self,
        data: Output,
        accepted: str = '*/*',
        logger: Logger | None = None
    ) -> tuple[bytes, str] | None:
        """
        Serialize output data to an accepted content type

        Args:
            data (Output): The output data to serialize
            accepted (str): The content type the client requesting inference will accept. If not
            present it should be assumed to be */*
            logger (Logger | None): A logger passed in to use for logging. If not present it should
            be assumed to be None

        Returns:
            tuple[bytes, str] | None: The serialized output data and its content type if it can be
            serialized to an accepted content type or None if it cannot
        """

    @staticmethod
    def validate(obj: Any) -> bool:
        """
        Validate the object fufills the InferenceMoule protocol

        Args:
            obj (Any): The object to validate

        Returns:
            bool: True if the object fufills the protocol, False otherwise
        """
        return all(hasattr(obj, attr) for attr in ['load', 'deserialize', 'predict', 'serialize'])

class TrainingModule(Protocol):
    """
    A module that can be used to train a model
    """

    def train(
        self,
        model_dir: str,
        *args: str,
        tensor_board_enabled: bool = False,
        tensor_board_dir: str = 'logs',
        logger: Logger | None = None
    ) -> None:
        """
        Train the model

        Artifacts can and should be saved in model_dir. If tensor_board_enabled is True, tensorboard
        logs can be saved in tensor_board_dir to utilize tensorboard for visualization.

        Args:
            model_dir (str): The path to the directory where the training artifacts should be saved
            *args (str): Specific arguments for training
            tensor_board_enabled (bool): Whether to tensorboard is enabled. If not present it should
            be assumed to be False
            tensor_board_dir (str): The path to the directory where the tensorboard logs should be
            saved if tensorboard is enabled. If not present it should be assumed to be 'logs'
            logger (Logger | None): A logger passed in to use for logging. If not present it should
            be assumed to be None
        """

    @staticmethod
    def validate(obj: Any) -> bool:
        """
        Validate the object fufills the TrainingModule protocol

        Args:
            obj (Any): The object to validate

        Returns:
            bool: True if the object fufills the protocol, False otherwise
        """
        return all(hasattr(obj, attr) for attr in ['train'])
