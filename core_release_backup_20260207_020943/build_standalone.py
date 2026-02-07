#!/usr/bin/env python3
"""
Bundled copy of build_standalone.py (modified) for Release/core_release.
This is a shallow copy used as the 'obfuscated' runtime stub in the release.
"""

# NOTE: This is a copy of the generator used in development. For full
# obfuscation use the project's obfuscation toolchain. This copy is intended
# to let the obfuscated runner call into a stable generator for tests.

from pathlib import Path
import sys
import os
# The real file is available in the repository; this copy is only for the
# release layout. If you need to update it, edit build/build_standalone.py
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
from build.build_standalone import main

if __name__ == '__main__':
    main()
