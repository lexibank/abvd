from setuptools import setup
import json

with open('metadata.json', 'r', encoding='utf-8') as fp:
    metadata = json.load(fp)


setup(
    name='lexibank_abvd',
    description=metadata['title'],
    license=metadata['license'],
    url=metadata['url'],
    py_modules=['lexibank_abvd'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lexibank.dataset': [
            'abvd=lexibank_abvd:Dataset',
        ]
    },
    install_requires=[
        'pylexibank>=2.1',
    ]
)
