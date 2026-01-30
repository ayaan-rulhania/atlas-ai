"""
Setup script for Atlas AI Python SDK
"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="atlas-ai",
    version="2.5.0",
    author="Atlas AI",
    author_email="support@atlas-ai.com",
    description="Python SDK for Atlas AI - Generate API keys and make chat requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ayaan-rulhania/atlas-ai",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "atlas-api=atlas_ai.api_key:api",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
