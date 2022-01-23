=======
History
=======

1.4.0 (2022-01-23)
------------------

* handle temporary error retrying HTTP request

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
