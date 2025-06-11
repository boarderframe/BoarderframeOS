"""
Setup configuration for BoarderframeOS package.
"""
from setuptools import setup, find_packages

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README for long description
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="boarderframeos",
    version="0.1.0",
    author="BoarderFrame",
    author_email="boarderframe@gmail.com",
    description="AI-Native Operating System with distributed agent coordination",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/boarderframe/BoarderframeOS",
    packages=find_packages(exclude=["tests*", "docs*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "boarderframeos=startup:main",
            "bfos=startup:main",
        ],
    },
    include_package_data=True,
    package_data={
        "boarderframeos": [
            "configs/*.json",
            "configs/*.yaml",
            "migrations/*.sql",
            "templates/*.html",
        ],
    },
)