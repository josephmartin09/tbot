from setuptools import find_packages, setup

import tbot.__version__ as __version__

setup(
    name="tbot",
    version=__version__,
    description="Library for technical analysis of financial data for use in trading and investment.",
    author="Joseph Maritn",
    packages=find_packages(),
)
