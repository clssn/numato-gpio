ChangeLog
=========

This project is semantically versioned according to
[SemVer](http://www.semver.org).

Release 0.6.0 (Unreleased)
--------------------------

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
