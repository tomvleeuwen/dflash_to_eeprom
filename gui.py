#!/usr/bin/env python2
import sys
from dflash_to_eee import DFlashConverter
import Tkinter, tkFileDialog, tkMessageBox


def main():
    converter = DFlashConverter()
    
    root = Tkinter.Tk()
    root.withdraw()

    source_path = tkFileDialog.askopenfilename()
    try:
        converter._read_file(source_path)
    except Exception as error:
        tkMessageBox.showerror(title="Error reading file", message=str(error))
        return -1
    
    try:
        converter._find_endblock()
    except Exception as error:
        tkMessageBox.showerror(title="Error converting file", message=str(error))
        return -1
    
    dest_path = tkFileDialog.asksaveasfilename()
    try:
        converter._save_file(dest_path)
    except Exception as error:
        tkMessageBox.showerror(title="Error saving file", message=str(error))
        return -1

    tkMessageBox.showinfo(title="Conversion complete", message=converter._get_info())

if __name__ == "__main__":
    sys.exit(main())
