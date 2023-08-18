====================
BleBox Python UniAPI
====================


.. image:: https://img.shields.io/pypi/v/blebox_uniapi.svg
        :target: https://pypi.python.org/pypi/blebox_uniapi

.. image:: https://travis-ci.com/blebox/blebox_uniapi.svg?branch=master
        :target: https://travis-ci.com/blebox/blebox_uniapi

.. image:: https://readthedocs.org/projects/blebox-uniapi/badge/?version=latest
        :target: https://blebox-uniapi.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Python API for accessing BleBox smart home devices


* Free software: Apache Software License 2.0
* Documentation: https://blebox-uniapi.readthedocs.io.


Features
--------

* supports `11 BleBox smart home devices`_
* contains functional/integration tests
* every device supports at least minimum functionality for most common automation needs
* insight of integration level are accesible from file `box_types.py <blebox_uniapi/box_types.py#L43>`_  
  
  (devices with apiLevel lower than defined in BOX_TYPE_CONF will not be supported but higher will)  
  

Contributions are most welcome!

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`11 BleBox smart home devices`: https://blebox.eu/produkty/?lang=en
