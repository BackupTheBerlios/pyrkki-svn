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

import socket
import thread
import re

import os
import sys

from threading import *

class IRCMessage:
    def __init__(self,sender,to,text):
        self.sender = sender
        self.to = to
        self.text = text

class IRCThread(Thread):
    def __init__(self, irc,messagefunk):
        Thread.__init__(self)
        self.irc = irc

        self.messagefunk = messagefunk

    def run(self):

        while True:
            data = self.irc.recv ( 4096 )

            # raw lines splitted with irc protocols line end mark
            # problem is that it leaves one empty line so we have
            # to send all but last lines to messagefunk
            lines = data.split('\r\n')
            self.messagefunk(lines[0:-1])

            # return to ping with pong
            if data.find ( 'PING' ) != -1:
                self.irc.send ( 'PONG ' + data.split() [ 1 ] + '\r\n' )


class IRCChannel:
    def __init__(self,name,mode):
        self.name = name
        self.lines = list()
        self.nicks = list()
        self.mode = mode
        self.maxlines = 100
        self.network =

    def add_line(self,line):
        if len(self.lines) < self.maxlines:
            self.lines.append(line)
        else:
            self.lines.pop(0)
            self.lines.append(line)
    def len(self):
        return len(self.lines)

#connectiossa pitaa olla ainakin vunktio message, joka otta guilta vastaan viestia
class IRCConnection:
    def __init__(self,name,serverIP, port, nick,user,username,messfunk):
        self.name = name
        self.serverIP = serverIP
        self.port = port
        self.nick = nick
        self.user = user
        self.username = username

        self.messagefunk = messfunk
        self.server = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
        #do the join commands etc

        self.channels = list()

        self.messages = IRCChannel("STATUS","no")

        #self.commands = dict([('JOIN',Join()),('PART',Part())])
        self.commands = list()
        self.commands.append(Join())
        self.commands.append(Part())
        self.commands.append(Msg())
        self.commands.append(Nick())
        self.commands.append(Names())

    def connect(self):
        server = self.server
        user = self.user
        username = self.username
        
        server.connect ( ( self.serverIP, self.port ) )
        server.recv ( 4096 )

        self.thread = IRCThread(server,self.messageparser)
        self.thread.start()

        self.message('/nick '+self.nick)

        usermessage = 'USER '+user+' '+user+' '+user+' :'+username+'\r\n'
        server.send ( usermessage )

    def passmessagetogui(self,channelNM,wcommand, txtline,sender):
        cha = self.get_channel(channelNM)
        if cha != None: 
            self.get_channel(channelNM).add_line(IRCMessage(str(sender),str(channelNM),txtline))
        else:
            cha = self.messages
            cha.add_line(IRCMessage(str(sender),'PALVELIN',"TÄSTÄPUUTTUU LINE"))
        self.messagefunk(cha,self.name,wcommand)
        
    def messageparser(self,lines):
        myre = re.compile('#[\S]+')
        myre2 = re.compile('\s[\S]+\s')
        channelNM = "STATUS" # default channel
        wcommand = "NONE"

        # THE MESSAGE PARSER OF ALL TIMES
        # MESSAGES ARE IN FOLLOWING FORMAT
        
        # message    =  [ ":" prefix SPACE ] command [ params ] crlf
        # prefix     =  servername / ( nickname [ [ "!" user ] "@" host ] )
        # command    =  1*letter / 3digit
        # params     =  *14( SPACE middle ) [ SPACE ":" trailing ]
        #            =/ 14( SPACE middle ) [ SPACE [ ":" ] trailing ]
        #
        # nospcrlfcl =  %x01-09 / %x0B-0C / %x0E-1F / %x21-39 / %x3B-FF
        #            ; any octet except NUL, CR, LF, " " and ":"
        # middle     =  nospcrlfcl *( ":" / nospcrlfcl )
        # trailing   =  *( ":" / " " / nospcrlfcl )
        #
        # SPACE      =  %x20        ; space character
        # crlf       =  %x0D %x0A   ; "carriage return" "linefeed"

        for line in lines:
            sender = ''
            nick = ''
            nickathost = ''
            server = ''
            command = ''
            command_number = 000
            params = ''
            
            if line[:1] == ':': # prefix found
                wcommand = "NONE"
                sender = line[1:line.find(' ')] #sender is what is next space

                if sender.find('.') == -1: # it must be nick since no dots
                    nick = sender
                elif sender.find('@') != -1 and sender.find('!') != -1: # it must be nick at host since it has at sign
                    nickathost = sender
                    nick = sender[:sender.find('!')]
                else:
                    server = sender
                    
                res2 = myre2.search(line) # catch the command
                command = line[res2.start()+1:res2.end()-1]

                if len(command) == 3: # it number command
                    command_number = int(command)
                    
                params = line[res2.end():]

                # lets see if this is going to some channel
                res = myre.search(params)

                if res != None:
                    channelname = params[res.start():res.end()]
                else: # If message is not going to any channel put it in STATUS-channel
                    channelname = 'STATUS'

                channelNM = channelname # this could mean trouble later

                # lets handle some commands
                if len(command)>3: # Text command
                    txtline = ''
                    om = 0 # ourmove

                    if nickathost[:len(self.nick)] == self.nick: # its us that makes a move
                        om = 1
                    if nick == self.nick:
                        om = 1
                            
                    if command == 'JOIN':
                        if om == 1:
                            self.channels.append(IRCChannel(channelname,"asd"))
                            wcommand = 'NEWWINDOW'
                        txtline = '<'+str(om)+'>'+nick+' joined '+channelNM
                        self.passmessagetogui(channelNM,wcommand,txtline,sender)
                    elif command == 'PART':
                        if om == 1:
                            wcommand = 'REMOVEWINDOW'
                            # pass information to GUI
                            self.passmessagetogui(channelNM,wcommand,"PARTED",sender)
                            self.channels.remove(self.get_channel(channelNM))
                        else:
                            txtline = ''+nick+' parted '+channelNM
                            # pass information to GUI
                            self.passmessagetogui(channelNM,wcommand,txtline,sender)
                    elif command == 'NICK':
                        newnick = params[params.find(':')+1:]
                        if om == 1:
                            self.nick = newnick
                        txtline = ''+nick+' is now know as '+newnick
                        self.passmessagetogui(channelNM,wcommand,txtline,sender)
                    elif command == 'PRIVMSG':
                        res = myre.search(params)
                        if res is not None:
                            txtline = params[res.end()+2:]
                        else:
                            txtline = params
                        self.passmessagetogui(channelNM,wcommand,txtline,sender)
                    else: # so its not one of those upper commands and not a number
                        txtline = ''+command+' '+params
                        self.passmessagetogui(channelNM,wcommand,txtline,sender)
                else: # number command
                    txtline = ''+params[params.find(self.nick)+len(self.nick)+1:]
                    self.passmessagetogui(channelNM,wcommand,txtline,sender)


            else: # this for commands that don't start with : example PING
                # lets get that PING pois
                if line.find('PING') == -1:
                    cha = self.get_channel(channelNM).add_line(IRCMessage(str('KESKEN 1'+server),'KESKEN',line))
                    # send so it to GUI
                    #self.passmessagetogui(channelNM,wcommand,txtline,sender)
                    self.passmessagetogui(channelNM,wcommand,str(line),sender)
                else:
                    cha = self.get_channel(channelNM).add_line(IRCMessage(str('KESKEN 1'+server),'KESKEN',line))
                    self.passmessagetogui(channelNM,wcommand,str(line),sender)

    def get_channel(self,name):
        if name == 'STATUS':
            return self.messages
        else:
            for channel in self.channels:
                if name == channel.name:
                    return channel

    def message(self,mes,channel=''):
        num = mes.find(' ') # find the first space
        if num == -1: # no space found
            comm = mes
        else:
            comm = mes[:num] # first word
        comm = comm.upper() # make the command uppercase
        for command in self.commands:
            if command.name == comm:
                msg = command.execute(mes[len(command.name)+1:],channel)
                if msg == -1:
                    return 0
                else:
                    self.server.send( msg )
                    return 0
        # we parse it to channel
        if channel[:1] == '#' and len(channel)>1 and len(mes)>0:
            msg = 'PRIVMSG '+str(channel)+' :'+mes+'\r\n'
            self.server.send( msg )

class Join:
    def __init__(self):
        self.name = '/JOIN'
        self.helptxt ="JOIN APUVA"
    def execute(self,message,channel=''):
        if message[:1] == '#' and len(message)>1:
            return 'JOIN '+message+'\r\n'
        else:
            return -1

class Part:
    def __init__(self):
        self.name = '/PART'
        self.helptxt ="PART APUVA"
    def execute(self,message,channel=''):
        if channel[:1] == '#' and len(channel)>1:
            return 'PART '+channel+'\r\n'
        else:
            return -1

class Nick:
    def __init__(self):
        self.name = '/NICK'
        self.helptxt = '/NICK your nickname'
    def execute(self,message,channel=''):
        if len(message)>1 and message[:1] != '#': # this should be corrected someday
            return 'NICK '+message+'\r\n'
        else:
            return -1
class Names:
    def __init__(self):
        self.name = '/NAMES'
        self.helptxt = '/NAMES gives names visiable to user'
    def execute(self,message,channel=''):
        return 'NAMES '+channel+'\r\n' # this is not ready yet.

class Msg:
    def __init__(self):
        self.name = '/MSG'
        self.helptxt = 'Command used to send private messages'
    def execute(self,message,channel=''):
        if message[:1] != '#' or message[:1] != '!':
            num = message.find(' ') # find the first space
            if num == -1: # no space found
                return -1
            elif len(message[num+1:])>0:
                nick = message[:num] # first word
                return 'PRIVMSG '+nick+' :'+message[num+1:]+'\r\n'
            else:
                return -1
        else:
            return -1
