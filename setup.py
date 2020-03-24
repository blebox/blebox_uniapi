#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['aiohttp>=3','semver>=2.9.1']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', 'asynctest>=0.13', 'semver', 'deepmerge']

setup(
    author="Gadget Mobile",
    author_email='the_gadget_mobile@yahoo.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python API for accessing BleBox smart home devices",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='blebox_uniapi',
    name='blebox_uniapi',
    packages=find_packages(include=['blebox_uniapi', 'blebox_uniapi.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/gadgetmobile/blebox_uniapi',
    version='1.0.0',
    zip_safe=False,
)
