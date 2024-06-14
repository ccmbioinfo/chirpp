from setuptools import setup, find_packages

setup(
    name='chirpp_report_gen',
    version='0.1.0',
    description="Python package for generating excel reports for CHIRPP",
    author='Alper Celik',
    author_email='alper.celik@sickkids.ca',
    packages=find_packages(),
    install_requires=["pandas", "spacy", "medspacy", "spacy_transformers", "transformers", "pytorch",
                      "sentence-transformers", "Levenshtein"],
    zip_safe=False,
    scripts=["chirpp/generate_report.py", "chirpp/process_epic_dump.py"],
    include_package_data=True
)