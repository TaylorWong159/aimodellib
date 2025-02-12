"""
Utility functions for async operations
"""

import asyncio
from typing import Callable

def create_task[I, O](func: Callable[[I], O], args: I) -> asyncio.Task[O]:
    """
    Create a task to run a function with an argument

    Args:
        func (Callable[[I], O]): The function to run
        args (I): The argument to pass to the function

    Returns:
        asyncio.Task[O]: The task that will run the function
    """
    async def inner() -> O:
        return func(args)
    return asyncio.create_task(inner())

def star_create_task[I, O](func: Callable[[I], O], *args: I, **kwargs) -> asyncio.Task[O]:
    """
    Create a task to run a function with arguments

    Args:
        func (Callable[[I, ...], O]): The function to run
        args (*I): The arguments to unpack and pass to the function
        kwargs (**Any): The keyword arguments to pass to the function

    Returns:
        asyncio.Task[O]: The task that will run the function
    """
    async def inner() -> O:
        return func(*args, **kwargs)
    return asyncio.create_task(inner())
