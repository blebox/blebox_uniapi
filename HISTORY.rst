=======
History
=======
2.2.0 (2023-08-29)
------------------
* added last_reset to energy sensor class
* added BasicAuth support to http client

2.1.4 (2023-01-03)
------------------
* added tilt position support for :code:`cover.Shutter`
* added :code:`Wind` for wind sensor of multisensors
* added :code:`Energy` sensor class for power consumption tracking
* implementing :code:`default_api_level` for
   * dimmerBox
   * wLightBox
   * wLightBoxS

2.1.3 (2022-10-27)
------------------
* thermoBox boost mode doesn't corrupt state

2.1.2 (2022-10-17)
------------------

* fixed CCT, CCTx2 modes for wLightBox v1 & v2

2.1.1 (2022-10-11)
------------------
* added support for thermoBox devices:
   * added thermoBox config to :code:`BOX_TYPE_CONFIG`
   * :code:`Climate` uses factory method implementation
   * added test coverage


2.1.0 (2022-08-05)
------------------
* added support for multiSensor API:
   * :code:`airQuality` moved to sensor module
   * new binary_sensor module, introducing :code:`Rain` class


2.0.2 (2022-07-06)
------------------
* added :code:`query_string` property in :code:`Button` class
* fixed test assertions after changes in error raised ValueError

2.0.1 (2022-06-01)
------------------
* used :code:`ValueError` type instead of :code:`BadOnValueError` in methods:

  * evaluate_brightness_from_rgb
  * apply_brightness
  * normalise_elements_of_rgb
  * _set_last_on_value
  * async_on

2.0.0 (2022-06-21)
------------------

* extended support for color modes in wLightBox devices
* initial support for tvLiftBox device
* major backward-incompatible architectural changes to enable dynamic configuration of devices
* removed products.py module and replaced with factory method on Box class
* general overhaul of public interfaces

1.3.3 (2021-05-12)
------------------

* fix support for wLightBoxS with wLightBox API
* fix state detection in gateBox

1.3.2 (2020-04-2)
------------------

* use proper module-level logger by default
* fix formatting

1.3.1 (2020-04-2)
------------------

* never skip command requests
* improve error messages

1.2.0 (2020-03-30)
------------------

* expose device info
* always add ip/port in connection errors
* fixed gateController support
* support for sauna min/max temp

1.1.0 (2020-03-24)
------------------

* fix bad wLightBox API path
* wrap api calls in semaphore (to serialize reqests to each box)
* throttle updates to 2/second (to avoid unnecessary requests)
* rework error handling and hierarchy (for cleaner usage)
* use actual device name (to help recognize the device)
* handle asyncio.TimeoutError (to handle timeout-related errors nicely)
* properly re-raise exceptions (to avoid lengthy call stacktraces)
* rename wLightBoxS feature to "brightness"

1.1.0 (2020-03-24)
------------------

* fix switchBox support
* fix minimum position handling
* drop Python 3.6 support (still may work)
* misc fixes, cleanup and increased test coverage

1.0.0 (2020-03-24)
------------------

* Fixed wLightBox issues
* Fixed wLightBoxS issues
* Fixed shutterBox issues
* Handle unknown shutterBox position
* Improved error handling + lots of new diagnostics
* Increased tests and test coverage (almost 100%)
* Lots of rework


0.1.1 (2020-03-15)
------------------

* Fixed switchBox support (newer API versions)

0.1.0 (2020-03-10)
------------------

* First release on PyPI.
