from setuptools import setup, find_packages

setup(
    name="mediacompressor",
    version="1.0.1",
    description="Cross-Platform Python Desktop Video & Image Compression Utility",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Aniket Verma",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "Pillow>=10.0.0",
        "imageio-ffmpeg>=0.4.9"
    ],
    entry_points={
        "console_scripts": [
            "mediacompressor=mediacompressor.cli:main",
            "media-compressor=mediacompressor.cli:main"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
