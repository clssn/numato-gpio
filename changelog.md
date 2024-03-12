Change Log
==========

This project is semantically versioned according to
[SemVer](http://www.semver.org) with one exception: Until the first major
release, breaking changes will increment the minor version only. This is likely
to happen quite often until things have settled down and a certain degree of
maturity is established.

Release 0.13.0
--------------

This release is going to make many variants of the Numato devices compatible.

Those variants' major differences are in the end-of-line sequences of responses
to queries and notificastions. Worse, in some cases they are not even uniform
across responses and notifications of a single device variant. Consequently,
this version now completely discards all end-of-line characters while reading
which also simplifies the reading code a lot. Discarding is possible as all
device resonses are either known by their length or are terminated by the
`>` prompt character.

Breaking change:

Using the notification API on a board that doesn't support notifications (8
port boards don't) will now raise a NumatoGpioException instead of returning
False.

Release 0.12.0
--------------

In this release the numato board's version string is read as a string and not
expected to be of integer type anymore. This should resolve most of the reported
issues.

Release 0.11.1
--------------

Dependency version upgrade, initiated by dependabot due to a security issue.

Release 0.11.0
--------------

This release changes the project to poetry/pyproject.toml based. Poetry manages
dependencies, resolves them to a lockfile and maintains the resolved versions in
a virtualenv. Poetry can also be used to package and upload releases to PyPi.

Release 0.10.0
--------------

This release finally adds support for all Numato USB GPIO devices. A device
mockup has been created whose behavior was derived from Numato documentation
and the analysis of user's Issues. In practice there may be additional
properties of devices which haven't been taken into account.

- Support 8, 16, 32, 64 and 128 port devices
- Add unit tests covering all ports and eol-sequences including notifications
- Fix notifications which in certain cases would remain undetected
- Improve unit test coverage to >80%
- Improve the Makefile to create a virtualenv for development and testing

Release 0.9.0
-------------

This release extends the support to devices with different end-of-line responses.

- Support end-of-line responses cr, lf and lfcr in addition to crlf
- New troubleshooting document to streamline support requests
- Minor bug fixes

Release 0.8.1
-------------

This release adds a github workflow to deploy release packages on PyPI.

Release 0.8.0
-------------

This version is released to relax the pyserial dependency in order to avoid
problems in the home-assistant project when the new pip resolver is in effect.
Additional features:

- Add a very basic unit-test against a pyserial mockup
- Configure tox to run the tests in a virtualenv
- Document CLI usage and improve CLI output

Release 0.7.1
-------------

This release fixes an error in the cleanup implementation. When a device can't
be properly cleaned  (e.g. because it's disconnected), its exception was not
handled, but fell through to the caller. So remaining devices could not be
cleaned up anymore.

- Fix crash during cleanup in case of a Serial communication failure

Release 0.7.0
-------------

While this release is a thorough refactoring of most parts of the code, the
number of breaking changes has been kept to a minimum.

The following breaking change was made: Accessor functions in the NumatoUsbGpio
class namely id(), ver(), notify(), iomask() and iodir() are turned into
properties. Calls to these functions need to be changed to:

```python
device_version = dev.id  # read access
dev.id = 5  # write access, permanent change of the device ID

dev.notify = True  # turn on notifications
notifications = dev.notify  # read whether notifications are enabled or not
```

- Change accessor functions into properties (breaking change)
- Refactor out duplicated code
- Validate expected device responses instead of discarding read bytes
- Re-order methods by level of abstraction
- Add `clean` target to makefile, cleaning up package data from releases
- Add system tests for limited API tests against a connected real device

Release 0.6.0
-------------

18 April 2020

This release improves stability of the system by discovering devices from a
user defined list of device files. Instead of opening a whole generic range of
devices, the user can now select which ones to use. The default is still
/dev/ttyACM0 to /dev/ttyACM9 if no list is passed to the discover method.

- Support discovery from selected device files

Release 0.5.0
-------------

16 April 2020

This release removes the constraint to firmware version 9 of the Numato device.
Now all devices with the same command set and word-length might be supported.
Otherwise an error with a speaking message is raised.

- Check response of some commands during discovery/construction
- Remove strict check for firmware version 9

Release 0.4.0
-------------

11 April 2020

This release is about refactoring and refinement of locking for thread safety
and error handling. It has no breaking changes.

- Lock discovery method, so no separate thread could interfere doing the same
- Lock low level _write method to protect its direct use in the constructor
- Refactor towards more pythonic code

Release 0.3.1
-------------

5 April 2020

This version is about learning that a deleted PyPI package can not be
re-uploaded at all. Hence a bugfix release.

Release 0.3.0 (deleted on PyPI)
-------------

5 April 2020

This version mainly improves stability and code formatting.

- Improve thread synchronization
- Improve error handling
- Initialize device more properly
- Format code with yapf
