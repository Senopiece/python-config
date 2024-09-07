from setuptools import setup, find_packages

setup(
    name="configurable",
    version="1.2",
    description="Library for loading yml configurations",
    author="Vitaly Mahonin",
    author_email="nabuki@vk.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.1,<2.0.0",
    ],
    python_requires=">=3.8",
)
