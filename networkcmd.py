#!/usr/bin/env python
"""
Copyright 2018 Allan Brand

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__author__ = 'Allan Brand'
__copyright__ = 'Copyright 2018'
__credits__ = ['Allan Brand']
__license__ = 'Apache v2.0'
__version__ = '0.9.0'
__maintainer__ = 'Allan Brand'
__email__ = 'allan.brand@gmail.com'
__status__ = 'Development'

import argparse
from getpass import getpass
import time, os, signal
from netmiko import Netmiko
from netmiko import ssh_exception
import threading
from queue import Queue

#
# Initialize some variables
###############################################
dev_list = []
cmd_list = []
nThreads = 8
eQueue = Queue()
tLock = threading.Lock()
signal.signal(signal.SIGPIPE, signal.SIG_DFL)
signal.signal(signal.SIGINT, signal.SIG_DFL)

#
# Configure Command-line Arguments
###############################################
parser = argparse.ArgumentParser()
grpCmd = parser.add_mutually_exclusive_group(required=True)
grpHst = parser.add_mutually_exclusive_group(required=True)
parser.add_argument('-u', '--username',
		    help='define the username')
parser.add_argument('-P', '--protocol',
		    required=False,
		    choices=['ssh', 'telnet'],
		    default='ssh',
		    help='define connection protocol')
parser.add_argument('-p', '--port',
                    required=False,
		    type=int,
		    choices=range(0,65535),
		    help='define the port number to connect to')
parser.add_argument('-w', '--wait',
                    required=False,
 		    type=int,
		    help='define delay time for the next prompt')
parser.add_argument('-M', '--multithread',
		    help='process commands on multiple devices simultaneously')
parser.add_argument('-l', '--log',
                    required=False,
 		    help='define a logfile prefix')
#
# Functionality to be added later
# parser.add_argument('-a', '--append',
#                     required=False,
# 		      action='store_true',
#		      help='log will be appended to existing file')
grpCmd.add_argument('-c', '--cmd',
		    help='define the command to send')
grpCmd.add_argument('-r', '--runfile',
		    help='define a file with a set of command to send')
grpHst.add_argument('-t', '--target',
		    help='define the hostname to connect')
grpHst.add_argument('-T', '--targetfile',
		    help='define a target file (one host per line)')
args = parser.parse_args()

if args.port:
	PORT = args.port
else:
	PORT = 22

if args.wait:
	CMD_DELAY = args.wait
else:
	CMD_DELAY = 1

if args.log:
	logFile = args.log + ip + '.log'
else:
	logFile = ip + '.log'


def single_SSH(ip):
	try:
		conn = Netmiko(host=ip, device_type='autodetect', username=uname, password=pword, auth_timeout=60, session_log=logFile)
		conn.find_prompt()
		for cmd in cmd_list:
			conn.send_command(cmd)
			time.sleep(CMD_DELAY)
		conn.disconnet()
	except ssh_exception.NetmikoTimeoutException:
		continue
	except ssh_exception.NetmikoAuthentionException:
		os.kill(os.getpid(), signal.SIGUSR1)


def threaded_SSH(i, q):
	while True:
		ip = q.get()
		try:
			conn = Netmiko(host=ip, device_type='autodetect', username=uname, password=pword, auth_timeout=60, session_log=logFile)
			conn.find_prompt()
			for cmd in cmd_list:
				conn.send_command(cmd)
				time.sleep(CMD_DELAY)
			conn.disconnet()
		except ssh_exception.NetmikoTimeoutException:
			q.task_done()
			continue
		except ssh_exception.NetmikoAuthentionException:
			q.task_done()
			os.kill(os.getpid(), signal.SIGUSR1)
		q.task_done()

def single_Telnet(ip):
	t = telnetlib.Telnet(ip)
	t.read_until(b'Username:')
	t.write(uname.encode('ascii') + b'\n')
	if pword:
		t.read_until(b'Password:')
		t.write(pword.encode('ascii') + b'\n')

		for cmd in cmd_list:
			t.write(b'{}\n'.format(cmd))
			time.sleep(CMD_DELAY)
			print(t.read_all().decode('ascii'))

def threaded_Telnet(i, q):
	# WIP
	pass

def Threaded_Operation():
	for d in list_dev:
		eQueue.put(d)

	for i in range(nThreads):
		thread = threading.Thread(target=threaded_SSH, args=(i, eQueue,))
		thread.daemon = True
		thread.start()

	eQueue.join()

if__name__== "__main__":
	#
	# Gather login credentials
	###############################################
	if args.username:
		uname = args.username
	else:
		uname = input('Username: ')

	pword = getpass.getpass()

	#
	# Gather targets to touch
	###############################################
	if args.target:
		dev_list.append(args.target)
	else:
		with open(args.targetfile) as f:
			for line in f:
				dev_list.append(line)

	#
	# Gather commands to execute
	###############################################
	if args.cmd:
		cmd_list.append(args.cmd)
	else:
		with open(args.targetfile) as f:
			for line in f:
				cmd_list.append(line)


	#
	# Process commands
	###############################################
	if args.protocol == 'telnet':
		import telnetlib
		if args.multithread:
			Threaded_Telnet()
		else:
			single_Telnet(args.target)
	else:
		if args.multithread:
			Threaded_Operation()
		else:
			single_SSH(args.target)
