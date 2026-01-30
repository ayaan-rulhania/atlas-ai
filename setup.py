"""
Setup script for Atlas CLI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file if it exists
readme_file = Path(__file__).parent / "apps" / "cli" / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read version from cli/__init__.py
version = "0.1.0"
try:
    init_file = Path(__file__).parent / "apps" / "cli" / "__init__.py"
    if init_file.exists():
        for line in init_file.read_text().splitlines():
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"').strip("'")
                break
except Exception:
    pass

setup(
    name="atlas-cli",
    version=version,
    description="Atlas CLI - Command-line interface for Atlas AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Atlas AI",
    url="https://github.com/ayaan-rulhania/atlas-ai",
    packages=find_packages(include=["apps.cli*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "pyfiglet>=1.0.0",
        "colorama>=0.4.6",
    ],
    entry_points={
        "console_scripts": [
            "atlas-cli=apps.cli.atlas_cli:main",
        ],
    },
    package_dir={"": "."},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
