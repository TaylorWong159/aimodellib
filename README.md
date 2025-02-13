# AI Model Library
This library is designed to standardize the training and deployment of AI models using Python as a scripting language

## Training
The purpose of this library is to provide external programs with a standard interface to train and serve models. Training is done through the TrainingModule protocol (see `aimodellib.util.types.TrainingModule`). This library also comes with a basic runner indended for local testing before packaging for said external programs. To use the basic training runner you can run the following command:
```
aimodellib train <training_module> <training_script> <model_dir> [training_args]
```

- **training_module:** The path to the folder containing the training script, other source code files, and optionally a requirements file (`requirements.txt`)
- **training_script:** The name of the python training script to use (for more detail see [The Training Script](#the-training-script))
- **model_dir:** The path to the folder to save any generated artifacts to
- **training_args:** Arguments to be passed onto the training script

### The Training Script
The training script **MUST** implement the `TrainingModule` protocol. This means the script should expose a `train` function compatible with the following signature:
``` python
def train(
    model_dir: str,
    *args: str,
    tensor_board_enabled: bool = False,
    tensor_board_dir: str = 'logs',
    logger: Logger | None = None
) -> None:
    ...
```
- **model_dir:** The directory to save any artifacts to
- **\*args:** The arguments passed to the training script as strings
- **tensor_board_enabled:** This will indicate whether or not tensorboard has been enabled by an external program
- **tensor_board_dir:** If tensorboard has been enabled this will contain the directory the training script should save tensorboard logs to
- **logger:** If a logger is provided the training script should use that logger to log any messages. See `aimodellib.utils.Logger` for more detail on the `Logger` protocol. `Logger.log` has a similar signature to print. There is also a class `aimodellib.utils.PrintLogger` that wraps the standard `print` function while implementing the `Logger` protocol although it can only print to stout.


## Serving
As previously stated, the purpose of this library is to provide external programs with a standard interface to train and serve models. Serving is done through the InferenceModule protocol (see `aimodellib.util.types.InferenceModule`). This library also comes with a basic runner indended for local testing before packaging for said external programs. To use the basic serving runner you can run the following command:
```
aimodellib serve <inference_module> <inference_script> <model_dir>
```

- **serving_module:** The path to the folder containing the serving script, other source code files, and optionally a requirements file (`requirements.txt`)
- **serving_script:** The name of the python serving script to use (for more detail see [The Serving Script](#the-serving-script))
- **model_dir:** The path to the folder to read any artifacts from

### The Serving Script
The serving script **MUST** implement the `InferenceModule` protocol. This means the script should expose functions compatible with the following signatures:
``` python
def load(model_dir: str, logger: Logger | None = None) -> Model:
    ...

def deserialize(
    data: bytes,
    content_type: str = 'application/octet-stream',
    logger: Logger | None = None
) -> Input:
    ...

def predict(data: Input, model: Model, logger: Logger | None = None) -> Output:
    ...

def serialize(
    data: Output,
    accepted: str = '*/*',
    logger: Logger | None = None
) -> tuple[bytes, str] | None:
    ...
```
#### Load:
Load and return a model
- **model_dir:** The directory to load any artifacts from
- **logger:** If provided it should be used to log any messages

#### Deserialize:
Deserialize/decode bytes to a valid input type
- **data:** The bytes
- **content_type:** The content type of the bytes (if not present should be assumed to be "application/octet-stream")
- **logger:** If provided it should be used to log any messages

#### Predict:
Make a prediction/inference on an input
- **data:** The input
- **model:** The model loaded by the load function
- **logger:** If provided it should be used to log any messages

#### Serialize:
Serialize/encode a prediction back to bytes. Return the bytes and the content type of them
- **data:** The prediction
- **accepted:** Acceptable formats to serialize to (if not present should be assumed to be "*/*" i.e. any format)
- **logger:** If provided it should be used to log any messages


## Packaging
External programs should use the following **Model Archive** specification when transferring models and their artifacts.

### Model Archive
A **Model Archive** is a **gzip** compressed **tar** archive file (`.tar.gz`) containing:
    1. The source code required for training and serving the model
    2. A requirements file (`requirements.txt`) containing any additional pip requirements; and
    3. A manifest file (`manifest.json`) (see [The Manifest File](#the-manifest-file) for details)
The path from the archive root to the folder containing all of the source code and requirements file will be known as the **module dir**. 

### Generating the Model Archive
A **Model Archive** can be generated manually using an archiving tool (`tar`, `7z`, etc.) and providing the required files or can be generated using the included packaging module.

#### The Packaging Module
The packaging module will create the archive and generate a manifest file for you or you can specify your own.
```
aimodellib package [OPTIONS]
```
| Option Flag(s)                | Description                                                                                                                                                               | Default                     |
|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------|
| **--module-dir, -m**          | The path to the directory containing all of the source files and an optional requirements.txt file                                                                        | **""**                      |
| **--train-script, -t**        | The path from the module directory to the training script to use (see [Training](#Training) for details on the training script requirements)                              | **"train.py"**              |
| **--serve-script, -s**        | The path from the module directory to the serving script to use (see [Serving](#Serving) for details on the serving script requirements)                                  | **"serve.py"**              |
| **--log-name-format, -l**     | The strftime formate string to use for naming log files                                                                                                                   | **"%Y-%m-%dT%H-%M-%S.log"** |
| **--log-dir, -L**             | The path from the package root to save log files to                                                                                                                       | **"logs"**                  |
| **--enable-tensorboard**      | If present a tensorboard server will be run on TB_PORT or 6006                                                                                                            | **N/A**                     |
| **--tensorboard-dir, -T**     | The path from the package root to save tensorboard logs to for the server to use                                                                                          | **"tb_logs"**               |
| **--manifest-file, -M**       | The path to a manifest file to use instead of generating one from the arguments above (see [Manifest File](#Manifest-File) for details on the manifest file requirements) | **N/A**                     |
| **--output, -o**              | The path to save the output model package to                                                                                                                              | **"model.tar.gz"**          |

### The Manifest File
A manifest file **must** be named `manifest.json` (case sensitive). If it has any other name it will be treated as invalid. It must be a well structured JSON file with one top-level object containing the parameters required for training and serving. Those parameters are as follows:

| Parameter                | Description                                            | Type               | Default                     |
|--------------------------|--------------------------------------------------------|--------------------|-----------------------------|
| **module**               | The path to the module dir                             | **string**         | **""**                      |
| **trainingScript**       | The path to the training script from the module dir    | **string \| null** | **null**                    |
| **servingScript**        | The path to the serving script from the module dir     | **string \| null** | **null**                    |
| **logDirectory**         | The path to save log files to                          | **string**         | **"logs"**                  |
| **logNamingFormat**      | The strftime format string to use for naming log files | **string**         | **"%Y-%m-%dT%H-%M-%S.log"** |
| **enableTensorboard**    | Whether or not to enable tensorboard                   | **boolean**        | **false**                   |
| **tensorboardDirectory** | The path to save and read tensorboard logs to and from | **string**         | **"tb_logs"**               |

External programs are may support additional parameters but **MUST** accept all those listed above. Any external program that does not accept all of these parameters cannot be considered to adhere to the aimodellib protocol.

#### Example manifest file:
``` JSON
// manifest.json
{
    "trainingScript": "main.py",
    "servingScript": "main.py",
    "module": "",
    "logDirectory": "logs",
    "logNamingFormat": "%Y-%m-%dT%H-%M-%S.log",
    "enableTensorboard": true,
    "tensorboardDirectory": "tb_logs"
}
```
#### This example specifies:
- The archive root as the module dir
- main.py as both the training script and serving script
- "logs/"%Y-%m-%dT%H-%M-%S.log" as the format log files should be save in; and
- Tensorboard should be enabled and use "tb_logs" as the tensorboard log directory
