from setuptools import setup, find_packages

VERSION = "0.0.1"
DESCRIPTION = "Estimate the stop times for a GTFS feed in the Databús platform."
with open("README.md", "r") as f:
    LONG_DESCRIPTION = f.read()


setup(
    name="databus_stoptimes",
    packages=find_packages(include=["stoptimes"]),
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Fabián Abarca, Anthony Monestel, Ulises Fonseca, Jesús Mena, Joselyn Castillo, Juan Sebastián Pereira",
    author_email="fabian.abarca@ucr.ac.cr",
    url="https://databus-stoptimes.readthedocs.io/",
    license="MIT",
    install_requires=[
        "pandas",
        "geopandas",
        "shapely",
        "numpy",
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
    ],
)
