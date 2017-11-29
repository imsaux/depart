import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["serial", "PyQt5"], "excludes": []}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "ATP",
        version = "0.5a",
        description = "Automated Testing Platform",
        options = {"build_exe": build_exe_options},
        executables = [Executable("start.py", base=base)])