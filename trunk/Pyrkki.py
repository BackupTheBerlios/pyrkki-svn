#!/usr/bin/python

# Copyright (C) 2005
# Petteri Klemola <petteri dot medusa dot tutka dot fi>
#
# This file is part of Pyrkki.
#
# Pyrkki is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#  
# Pyrkki is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with Pyrkki; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from CursesGUI import *
from sys import argv, stdout

if __name__=='__main__':
    print " Pyrkki: Venomous Chat Client"
    print " Not released yet, DO NOT USE: Contains FATAL BUGS"
    print " Copyright (C) 2005"
    print " Petteri Klemola"

    if len(argv) < 2:
        print " Usage:"
        print " No parameters yet just use"
        print " Pyrkki GO"
        print " and modify CursesGUI.py to suit your needs (for server and nick)"
    else:
        # this is the first version so only curses gui awailable
        gui = CursesGui()
        
        gui.start()
        




