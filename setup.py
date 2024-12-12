from setuptools import setup, find_packages

setup(
    name="mcard-core",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    author="Ben Koo",
    author_email="koo0905@gmail.com",
    description="A content-addressable data wrapper library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/benkoo/mcard-core",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
