from setuptools import setup, find_packages

setup(
    name="icepi",
    version="0.1",
    zip_safe=False,
    packages=find_packages(),
    install_requires=["tornado", "ctypes"]
)
