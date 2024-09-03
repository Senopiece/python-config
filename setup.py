from setuptools import setup, find_packages

setup(
    name="python_config",
    version="1.0",
    description="Library for loading yml configurations",
    author="Vitaly Mahonin",
    author_email="nabuki@vk.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
    ],
    python_requires=">=3.8",
)
