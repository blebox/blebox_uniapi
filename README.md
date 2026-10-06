# BleBox Python UniAPI

[![PyPI](https://img.shields.io/pypi/v/blebox_uniapi.svg)](https://pypi.python.org/pypi/blebox_uniapi)

Python API for accessing BleBox smart home devices

* Free software: Apache Software License 2.0
* Documentation: https://blebox-uniapi.readthedocs.io.

## Features

* supports [11 BleBox smart home devices]
* contains functional/integration tests
* every device supports at least minimum functionality for most common automation needs
* insight of integration level are accesible from file [box_types.py](blebox_uniapi/box_types.py#L43)

  (devices with apiLevel lower than defined in BOX_TYPE_CONF will not be supported but higher will)

Contributions are welcome!

## Credits

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[audreyr/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
[11 BleBox smart home devices]: https://blebox.eu/produkty/?lang=en
