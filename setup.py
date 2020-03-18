from setuptools import setup, find_packages
setup(
    name="session_management",
    version="0.1",
    packages=find_packages(),
    package_data={'': ['*.kv']},
    install_requires=['typing_extensions', 'python-reapy'],
)
