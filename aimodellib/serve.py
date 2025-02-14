"""
Training module executor
"""

import asyncio
import os
import sys

import aiohttp
import aiohttp.web

#pylint: disable=import-error
from .util.types import InferenceModule, Logger
from .util.logging import PrintLogger
from .loading import load_module

PIP_CMD = os.environ.get('PIP_CMD', 'pip')

BAD_REQ = 400
SERVER_ERR = 500

async def _run_server(app: aiohttp.web.Application, logger: Logger, port: int = 8080) -> None:
    try:
        logger.log('Starting server...')
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, port=port)
        await site.start()
        logger.log('Server started!')
        await asyncio.Future() # Run till cancelled
    except asyncio.CancelledError:
        logger.log('Server')
    finally:
        logger.log('Cleaning up server resources...')
        await runner.cleanup()
        logger.log('Server resources cleaned up!')

def main(
    args: list[str],
    logger: Logger=PrintLogger(),
    return_future: bool = False
) -> asyncio.Future[None] | None:
    """
    Start serving inference requests
    """
    # Parse args
    if len(args) < 2:
        logger.log(
            'Usage: aimodellib serve <inference_module> <inference_script> <model_dir> [port]'
        )
        return None
    # Parse args
    logger.log('Serve args:', *args)
    module_path, inference_script, model_dir, *serve_args = args
    module_path = os.path.abspath(module_path)
    if len(serve_args) > 0:
        try:
            port = int(serve_args[0])
        except ValueError as err:
            raise ValueError(f'Invalid port "{serve_args[0]}"') from err
    else:
        port = 8080

    # Load the module
    logger.log('Loading module...')
    inference_module: InferenceModule = load_module(module_path, inference_script, logger=logger)
    if not InferenceModule.validate(inference_module):
        raise ValueError('Invalid inference module')
    logger.log('Module loaded!')

    logger.log('Loading Model...')
    model = inference_module.load(model_dir, logger=logger)
    logger.log('Model loaded!')
    # Setup request handlers
    routes = aiohttp.web.RouteTableDef()

    # GET /ping should respone 200 OK
    @routes.get('/ping')
    async def ping(_req: aiohttp.web.Request) -> aiohttp.web.Response:
        return aiohttp.web.Response()

    # POST /invocations should perform inference
    @routes.post('/invocations')
    async def invoke(req: aiohttp.web.Request) -> aiohttp.web.Response:
        try:
            content_type = req.headers.get('Content-Type', 'application/octet-stream')
            accepted = req.headers.get('Accept', '*/*')
            req_body = await req.read()
            output_uri: str | None = None

            # If Content-Type is uri-list then the data is to be transfered via an external api
            if content_type == 'text/uri-list':
                uri_list = req_body.decode('utf-8').split('\r\n')
                if len(uri_list) != 2:
                    return aiohttp.web.Response(status=BAD_REQ, body='Invalid URI list')
                input_uri, output_uri = uri_list
                async with aiohttp.ClientSession() as session:
                    async with session.get(input_uri) as res:
                        req_body = await res.read()

            input_data = inference_module.deserialize(req_body, content_type, logger=logger)
            output = inference_module.predict(input_data, model, logger=logger)
            res_body = inference_module.serialize(output, accepted, logger=logger)
            if res_body is None:
                return aiohttp.web.Response(
                    status=BAD_REQ,
                    body='Unable to serialize output to an accepted content type'
                )

            if output_uri is not None: # Output should be sent to an external api
                async with aiohttp.ClientSession() as session:
                    async with session.post(output_uri, data=res_body) as res: # PUT or POST?
                        if res.ok:
                            return aiohttp.web.Response(text=f'Output written to "{output_uri}"')
                        return aiohttp.web.Response(
                            status=res.status,
                            body=await res.read()
                        )
            # Send output in the response
            return aiohttp.web.Response(body=res_body)
        except Exception as err: #pylint: disable=broad-exception-caught
            return aiohttp.web.Response(status=SERVER_ERR, body=str(err))
    app = aiohttp.web.Application()
    app.add_routes(routes)

    # Run the server
    if return_future:
        return asyncio.create_task(_run_server(app, logger, port=port))
    aiohttp.web.run_app(app, port=port)

if __name__ == '__main__':
    main(sys.argv[1:])
