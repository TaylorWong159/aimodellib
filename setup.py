
import re
from setuptools import setup, find_packages

VERSION_STR_REGEX = re.compile(r'.*VERSION\s*=\s*[\'"]([^\'"]*)[\'"].*')

with open('aimodellib/__init__.py', 'r', encoding='utf-8') as f:
    version_str = f.readline().split('=')[1].strip().strip('"')
    version = VERSION_STR_REGEX.match(version_str).group(1)

setup(
    name='aimodellib',
    version=version,
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
