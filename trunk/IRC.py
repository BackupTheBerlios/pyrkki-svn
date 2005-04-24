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
import Queue
import os
import sys

from time import localtime,strftime
from threading import *

class IRCUser:
    def __init__(self,user,host,server,nick,status,realname):
        self.user = user
        self.host = host
        self.server = server
        self.nick = nick
        self.status = status.strip('H') # removed the H
        self.realname = realname
        
class IRCMessage:
    def __init__(self,sender,to,text,time):
        self.sender = sender
        self.to = to
        self.text = text
        self.time = time

class QueueMessage:
    def __init__(self,lines,name):
        self.lines = lines
        self.name = name

class IRCServer(Thread):
    def __init__(self,name,serverIP, port, nick,user,username,messagequeue):
        Thread.__init__(self)
        self.name = name
        self.serverIP = serverIP
        self.port = port
        self.nick = nick
        self.user = user
        self.username = username
        self.messagequeue = messagequeue
        self.socket = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
    def run(self):
        while True:
            data = self.socket.recv ( 4096 )
            # raw lines splitted with irc protocols line end mark
            # problem is that it leaves one empty line so we have
            # to send all but last lines to messagefunk
            lines = data.split('\r\n')
            self.messagequeue.put(QueueMessage(lines[0:-1],self.name))

            # return to ping with pong
            if data.find ( 'PING' ) != -1:
                self.socket.send ( 'PONG ' + data.split() [ 1 ] + '\r\n' )


class IRCChannel:
    def __init__(self,name,mode,_server):
        self.name = name
        self.lines = list()
        self.users = list()
        self.mode = mode
        self.maxlines = 100
        self.server = _server
        self.usersopen = 0

    def add_user(self,user):
        if self.usersopen == 0:
            self.users = list() # clear users
            self.usersopen = 1 # wait for more users
        try:
            self.users.index(user)
        except:
            self.users.append(user)
    
    def add_users(self,users):
        if self.namesopen == 0:
            self.users = list() # clear the list
            self.namesopen = 1 # waiting for more users
        for user in users:
            try:
                self.users.index(user)
            except:
                self.users.append(user)

    def add_line(self,line):
        if len(self.lines) < self.maxlines:
            self.lines.append(line)
        else:
            self.lines.pop(0)
            self.lines.append(line)
    def len(self):
        return len(self.lines)

#connectiossa pitaa olla ainakin vunktio message, joka otta guilta vastaan viestia
class IRC(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.channels = list()
        self.messages = IRCChannel("STATUS","no","STATUS") # status channel
        self.messagequeue = Queue.Queue()
        self.servers = list()
        self.userwho = 1 # if user is doing who command

    def connect(self,name,serverIP, port, nick,user,username,messfunk):
        self.messagefunk = messfunk
        serv = IRCServer(name,serverIP,port,nick,user,username,self.messagequeue)
        serv.socket.connect ( ( serverIP, port ) )
        serv.socket.recv ( 4096 )
        serv.start()
        muss = 'NICK '+nick+'\r\n'
        serv.socket.send(muss)
        usermessage = 'USER '+user+' '+user+' '+user+' :'+username+'\r\n'
        serv.socket.send ( usermessage )
        if len(self.servers) == 0:
            self.messages.server = serv.name
        self.servers.append(serv)

    def run(self):
        while True:
            x = self.messagequeue.get()
            # FIX LATER
            server = self.get_server(x.name)
            self.messageparser(x.lines,server)

    def passmessagetochannel(self,channelNM,wcommand, txtline,sender):
        cha = self.get_channel(channelNM)
        if cha != None: 
            self.get_channel(channelNM).add_line(IRCMessage(str(sender),str(channelNM),txtline,localtime()))
        else:
            cha = self.messages
            cha.add_line(IRCMessage(str(sender),'PALVELIN',"TÄSTÄPUUTTUU LINE",localtime()))
        self.messagefunk(cha,'REMEBER TO FIX LATER',wcommand)
        
    def messageparser(self,lines,sserver):
        myre = re.compile('#[\S]+')
        myre2 = re.compile('\s[\S]+\s')
        channelNM = "STATUS" # default channel
        wcommand = "NONE"

        self.name = sserver.name
        self.nick = sserver.nick

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
                            self.channels.append(IRCChannel(channelname,"asd",self.name))
                            wcommand = 'NEWWINDOW'
                        txtline = '<'+str(om)+'>'+nick+' joined '+channelNM
                        # ask /names from channel to update channel.users
                        self.message('/who',sserver,channelNM)
                        self.userwho = 0
                        self.passmessagetochannel(channelNM,wcommand,txtline,sender)
                    elif command == 'PART':
                        if om == 1:
                            wcommand = 'REMOVEWINDOW'
                            # pass information to GUI
                            self.passmessagetochannel(channelNM,wcommand,"PARTED",sender)
                            self.channels.remove(self.get_channel(channelNM))
                        else:
                            txtline = ''+nick+' parted '+channelNM
                            # ask /names from channel to update channel.users
                            self.message('/who',sserver,channelNM)
                            self.userwho = 0
                            # pass information to GUI
                            self.passmessagetochannel(channelNM,wcommand,txtline,sender)
                    elif command == 'NICK':
                        newnick = params[params.find(':')+1:]
                        if om == 1:
                            self.nick = newnick
                        txtline = ''+nick+' is now know as '+newnick
                        self.passmessagetochannel(channelNM,wcommand,txtline,sender)
                    elif command == 'PRIVMSG':
                        res = myre.search(params)
                        if res is not None:
                            txtline = params[res.end()+2:]
                        else:
                            txtline = params
                        self.passmessagetochannel(channelNM,wcommand,txtline,sender)
                    else: # so its not one of those upper commands and not a number
                        txtline = ''+command+' '+params
                        self.passmessagetochannel(channelNM,wcommand,txtline,sender)
                else: # number command
                    if int(command) == 352: # who reply
                        wp = params.split(' ')
                        self.get_channel(channelNM).add_user(IRCUser(wp[2],wp[3],wp[4],wp[5],wp[6],wp[8]))
                        if self.userwho == 1: # 
                            self.passmessagetochannel(channelNM,wcommand,params,sender)
                    elif int(command) == 315: # end of who
                        self.get_channel(channelNM).usersopen=0
                        if self.userwho == 0: #
                            self.userwho = 1
                            self.messagefunk(self.get_channel(channelNM),'REMEBER TO FIX LATER',wcommand) # just to update win
                        else:
                            self.passmessagetochannel(channelNM,wcommand,params,sender)

                        
                    #elif int(command) == 353: # channel names is coming here
                    #    nickstemp = params[params.find(':')+1:]
                    #    nicks = nickstemp.split(' ')
                    #    nicks = nicks[0:-1]
                    #    self.get_channel(channelNM).add_users(nicks)
                    #    self.passmessagetochannel(channelNM,'NAMES','',sender)
                    #    # no names txt to GUI
                    #elif int(command) == 366: # end of names list
                    #    self.get_channel(channelNM).namesopen=0
                    #    self.passmessagetochannel(channelNM,'NAMES','',sender)
                    else:
                        txtline = ''+params[params.find(self.nick)+len(self.nick)+1:]
                        self.passmessagetochannel(channelNM,wcommand,txtline,sender)

            else: # this for commands that don't start with : example PING
                # lets get that PING pois
                if line.find('PING') == -1:
                    cha = self.get_channel(channelNM).add_line(IRCMessage(str('KESKEN 1'+server),'KESKEN',line,localtime()))
                    # send so it to GUI
                    self.passmessagetochannel(channelNM,wcommand,str(line),sender)
                else:
                    cha = self.get_channel(channelNM).add_line(IRCMessage(str('KESKEN 1'+server),'KESKEN',line,localtime()))
                    self.passmessagetochannel(channelNM,wcommand,str(line),sender)

    def get_channel(self,name):
        name = name.upper()
        if name == 'STATUS':
            return self.messages
        else:
            for channel in self.channels:
                if name == channel.name.upper():
                    return channel
    def get_server(self,name):
        for server in self.servers:
            if server.name == name:
                return server
        return self.servers[0]

    def message(self,mes,serverName,channel=''):
        if len(mes)<1:
            return 
        server = self.get_server(serverName)

        if mes[0] == '/' and len(mes)>1: # this is a command
            mes = mes[1:]
            num = mes.find(' ') # find the first space
            parameters = ''
            if num == -1: # no space found
                comm = mes.upper()
            else:
                comm = mes[:num] # first word
                comm =  comm.upper()
                parameters = mes[num+1:]
            if channel == 'STATUS':
                channel = ''
            else:
                channel = channel+' '
            for comma in list(('TOPIC','PART')):
                if comma == comm:
                    parameters = ':'+parameters
                    break

            if comm == 'MSG':
                num2 = parameters.find(' ')
                if num2  == -1:
                    return 0
                else:
                    msg = 'PRIVMSG '+parameters[:num2]+' :'+parameters[num2+1:]+'\r\n'
                    server.socket.send( msg )
                    return

            mes = comm+' '+channel+''+parameters+'\r\n'

            server.socket.send(mes)
            return 0

        # we parse it to channel
        if channel[0] == '#' and len(channel)>1 and len(mes)>0:
            msg = 'PRIVMSG '+str(channel)+' :'+mes+'\r\n'
            server.socket.send( msg )
