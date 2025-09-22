from setuptools import setup, find_packages

setup(
    name='chirpp',
    version='0.1.0',
    description="Python package for generating excel reports for CHIRPP",
    author='Alper Celik',
    author_email='alper.celik@sickkids.ca',
    packages=find_packages(),
    install_requires=["pandas", "spacy", "medspacy", "spacy_transformers", "transformers", "torch", "tokenizers"
                      "sentence-transformers", "Levenshtein"],
    zip_safe=False,
    scripts=["chirpp/generate_report.py"],
    include_package_data=True
)