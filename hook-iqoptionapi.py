# hook-iqoptionapi.py
from PyInstaller.utils.hooks import collect_all

# Tell PyInstaller to collect everything from the iqoptionapi package
datas, binaries, hiddenimports = collect_all('iqoptionapi')
