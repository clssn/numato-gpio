Change Log
==========

This project is semantically versioned according to
[SemVer](http://www.semver.org) with one exception: Until the first major
release, breaking changes will increment the minor version only. This is likely
to happen quite often until things have settled down and a certain degree of
maturity is established.

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
