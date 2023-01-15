# -*- coding: utf-8 -*-
"""
===============================================================================

   GeodataFlow:
   Geoprocessing framework for geographical & Earth Observation (EO) data.

   Copyright (c) 2022-2023, Alvaro Huarte. All rights reserved.

   Redistribution and use of this code in source and binary forms, with
   or without modification, are permitted provided that the following
   conditions are met:
   * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   * Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
   TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
   OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SAMPLE CODE, EVEN IF
   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

===============================================================================
"""

import os
from setuptools import setup

BASEDIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))


# Metadata of GeodataFlow.
metadata = {}
with open(os.path.join(BASEDIR, 'geodataflow/dataframes/__meta__.py'), 'r') as fp:
    exec(fp.read(), metadata)

with open(os.path.join(BASEDIR, 'README.md'), 'r') as fp:
    readme = fp.read()

with open(os.path.join(BASEDIR, 'requirements.txt'), 'r') as fp:
    all_reqs = fp.readlines()

install_requires = [x.strip()
                    for x in all_reqs if 'git+' not in x and '--' not in x and not x.startswith('#')]
dependency_links = [x.strip().replace('git+', '')
                    for x in all_reqs if 'git+' not in x and '--' not in x and not x.startswith('#')]

# Setup for GeodataFlow.
setup(
    name=metadata['__name__'],
    version=metadata['__version__'],
    description=metadata['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=metadata['__author__'],
    author_email=metadata['__email__'],
    url=metadata['__url__'],
    license=metadata['__license__'],
    packages=[
        'geodataflow', 'geodataflow.dataframes'
    ],
    package_data={
        'geodataflow': ['pipelineapp.default.settings', 'pipelineapi.default.settings'],
        'geodataflow.dataframes': ['modules/**/*.py']
    },
    install_requires=install_requires,
    dependency_links=dependency_links,
    python_requires='>=3.7',
    extras_require={
        'eodag': ['eodag>=2.4.0'],
        'gee': ['earthengine-api==0.1.320']
    },
    entry_points={
    },
    project_urls={
        'Bug Tracker': 'https://github.com/ahuarte47/geodataflow/issues/',
        'Source Code': 'https://github.com/ahuarte47/geodataflow'
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Image Processing',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
