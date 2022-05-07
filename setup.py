#!/usr/bin/env python3

import setuptools

with open("README.md") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    install_requires = fh.read()

name = "vsencoder"
version = "1.0.0"
release = "1.0.0"

setuptools.setup(
    name=name,
    version=release,
    author="LightArrowsEXE",
    author_email="Lightarrowsreboot@gmail.com",
    description="vs-encoder, an extensive wrapper around vardautomation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["vsencoder"],
    url="https://github.com/Irrational-Encoding-Wizardry/vs-encoder",
    package_data={
        'vsencoder': ['py.typed'],
    },
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    command_options={
        "build_sphinx": {
            "project": ("setup.py", name),
            "version": ("setup.py", version),
            "release": ("setup.py", release),
            "source_dir": ("setup.py", "docs")
        }
    }
)
