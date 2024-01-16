from setuptools import find_packages, setup

setup(
    name='estimator',
    packages=find_packages(include=['estimator']),
    version='0.0.1',
    description='Estimador de stop times GTFS',
    author='Anthony Monestel'
    license='MIT',
    install_requires=[
        'numpy',
        'pandas',
    ],
)
