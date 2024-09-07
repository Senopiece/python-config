from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="configurik",
    version="1.2",
    description="Library for loading yml configurations",
    author="Vitaly Mahonin",
    author_email="nabuki@vk.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv>=1.0.1,<2.0.0",
    ],
    python_requires=">=3.8",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Senopiece/python-config",
)
