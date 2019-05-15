# pygbasm
GameBoy assembler/linker in Python

This is an experimental project that will compile LR35902 (Z80-ish)
assembly and create an executable that is compatible with a Game Boy (DMG)
ROM that can, in turn, be run by on-line emulators such as
https://gameplaycolor.com.

This compiler is designed so that hobbyists can create/test/play their own
DMG and Game Boy Color games.

One of the goals of this project is to be able to build and run a game from
an iPad using [Pythonista](http://omz-software.com/pythonista/)

At this point, this code is very incomplete and not even usable. It also
represents my first Python project. Proceed with caution.

If you want to play and test it you can refer to the
gbasm/tests/unit_tests.py to get an idea of how to use the various
objects. Unit tests are being built out and consist of a bunch of Label
tests.

Many of the python files have a __main__ that runs a simple smoke-test of
the object(s) in the file. For example, the instruction/instruction.py file
has several allocate/print statements, some of them negative.
