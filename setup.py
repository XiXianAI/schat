from setuptools import setup, find_packages

setup(
    name="schat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.18.1",
        "google-generativeai>=0.3.0",
    ],
) 