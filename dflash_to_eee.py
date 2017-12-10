#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Copyright 2017, Ben van Leeuwen Autotechniek, https://www.benvanleeuwen.com/
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

######################################################################### 
#                                                                       #
#  DOCUMENTATION                                                        #
#                                                                       #
# The "FRM3" and other Electronic Control Units contain the             #
# MC9S12XEQ384 microprocessor with integrated Flash. When the           #
# integrated Flash is used in eeprom emulation mode, like in the case   #
# of the FRM3, the settings can get corrupted making the ECU unable to  #
# access the eeprom again. The ECU can be repaired by programming the   #
# correct data in the (simulated) eeprom.                               #
#                                                                       #
# This tool allows the corrupt data in the microprocessor to be read,   #
# even after the eeprom got corrupted. This is done by reading the      #
# d-flash contents from the microcontroller using an appropriate        #
# programmer (like xprog), after which this program can convert it to   #
# an eeprom image which can then be programmed to the simulated eeprom  #
# area again using the same programmer.                                 #
#
# This script runs under the following assumptions: The Flash is used   #
# as a circular buffer, where each flash block can contain zero to 63   #
# "eeprom commands", which "update" the data in the simulated  eeprom.  #
# It is assumed that an eeprom word starts as 0xFF, and can be written  #
# by adding a command to the flash. It can be overwritten by adding     #
# another command to the flash (The flash cannot be erased at word-     #
# level, and the block can still contain valid commands for a different #
# address, so it has to keep the old command). Thus, the order of       #
# commands matter. It is assumed that a block that has its header set   #
# to FFFFFFFE is  prepared to become the next block to be written to.   #
# It is also assumed that a block that is not completely filled with    #
# commands is the current block, which shall be located just before the #
# prepared block. If none of these conditions are found, it just        #
# searches for the longest chain of empty blocks (header starts with    #
# 0xFFFF and not 0xFACF), and assumes that these are the prepared       #
# blocks.                                                               #
#                                                                       #
# This is all just based on looking to a D-flash dump, so there might   #
# be more magic. However, the resuling eeprom file looks reasonable,    #
# and it worked in all cases where this tool did not report an error.   #
#                                                                       #
#########################################################################

import sys
import struct
import logging
from copy import copy


class DFlashConverter(object):
    NB_BLOCKS  = 128 # Number of flash erase blocks
    BLOCKSIZE  = 256 # Number of bytes in one flash block
    HEADERSIZE = 4   # Size of block header.
    CMDSIZE    = 4   # Number of bytes occupied by one eeprom update

    EESIZE = 2048   # Number of 2-byte words in the simulated eeprom

    BLOCK_VALID = 0xFACF
    BLOCK_EMPTY = 0xFFFF
    BLOCK_EMPTY_CLEARED = 0xFFFF
    CMD_MASK   = 0xF800
    CMD_VALID  = 0xB800
    CMD_EMPTY  = 0xF800
    
    VALID   = "VALID"
    LAST    = "LAST"
    EMPTY   = "EMPTY"
    NEW     = "NEW"
    INVALID = "INVALID"
    
    
    def __init__(self):
        """ DFlashConverter:
            This object contains all the magic to convert the D-Flash to Eeprom image.
        """
        self.block_types = []
        self.block_data = []
        self.endblock = None
        self.corrupt = None
        
        self.cmds_per_block = (self.BLOCKSIZE - self.HEADERSIZE) / self.CMDSIZE
        
    def _read_file(self, filename):
        """ Reads the d-flash file and stores the data in convenient lists
            of block types and block commands
        """
        self.corrupt = False
        with open(filename, 'rb') as infile:
            self.block_data = [ [] for _ in xrange(self.NB_BLOCKS)]
            for blockid in xrange(self.NB_BLOCKS):
                
                infile.seek(blockid * self.BLOCKSIZE)
                blockheader = infile.read(self.HEADERSIZE)
                if len(blockheader) != 4:
                    raise Exception("Input file too short")
                header = struct.unpack(">HH", blockheader)
                if header[0] == self.BLOCK_EMPTY:
                    if header[1] == self.BLOCK_EMPTY_CLEARED:
                        self.block_types.append(self.EMPTY)
                    else: # Block has already been prepared.
                        self.block_types.append(self.NEW)
                elif header[0] == self.BLOCK_VALID:
                    # There seem to be different type of data blocks defined in header[1],
                    # however I have currently no idea how to handle it.
                    logging.debug("Data block id: %d, type: 0x%04X" % (blockid, header[1]))
                    self.block_types.append(self.VALID)
                    for blockitem in xrange(self.cmds_per_block):
                        cmdread = infile.read(self.CMDSIZE)
                        if len(cmdread) != 4:
                            raise Exception("Input file too short")
                        datapair = struct.unpack(">HH", cmdread)
                        
                        cmd  = datapair[0] & self.CMD_MASK
                        addr = datapair[0] & ~self.CMD_MASK
                        data = datapair[1]
                        
                        if cmd == self.CMD_VALID:
                            self.block_data[blockid].append((addr, data))
                        elif cmd == self.CMD_EMPTY:
                            self.block_types[-1] = self.LAST
                        else:
                            logging.error("Unknown CMD type detected: 0x%02X" % cmd)
                            self.corrupt = True
                else:
                    logging.error("Unknown block type: 0x%04X" % header[0])
                    self.corrupt = True
                    self.block_types.append(self.INVALID)
    
    def _find_new_blocks(self):
        """ Finds the "new" blocks and checks that they are all consequtive. 
            Returns the last block before the "new" blocks since it can be
            used as "endblock" """
        block_types = copy(self.block_types)
        
        # Append the new blocks at the start to the end of the list, so
        # we can easily loop through it without accounting for the
        # start - end split
        curr_block = 0
        while block_types[curr_block] == self.NEW or block_types[curr_block] == self.EMPTY:
            block_types.append(block_types[curr_block])
            curr_block += 1
            if curr_block > self.NB_BLOCKS:
                raise Exception("All blocks seem to be new blocks")
        
        newblock = None
        ended = False
        
        for curr_block in xrange(curr_block, len(block_types)):
            if block_types[curr_block] == self.NEW:
                if newblock is None:
                    newblock = curr_block
                elif ended:
                    logging.warning("Found more than one set of new blocks!")
                    return None
            elif block_types[curr_block] != self.EMPTY and newblock is not None:
                ended = True
        # Return the "endblock", which is the block just before the first newblock
        if newblock is None:
            logging.warning("No new blocks found!")
            return None
        return (newblock - 1) % self.NB_BLOCKS
        
    def _find_last_block(self):
        """ Finds the last block, e.g. the block that is valid but is not
            (completely) filled with data. Can be used as "endblock" """
        # If there is exactly one "Last" block, simply return it.
        if self.block_types.count(self.LAST) == 1:
            return self.block_types.index(self.LAST)
        if self.block_types.count(self.LAST) == 0:
            logging.warning("No last block found!")
            return None
        logging.warning("More than one 'last' block found!")
        return None
    
    def _find_longest_empty(self):
        """ Finds the longest chain of empty block and returns the 
            block just before that as lastblock, as a fallback mechanism.
            Returns the last block of the chain in case no empty block could
            be found. """
        # It's still possible that there are "NEW" blocks that are not consequtive
        # Therefore, just find the longest chain of "NEW" and "EMPTY" blocks.
        now = 0
        longest = 0
        longest_block = None
        # We are lazy. Just concatenate blocks to itself so if the longest
        # chain of zero blocks covers the end and start we still see it.
        for blockid, block in enumerate(self.block_types+self.block_types):
            if block == self.EMPTY or block == self.NEW:
                now += 1
            else:
                now = 0
            
            if now > longest:
                longest = now
                longest_block = blockid
        if longest_block is None:
            return self.NB_BLOCKS - 1
        return (longest_block - longest) % self.NB_BLOCKS
        
    def _save_file(self, filename):
        """ Given that all the block data and endblock are known, start
            building the eeprom image and save it to a file and to a
            local array for analysis 
        """
        startblock = (self.endblock + 1) % self.NB_BLOCKS

        data = [0xFFFF] * self.EESIZE
        for block in range(startblock, self.NB_BLOCKS) + range(0, startblock):
            for item in self.block_data[block]:
                data[item[0]] = item[1]

        # We have collected the data. Now simply output it to a file.
        with open(filename, 'wb') as outfile:
            for word in data:
                outfile.write(struct.pack(">H", word))
                
        self.data = data

    def _get_byte(self, addr):
        """ Get a single byte from the 16-bit eeprom data array, 
            after it has been created by _save_file
        """
        if addr % 2 == 1:
            return self.data[addr//2] & 0xFF
        return self.data[addr//2] >> 8

    def _get_info(self):
        """ Show info about the re-build image. Currently it only shows the
            VIN number
        """
        result = "\n\n"
        
        if self.corrupt:
            result += "Corrupt D-Flash file detected! Results probably incorrect!\n"
        
        # VIN
        vin = ""
        for addr in xrange(0xFD3, 0xFE4):
            vin = vin + chr(self._get_byte(addr))
        result += "VIN: %s\n" % vin
        
        # Mfg. date
        day = "%02x" % self._get_byte(0xFBE)
        month = "%02x" % self._get_byte(0xFBD)
        year = "%02x" % self._get_byte(0xFBB) + "%02x" % self._get_byte(0xFBC)
        result += "Production date: %s.%s.%s\n" % (day, month, year)
        
        # Original programming date - always equal to production date...
        # day = "%02x" % self._get_byte(0xFA0)
        # month = "%02x" % self._get_byte(0xF9F)
        # year = "%02x" % self._get_byte(0xF9D) + "%02x" % self._get_byte(0xF9E)
        # result += "MIF. date: %s.%s.%s\n" % (day, month, year)
        
        # Prog. date
        day = "%02x" % self._get_byte(0xF89)
        month = "%02x" % self._get_byte(0xF88)
        year = "%02x" % self._get_byte(0xF86) + "%02x" % self._get_byte(0xF87)
        result += "Programming date: %s.%s.%s\n" % (day, month, year)
        
        # Mfg. part no
        data = 0
        for byte in xrange(6):
            data = (data << 8) + self._get_byte(0xF97 + byte)
        result += "HW-NR: %07x (Hardware part number)\n" % data
        
        # MIF part no
        data = 0
        for byte in xrange(6):
            data = (data << 8) + self._get_byte(0xF8A + byte)
        result += "SW-NR: %07x (Updated part number)\n" % data
        
        # MIF part no
        data = 0
        for byte in xrange(6):
            data = (data << 8) + self._get_byte(0xF65 + byte)
        result += "ZB-NR: %07x (Original part number)\n" % data
        
        # Sticker part no?
        data = 0
        for byte in xrange(6):
            data = (data << 8) + self._get_byte(0xFBF + byte)
        result += "S:     %07x (Original part number)\n" % data
        
        return result
        
    
    def convert(self, dflash_filename, ee_filename):
        """ Main function that converts dflash_filename to ee_filename
            and shows some info afterwards
        """
        self._read_file(dflash_filename)
        self._find_endblock()
        self._save_file(ee_filename)
        logging.info(self._get_info())
    
    def _find_endblock(self):
        endblock_new = self._find_new_blocks()
        endblock_last = self._find_last_block()
        
        if endblock_new is None:
            if endblock_last is None:
                logging.warning("No last or new blocks, using longest chain of empty blocks!")
                self.endblock = self._find_longest_empty()
            else:
                self.endblock = endblock_last
        else:
            # This whole if-statement is just here to generate the warning message.
            if endblock_last != endblock_new and endblock_last is not None:
                # It is allowed to have empty blocks between the last used and the new block.
                # Make sure we have a contineous set of blocks by appending the list to itself.
                block_types = self.block_types + self.block_types
                endblock_new_wrapped = endblock_new
                if endblock_new_wrapped < endblock_last:
                    endblock_new_wrapped += len(self.block_types)
                if block_types[endblock_last+1:endblock_new_wrapped+1].count(self.EMPTY) != \
                                                    endblock_new_wrapped - endblock_last:
                    logging.warning("Inconsistency detected, last used block not followed by new blocks!")
                    logging.warning("Using new blocks as reference!")
            self.endblock = endblock_new
        

def main():
    """ No options, just call with dflash_filename and ee_filename..."""
    
    logging.getLogger().setLevel(logging.INFO)
    
    if len(sys.argv) != 3:
        print "Usage: %s <dflash> <eeprom>" % sys.argv[0]
        sys.exit(1)
    
    converter = DFlashConverter()
    converter.convert(sys.argv[1], sys.argv[2])
        
if __name__ == "__main__":
    main()
