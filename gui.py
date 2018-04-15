#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2017-2018, Ben van Leeuwen Autotechniek, https://www.benvanleeuwen.com/
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the 
#    distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import sys
from dflash_to_eee import DFlashConverter
import Tkinter, tkFileDialog, tkMessageBox

USER_NOTES = """
NOTE: Ensure you write to EEE partition and not back to D-Flash!

NOTE: Always verify after writing the image to the device!"""


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

    tkMessageBox.showwarning(title="Warning", message=USER_NOTES)

if __name__ == "__main__":
    sys.exit(main())
