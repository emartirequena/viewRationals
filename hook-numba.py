from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

hiddenimports = collect_submodules('numba')
binaries = collect_dynamic_libs('llvmlite')
