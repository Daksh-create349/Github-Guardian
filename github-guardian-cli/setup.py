from setuptools import setup, find_packages

setup(
    name="github-guardian",
    version="1.0.1",
    description="Deep Forensic Security Audit Engine & Pre-Commit Shield",
    author="GitHub Guardian Team",
    packages=find_packages(),
    py_modules=["guardian"],
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.7.0",
        "httpx>=0.27.0"
    ],
    entry_points={
        "console_scripts": [
            "guardian=guardian:app",
        ],
    },
)
