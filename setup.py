#!/usr/bin/env python3

from setuptools import setup

setup(
    name="pymelcloud",
    version="0.1.0",
    description="Python MELCloud interface",
    author="Vilppu Vuorinen",
    author_email="vilppu.jotain@gmail.com",
    license="MIT",
    url="https://github.com/vilppuvuorinen/pymelcloud",
    python_requires=">3.5",
    packages=["pymelcloud"],
    keywords=["homeautomation", "melcloud"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Home Automation",
    ],
    install_requires=["aiohttp"],
    scripts=[],
)
