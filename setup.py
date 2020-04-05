"""Setup specification for the numato-gpio package."""
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="numato-gpio",
    version="0.3.1",
    author="Henning Classen",
    author_email="code@clssn.de",
    description="Python API for Numato GPIO Expanders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clssn/numato-gpio",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    install_requires=["pyserial==3.1.1"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.4",
)
