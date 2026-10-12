#!/usr/bin/env python
""" Main BlueSky start script """
import sys

# This repo's own directory path contains a non-ASCII character (Vietnamese), which the Windows
# console/locale default codepage (cp1252) can't encode. That breaks any print() of a path
# derived from this repo (e.g. scenario/cache file paths) unless stdout/stderr are explicitly
# UTF-8. Reconfiguring here (before any other import can print anything) makes that safe
# regardless of how this script is launched (WebATM's auto-start subprocess already also sets
# PYTHONIOENCODING/PYTHONUTF8 env vars, but this covers direct/manual launches too).
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from bluesky.__main__ import main


if __name__ == "__main__":
    # Run mainloop if BlueSky is called directly
    sys.exit(main())
