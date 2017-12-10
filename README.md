# dflash_to_eeprom [![Build Status](https://travis-ci.org/tomvleeuwen/dflash_to_eeprom.svg?branch=master)](https://travis-ci.org/tomvleeuwen/dflash_to_eeprom)
Tool to fix corrupt MC9S12XEQ384 eeprom.

# Background
The "FRM3" and other Electronic Control Units contain the MC9S12XEQ384 microprocessor with integrated Flash. When the integrated Flash is used in eeprom emulation mode, like in the case of the FRM3, the settings can get corrupted making the ECU unable to  access the eeprom again. The ECU can be repaired by programming the correct data in the (simulated) eeprom.

# Usage
This tool allows the corrupt data in the microprocessor to be read, even after the eeprom got corrupted. This is done by reading the d-flash contents from the microcontroller using an appropriate programmer (like xprog), after which this program can convert it to an eeprom image which can then be programmed to the simulated eeprom area again using the same programmer.

# Internals
This tool runs under the following assumptions: The Flash is used as a circular buffer, where each flash block can contain zero to 63 "eeprom commands", which "update" the data in the simulated eeprom. It is assumed that an eeprom word starts as 0xFF, and can be written by adding a command to the flash. It can be overwritten by adding another command to the flash (The flash cannot be erased at word-level, and the block can still contain valid commands for a different address, so it has to keep the old command). Thus, the order of commands matter. It is assumed that a block that has its header set to FFFFFFFE is  prepared to become the next block to be written to.
It is also assumed that a block that is not completely filled with commands is the current block, which shall be located just before the prepared block. If none of these conditions are found, it just searches for the longest chain of empty blocks (header starts with 0xFFFF and not 0xFACF), and assumes that these are the prepared blocks.

# Magic
This is all just based on looking to D-flash dumps, so there might be more magic. However, so far in all cases where this tool did not detect any errors, the resulting image worked fine. When the D-Flash image is corrupt, this script will tell you so.

Note: This tool does not clear any error codes, short circuit counters, mileage or checksums. Therefore, in all cases you should clear the fault memory after the FRM3 is installed and in some cases it is wise to reset the short circuit counters.
