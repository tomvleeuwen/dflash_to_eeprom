@echo off
REM Simply call pyinstaller and rename the output file
C:\Python27\Scripts\pyinstaller.exe gui.py --onefile
move dist\gui.exe dflash_to_eee.exe
rmdir dist
