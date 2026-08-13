#!/usr/bin/env python3
"""Setup script for LOQ Power Manager."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="loq-power-manager",
    version="0.2.0",
    author="Anindra",
    author_email="anindrakarmakar+git@proton.me",
    description="Power profile and battery manager for Lenovo LOQ laptops",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/an1ndra/loq-power-manager",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "PyQt6>=6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "loq-power-manager=loq_power_manager.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Hardware",
        "Topic :: Utilities",
    ],
)
