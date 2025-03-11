"""Setup script for WhatsApp MCP Server."""

from setuptools import find_packages, setup
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from files
def read_requirements(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

install_requires = read_requirements("requirements.txt")
dev_requires = read_requirements("dev-requirements.txt")

setup(
    name="whatsapp-mcp-server",
    version="0.1.0",
    author="WhatsApp MCP Team",
    description="A server that provides a RESTful API to interact with WhatsApp Business API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/msaelices/whatsapp-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
    },
    entry_points={
        "console_scripts": [
            "whatsapp-mcp=whatsapp_mcp.main:main",
        ],
    },
)

