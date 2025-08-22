from PyInstaller.utils.hooks import collect_data_files

# This collects all the Playwright data files, including the browser binaries
datas = collect_data_files('playwright', include_py_files=True)