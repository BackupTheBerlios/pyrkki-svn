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


import curses
import os
import sys

from IRC import *

class CursesGui:
    def __init__(self):

        # number if active connection
        self.con_num=0
        self.connections = list()
        
        # init the screen
        self.scr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.scr.keypad(1)

        # init the first window as status window
        y,x = self.scr.getmaxyx()
        self.statuswin = curses.newwin(1,x,y-2,0)
        self.statuswin.addstr(0,0,"[NOT CONNECTED]")

        # staus win 2 who@where
        statuswin2W = 10
        self.statuswin2 = curses.newwin(1,statuswin2W,y-1,0)
        self.statuswin2.addstr(0,0,"NICK")

        # type win
        self.typewin = curses.newwin(1,x-statuswin2W-1,y-1,statuswin2W-1)
        self.typewin.keypad(1)

        # message win
        self.messagewin = curses.newwin(y-2,x,0,0)

        # list of our window (channel)
        self.mwindows = list()
        self.active_mwindow = 0

        # refresh the windows
        self.messagewin.refresh()
        self.statuswin.refresh()
        self.statuswin2.refresh()
        self.typewin.refresh()        

    def update_status(self):
        # update the status bar
        self.statuswin.clear()
        chan = self.mwindows[self.active_mwindow]
        self.statuswin.addstr(0,0,'['+self.connections[self.con_num].name+'] '+chan.name+' '+str(self.mwindows.index(chan)))

    # draw the window again
    def update_window(self):
        channel = self.mwindows[self.active_mwindow]
        self.draw_lines_to_message_win(channel)

        self.update_status()
        # refresh the windows
        self.messagewin.refresh()
        self.statuswin.refresh()
        self.statuswin2.refresh()
        self.typewin.refresh()        

    def update_window2(self,channel,network,command):
        if command == 'NEWWINDOW':
            self.mwindows.append(channel)
            self.active_mwindow = len(self.mwindows)-1
        elif command == 'REMOVEWINDOW':
            self.active_mwindow = 0
            self.mwindows.remove(channel)
            self.update_window() 
        if self.mwindows[self.active_mwindow] == channel:
            for chanwin in self.mwindows:
                if chanwin.name == channel.name:
                    self.draw_lines_to_message_win(channel)
        self.update_status()
        # refresh the windows
        self.messagewin.refresh()
        self.statuswin.refresh()
        self.statuswin2.refresh()
        self.typewin.refresh()        

    def draw_lines_to_message_win(self,channel):
        # first clear the window
        self.messagewin.clear()
        lines = channel.lines
        mwy,mwx = self.messagewin.getmaxyx()
        currentline = 0
        lines.reverse()
        # get the lines for lines
        splittedlines = list()
        for line in lines:
            pituus = len(line.sender)+3
            pituus2 = mwx -1 -pituus
            x = 0
            templines = list()
            while x < len(line.text):
                #sline = '<'+line.sender+'> ' +line.text[x:mwx-1 -pituus]
                sline = '<'+line.sender+'> ' +line.text[x:pituus2 +x]
                x = x + mwx -1 - pituus
                templines.append(sline)
            templines.reverse()
            for tline in templines:
                splittedlines.append(tline)
        numlines = len(splittedlines)
        # put the splitted lines to screen
        for line in splittedlines:
            if currentline < mwy:
                self.messagewin.addstr(mwy - currentline -1, 0,line)
                currentline = currentline + 1
            else:
                break
        lines.reverse()

            
    # here is the main function with the main loop etc.
    def start(self):
        self.connections.append(IRCConnection('TESTI','192.168.1.2',6667,'pzq2','asd2dasv','dyksi',self.update_window2))
        xasd = self.connections[self.con_num]
        xasd.connect()
        self.mwindows.append(xasd.messages)
        pirssion = 1
        # lets take some key input this just a quick method. Remember to fix later
        while pirssion == 1:
            inputstring = ''
            enterpushed = 0
            while enterpushed == 0:
                self.typewin.refresh()
                inputchar = self.typewin.getch(0,len(inputstring)+1)
                if inputchar < 255:
                    if inputchar == 10: # enter
                        enterpushed = 1
                    elif inputchar == 127:
                        inputstring = inputstring[:-1]
                        self.typewin.delch(0,len(inputstring)+1)
                    else:
                        for chmark in list(' 1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖabcdefghijklmnopqrstuvwxyzåäö!"#¤%&/()=?¡@£$~¥{[]}\~<>,.-*^:;'):
                            if inputchar == ord(chmark):
                                inputstring += chmark
                                self.typewin.addch(0,len(inputstring),ord(chmark))
                                break
                elif inputchar == 263: # backspace
                    inputstring = inputstring[:-1]
                    self.typewin.delch(0,len(inputstring)+1)
                elif inputchar == 260:
                    if self.active_mwindow > 0:
                        self.active_mwindow = self.active_mwindow -1
                        self.update_window()
                elif inputchar == 261:
                    if len(self.mwindows)-1 > self.active_mwindow:
                        self.active_mwindow = self.active_mwindow +1
                        self.update_window()
                
                self.typewin.refresh()

            #put our message to channel or status screen
            self.putmessagetoscreen(inputstring)
            
            self.update_window()

            channel = self.mwindows[self.active_mwindow].name

            if channel == 'STATUS':
                channel = ''
            self.connections[self.con_num].message(inputstring,channel)
            self.typewin.erase()
            

        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def putmessagetoscreen(self,inputstring):

        chan = self.mwindows[self.active_mwindow]
        nick = self.connections[self.con_num].nick
    
        chan.add_line(IRCMessage(str(nick),'itse',inputstring))
        # chan.add_line(IRCMessage(str(nick),'itse',str(chan.users))) users
        self.update_window()
