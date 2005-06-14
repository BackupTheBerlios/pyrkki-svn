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


import os
import sys
import curses
import curses.ascii

from IRC import *

from EditBuffer import *

class CursesGui:
    def __init__(self):

        # our irc-object
        self.irc = IRC(self.update_window2)
        
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
        self.messagewin = curses.newwin(y-2,x-13,0,0) # nick lengt is 9 char should be done dynamically
        # so that windows size should depend on nick lenghts

        # nick win
        self.nickwin = curses.newwin(y-2,13,0,x-13) # should also be dynamic
        
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
            self.nickwin.addstr(x,0,user.status+user.nick)
            x = x + 1
            if x+3 > maxy: # break if too many nicks to fit window
                break
        self.nickwin.refresh()
        
    def resizewindows(self,numlines=0):
        if numlines < 1:
            numlines = 0

        # numlines is according to typewin

        # init the first window as status window
        y,x = self.scr.getmaxyx()

        self.statuswin = curses.newwin(1,x,(y-(2+numlines)),0)
        #self.statuswin.addstr(0,0,"[NOT CONNECTED]")

        # staus win 2 who@where
        statuswin2W = 10
        self.statuswin2 = curses.newwin((1+numlines),statuswin2W,(y-(1+numlines)),0)
        self.statuswin2.addstr(0,0,"NICK")

        # type win
        self.typewin = curses.newwin((1+numlines),x-statuswin2W-1,(y-(1+numlines)),statuswin2W-1)
        self.typewin.keypad(1)

        # message win
        self.messagewin = curses.newwin((y-(2+numlines)),x-13,0,0) # nick lengt is 9 char should be done dynamically
        # so that windows size should depend on nick lenghts

        # nick win
        self.nickwin = curses.newwin((y-(2+numlines)),13,0,x-13) # should also be dynamic
        
        # refresh the windows
        self.update_window()

        
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

    def get_time(self,loctime):
        # example
        # strftime("%a, %d %b %Y %H:%M:%S", loctime)
        # 'Sun, 24 Apr 2005 13:46:24'
        return strftime("%H:%M",loctime)

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

        # check the length of the time prefix
        prefixlength = (len(self.get_time(localtime())) +1) # +1 for one space
        for line in lines:
            # if the sender is nick (it has ! in it) cut the host for now
            # REMEMBER TO FIX LATER
            nik = line.sender.find('!')
            if nik > 0:
                nikki = line.sender[0:nik]
            else:
                nikki = line.sender

            linetime = self.get_time(line.time)+' '

            justwords = line.text.split(' ')
            justwords2 = list()
            pituus2 = (mwx -1 - (len(nikki)+3+prefixlength)) # carefull with the parenthesis

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
            sline = linetime+'<'+nikki+'> '
            templines = list()
            for word in justwords2:
                if len(sline)+len(word) < mwx:
                    if len(sline) == len(nikki)+3+prefixlength:
                        sline = sline+''+word
                    else:
                        sline = sline+' '+word
                else:
                    templines.append(sline)
                    sline = linetime+'<'+nikki+'> '+word
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


    def start(self):
        self.irc.connect('ORJAnet','192.168.1.2',6667,'petteri','asd2dasv','dyksi')
        self.irc.start()

        currentserver = 0
        self.mwindows.append(self.irc.messages)
        #self.irc.connect('EFnet','someseerver',6667,'pzq2','asd2dasv','dyksi',self.update_window2)
        pirssion = 1
        # lets take some key input this just a quick method. Remember to fix later
        while pirssion == 1:
            textbuffer = EditBuffer()
            enterpushed = 0
            oldlen = 0

            while enterpushed == 0:
                ty,tx = self.typewin.getmaxyx()
                ch = self.typewin.getch(textbuffer.y,textbuffer.x)
                #lines = textbuffer.input(self.typewin.getch(textbuffer.x,textbuffer.y+1),ty,tx)
                if ch > 0:
                    if ch == 10: # enter
                        enterpushed = 1
                    lines = textbuffer.input(ch,ty,tx)
                    
                    
                    # update the typewindow
                    self.typewin.clear()
                    
                    if len(lines) != oldlen:
                        self.resizewindows(len(lines)-1)
                        oldlen = len(lines)
                        
                    linecounter = 0
                    wholestring = ''
                    for line in lines:
                        self.typewin.addstr(linecounter,1,line)
                        wholestring = wholestring + line
                        linecounter = linecounter +1

                
                    self.typewin.refresh()
            # enter has been pushed, back to normal window sizes
            self.resizewindows(0)

            #put our message to channel or status screen
            self.putmessagetoscreen(wholestring)
            self.update_window()
            channel = self.mwindows[self.active_mwindow].name
            self.irc.message(wholestring,self.mwindows[self.active_mwindow].server,channel)
            self.typewin.erase()
            

        curses.nocbreak()
        stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def putmessagetoscreen(self,inputstring):
        chan = self.mwindows[self.active_mwindow]
        # dirty hack FIX LATER
        try:
            nick = self.irc.get_server(chan.server).nick
        except:
            nick = 'pyRKKI ERROR: NOT CONNECTED'
        chan.add_line(IRCMessage(str(nick),'itse',inputstring,localtime()))
        self.update_window()

class EditBuffer:
    def __init__(self):
        self.lines = list()
        self.lines.append('') # first line
        self.pointer = 0
        self.x = 1
        self.y = 0
        self.cursormove = 0 # not move cursor

    def add_char(self, ch):
        li = self.lines[self.y]
        self.lines[self.y] = li[:self.x-1]+ch+li[self.x-1:]

    def del_char(self):
        if self.x < 2 and self.y > 0:
            self.lines[self.y-1] = self.lines[self.y-1][:-1]
        else:
            li = self.lines[self.y]
            self.lines[self.y] = li[:self.x-2]+li[self.x-1:]
    
    def input(self, ch, winY, winX):
        self.maxx = winX
        self.maxyy = winY
        self.cursormove = 0

        if ch == curses.KEY_LEFT:
            if self.x > 1:
                self.x = self.x -1
        elif ch == curses.KEY_RIGHT:
            if self.x < len(self.lines[self.y])+1:
                self.cursormove = 1
        elif ch == curses.KEY_UP:
            if self.y > 0 and len(self.lines[self.y-1])+2 > self.x:
                self.y = self.y-1
        elif ch == curses.KEY_DOWN:
            if self.y < len(self.lines)-1 and len(self.lines[self.y+1])+2 > self.x:
                self.y = self.y+1
        elif ch == curses.ascii.SOH: # ctrl-a
            self.cursormove = 2 # begin of the line
        elif ch == curses.ascii.ENQ: # ctrl-e
            self.cursormove = 5 # end of the line
        elif ch == curses.ascii.VT: # ctrl-k
            if len(self.lines) > 1:
                if self.y == len(self.lines)-1:
                    del self.lines[self.y]
                    self.y = self.y -1
                else:
                    del self.lines[self.y]
                self.x = len(self.lines[self.y])+1
            else:
                del self.lines
                self.lines = list()
                self.x=1
                self.y=0
        elif ch in (curses.ascii.BS, curses.KEY_BACKSPACE, 127): # backspace
            if self.x > 1:
                self.del_char()
            self.cursormove = 3 # one back
        else:
            totalcount = 0
            for line in self.lines:
                totalcount = totalcount + len(line)
            if totalcount < 500:
                for chmark in list(' 1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZÅÄÖabcdefghijklmnopqrstuvwxyzåäö!"#¤%&/()=?+¡@£$~¥{[]}\~<>,.-*^:;'):
                    if ch == ord(chmark):
                        self.add_char(chmark)
                        self.cursormove = 1 # one forward
        newlines = list()
        wholestring = ''
        newstring = ''
        for line in self.lines:
            wholestring = wholestring + line

        splitted = wholestring.split(' ')

        if len(splitted) == 1: #only one word
            while len(wholestring) > 0: # we still have character left
                newlines.append(wholestring[:self.maxx-2]) # add line
                wholestring = wholestring[self.maxx-2:] # the end of the line for next line
        else: # more than one word
            newlines.append('')
            newstring = ''
            wordcount = 0
            while wordcount < len(splitted):
                word = splitted[wordcount]
                
                if wordcount < (len(splitted) -1): # is not the last
                    word = word+' ' # add the space
                temp = newlines[len(newlines)-1]
                
                if len(temp+word) < self.maxx-2:
                    newlines[len(newlines)-1] = temp + word
                else:
                    if len(word) < self.maxx-2:
                        newlines.append(word)
                        # for jumpingo
                        if self.x == self.maxx-2 and self.cursormove == 1:
                            self.cursormove = 4 # jump
                    else:
                        while len(word) > 0:
                            newlines.append(word[:self.maxx-2])
                            word = word[self.maxx-2:]
                wordcount = wordcount +1

        if len(newlines) == 0:
            newlines.append('')
        
        self.lines = newlines

        if self.cursormove == 1: # one forward
            if self.x > len(self.lines[self.y]):
                self.y = self.y +1
                self.x = 2
            else:
                self.x = self.x +1
        elif self.cursormove == 2: # ctrl-a
            self.x = 1
        elif self.cursormove == 3: # one back
            if self.x > 1 and self.y == 0:
                self.x = self.x -1
            if self.y > len(self.lines) -1:
                self.y = self.y -1
                self.x = len(self.lines[self.y])+1
            elif self.x > 2 and self.y > 0:
                self.x = self.x -1
            elif self.y > 0:
                self.y = (self.y -1)
                self.x = len(self.lines[self.y])+1

        elif self.cursormove == 4: # jump
            if self.x > len(self.lines[self.y]):
                self.y = self.y +1
                fspace = self.lines[self.y].find(' ')
                if fspace != -1:
                    self.x = fspace
                else:
                    self.x = len(self.lines[self.y])+1
        elif self.cursormove == 5: # end of the line
            self.x = len(self.lines[self.y])+1

            
        return self.lines
