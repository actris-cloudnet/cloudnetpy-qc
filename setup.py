"""Package configuration."""
from typing import Any, Dict

from setuptools import find_packages, setup

version: Dict[str, Any] = {}
with open("cloudnetpy_qc/version.py", encoding="utf-8") as f:
    exec(f.read(), version)  # pylint: disable=W0122

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

setup(
    name="cloudnetpy_qc",
    version=version["__version__"],
    description="Quality control routines for CloudnetPy products",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Finnish Meteorological Institute",
    author_email="actris-cloudnet@fmi.fi",
    url="https://github.com/actris-cloudnet/cloudnetpy-qc",
    license="MIT License",
    packages=find_packages(),
    include_package_data=True,
    setup_requires=["wheel"],
    python_requires=">=3.10",
    install_requires=["numpy", "scipy", "netCDF4", "cfchecker"],
    extras_require={
        "test": [
            "pytest-flakefinder",
            "pylint",
            "mypy",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
)
