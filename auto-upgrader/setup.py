from setuptools import find_packages, setup

setup(
    name="auto-upgrader",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "PyGithub",
    ],
    entry_points={
        "console_scripts": [
            "upgrader=upgrader:cli",
        ],
    },
)
