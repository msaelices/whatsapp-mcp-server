"""Setup script for WhatsApp MCP Server."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

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
    install_requires=[
        "pydantic>=2.0.0",
        "qrcode>=7.0",
        "Pillow>=9.0.0",
        "click>=8.0.0",
        "mcp>=1.3.0",
        "whatsapp-api-client-python==0.0.49",
    ],
    entry_points={
        "console_scripts": [
            "whatsapp-mcp=whatsapp_mcp.main:main",
        ],
    },
)

