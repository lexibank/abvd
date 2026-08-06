from setuptools import setup, find_packages
import json

with open('metadata.json', 'r', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_abvd',
    description=metadata['title'],
    license=metadata['license'],
    url=metadata['url'],
    py_modules=['lexibank_abvd'],
    packages=find_packages(where='.'),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'abvd=lexibank_abvd:Dataset',
        ],
        'cldfbench.commands': [
            'abvd=abvd_commands',
        ],
    },
    install_requires=[
        'pylexibank>=4.1',
        'cldfviz[cartopy]',
    ]
)
