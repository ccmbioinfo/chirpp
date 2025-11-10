from setuptools import setup, find_packages

setup(
    name='chirpp',
    version='0.1.0',
    description="Python package for generating excel reports for CHIRPP",
    author='Alper Celik',
    author_email='alper.celik@sickkids.ca',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True
)
