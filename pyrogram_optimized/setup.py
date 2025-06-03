#!/usr/bin/env python3
"""
Setup script for Pyrogram Optimized
High-performance Telegram MTProto API client
"""

import os
import sys
from setuptools import setup, find_packages

# Read version from __init__.py
with open("__init__.py", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]
            break
    else:
        version = "2.1.21-optimized"

# Read README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Separate optional requirements
core_requirements = []
optional_requirements = []

for req in requirements:
    if any(opt in req for opt in ["uvloop", "orjson", "aiofiles", "msgpack", "lz4", "xxhash", "psutil"]):
        optional_requirements.append(req)
    else:
        core_requirements.append(req)

setup(
    name="pyrogram-optimized",
    version=version,
    description="High-performance Telegram MTProto API client based on Pyrogram",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pyrogram Optimized Team",
    author_email="dev@pyrogram-optimized.org",
    url="https://github.com/pyrogram-optimized/pyrogram-optimized",
    license="LGPLv3",
    
    packages=find_packages(),
    python_requires=">=3.8",
    
    install_requires=core_requirements,
    
    extras_require={
        "fast": [
            "tgcrypto>=1.2.5",
            "cryptography>=41.0.0",
            "orjson>=3.9.0",
            "aiofiles>=23.0.0",
        ],
        "full": optional_requirements,
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    keywords=[
        "telegram", "chat", "messenger", "api", "client", "library", "python",
        "mtproto", "pyrogram", "performance", "optimization", "async", "bot"
    ],
    
    project_urls={
        "Documentation": "https://pyrogram-optimized.readthedocs.io/",
        "Source": "https://github.com/pyrogram-optimized/pyrogram-optimized",
        "Tracker": "https://github.com/pyrogram-optimized/pyrogram-optimized/issues",
    },
    
    entry_points={
        "console_scripts": [
            "pyrogram-optimized=pyrogram_optimized.cli:main",
        ],
    },
    
    include_package_data=True,
    zip_safe=False,
)