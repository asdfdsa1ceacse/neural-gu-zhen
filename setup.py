from setuptools import setup, find_packages
import dna_memory

setup(
    name="dna-memory",
    version=dna_memory.__version__,
    description="多链 DNA 记忆匹配引擎 — Multi-Strand DNA Memory Matching Engine",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Yiming Zhong",
    author_email="",
    url="https://github.com/asdfdsa1ceacse/dna-memory",
    packages=find_packages(),
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
