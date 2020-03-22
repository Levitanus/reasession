from setuptools import setup, find_packages
setup(
    name="reasession",
    version="0.1",
    packages=find_packages(),
    package_data={'': ['*.kv', 'py.typed']},
    install_requires=['typing_extensions', 'python-reapy'],
)
