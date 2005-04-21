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
        self.irc = IRC()
        
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
        self.messagewin = curses.newwin(y-2,x-10,0,0) # nick lengt is 9 char should be done dynamically
        # so that windows size should depend on nick lenghts

        # nick win
        self.nickwin = curses.newwin(y-2,10,0,x-10) # should also be dynamic
        
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
        self.statuswin.addstr(0,0,'['+chan.server+'] '+chan.name+' '+str(self.mwindows.index(chan)))

    def update_nickwin(self):
        self.nickwin.clear()
        chan = self.mwindows[self.active_mwindow]
        x = 0
        maxy,maxx = self.scr.getmaxyx()
        for user in chan.users:
            self.nickwin.addstr(x,0,user)
            x = x + 1
            if x+3 > maxy: # break if too many nicks to fit window
                break
        self.nickwin.refresh()
        
    # draw the window again
    def update_window(self):
        channel = self.mwindows[self.active_mwindow]
        self.draw_lines_to_message_win(channel)
        self.update_status()
        self.update_nickwin()
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
        elif command == 'NAMES':
            self.update_nickwin() # fix later
        if self.mwindows[self.active_mwindow] == channel:
            for chanwin in self.mwindows:
                if chanwin.name == channel.name:
                    self.draw_lines_to_message_win(channel)
        self.update_status()
        self.update_nickwin()
        # refresh the windows
        self.messagewin.refresh()
        self.statuswin.refresh()
        self.statuswin2.refresh()
        self.typewin.refresh()        

    def draw_lines_to_message_win(self,channel):
        # This is fucked up. Write better when time
        # first clear the window
        self.messagewin.clear()
        lines = channel.lines
        mwy,mwx = self.messagewin.getmaxyx()
        currentline = 0
        lines.reverse()
        # get the lines for lines
        splittedlines = list()

        for line in lines:
            # if the sender is nick (it has ! in it) cut the host for now
            # REMEMBER TO FIX LATER
            nik = line.sender.find('!')
            if nik > 0:
                nikki = line.sender[0:nik]
            else:
                nikki = line.sender

            justwords = line.text.split(' ')
            justwords2 = list()
            pituus2 = (mwx -1 - (len(nikki)+3))
            for word in justwords:
                x = 0
                if len(word) > pituus2:
                    while len(word[x:len(word)]) > pituus2:
                        justwords2.append(word[x:(x+pituus2)])
                        x = x+pituus2
                    justwords2.append(word[x:len(word)])
                else:
                    justwords2.append(word)

            # now all the words should be nice length
            sline = '<'+nikki+'> '
            templines = list()
            for word in justwords2:
                if len(sline)+len(word) < mwx:
                    if len(sline) == len(nikki)+3:
                        sline = sline+''+word
                    else:
                        sline = sline+' '+word
                else:
                    templines.append(sline)
                    sline = '<'+nikki+'> '+word
            templines.append(sline)

            templines.reverse()
            splittedlines.extend(templines)

        numlines = len(splittedlines)

        # put the splitted lines to screen
        for line in splittedlines:
            if currentline < mwy:
                try:
                    self.messagewin.addstr(mwy - currentline -1, 0,line)
                except:
                    self.messagewin.addstr(mwy - currentline -1, 0,'FATAL ERROR')
                currentline = currentline + 1
            else:
                break
        lines.reverse()

    # here is the main function with the main loop etc.
    def start(self):
        self.irc.connect('ORJAnet','192.168.1.2',6667,'pzq2','asd2dasv','dyksi',self.update_window2)
        self.irc.start()

        currentserver = 0
        self.mwindows.append(self.irc.messages)
        # self.irc.connect('EFnet','someserverhere',6667,'pzq2','asd2dasv','dyksi',self.update_window2)
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
                    else: # change active connection
                        if len(self.irc.servers) > currentserver+1:
                            currentserver = currentserver + 1
                            self.irc.messages.server = self.irc.servers[currentserver].name
                        else:
                            currentserver = 0
                            self.irc.messages.server = self.irc.servers[currentserver].name
                        
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
            self.irc.message(inputstring,self.mwindows[self.active_mwindow].server,channel)

            self.typewin.erase()
            

        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def putmessagetoscreen(self,inputstring):
        chan = self.mwindows[self.active_mwindow]
        nick = self.irc.get_server(chan.server).nick
        chan.add_line(IRCMessage(str(nick),'itse',inputstring))
        self.update_window()
