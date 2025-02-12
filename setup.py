from setuptools import setup, find_packages

setup(
    name='aimodellib',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'boto3',
        'requests',
        'tensorboard'
    ],
    entry_points={
        'console_scripts': [
            'aimodellib=aimodellib.main:main'
        ]
    }
)
