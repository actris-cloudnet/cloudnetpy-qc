
from setuptools import setup, find_packages

version = {}
with open("cloudnetpy_qc/version.py") as f:
    exec(f.read(), version)

with open('README.md') as f:
    readme = f.read()

setup(
    name='cloudnetpy_qc',
    version=version['__version__'],
    description='Quality control routines for CloudnetPy',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Finnish Meteorological Institute',
    author_email='actris-cloudnet@fmi.fi',
    url='https://github.com/actris-cloudnet/cloudnetpy-qc',
    license='MIT License',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=['numpy', 'netCDF4'],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
    ],
)
