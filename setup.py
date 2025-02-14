from setuptools import setup, find_packages

setup(
    name='aimodellib',
    version='1.0.0-a3',
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
