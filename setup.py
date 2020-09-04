import setuptools
import glob
import os.path

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="obs4mips",
    include_package_data=True,
    version="2.0.0",
    author="Obs4MIPs Task Team",
    author_email="obs4mips-admin@llnl.gov",
    description="JSON Tables for CMOR3 to create obs4MIPs datasets.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PCMDI/obs4MIPs-cmor-tables",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    data_files=[('obs4mips_tables', glob.glob(os.path.join('Tables', '*json')))]
)
