#!/usr/bin/env python
#
# based on work by by Lubomir Stroetmann and others
# Copyright 2016 softScheck GmbH
#  from: https://github.com/softScheck/tplink-smartplug/blob/master/tplink_smartplug.py
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import socket
import struct
import sys

# Predefined Smart Plug Commands
# This list can be extended or edited by adding/removing dictionary entries
commands = {'info'     : '{"system":{"get_sysinfo":{}}}',
			'on'       : '{"system":{"set_relay_state":{"state":1}}}',
			'off'      : '{"system":{"set_relay_state":{"state":0}}}',
			'cloudinfo': '{"cnCloud":{"get_info":{}}}',
			'wlanscan' : '{"netif":{"get_scaninfo":{"refresh":0}}}',
			'time'     : '{"time":{"get_time":{}}}',
			'discover' : '{"system":{"get_sysinfo":{}}}',
			'schedule' : '{"schedule":{"get_rules":{}}}',
			'countdown': '{"count_down":{"get_rules":{}}}',
			'antitheft': '{"anti_theft":{"get_rules":{}}}',
			'reboot'   : '{"system":{"reboot":{"delay":1}}}',
			'reset'    : '{"system":{"reset":{"delay":1}}}',
			'e+i'      : '{ "emeter": { "get_realtime": {} }, "system": { "get_sysinfo": {} } }',
			'energy'   : '{"emeter":{"get_realtime":{}}}'
}

# We don't want to print if this class has been called from Indigo
istty = False
if sys.stdin.isatty():
	# running interactively
	istty = True

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
	key = 171
	result = struct.pack('>I', len(string))
	for i in string:
		a = key ^ ord(i)
		key = a
		result += chr(a)
	return result

def decrypt(string):
	key = 171
	result = ""
	for i in string:
		a = key ^ ord(i)
		key = ord(i)
		result += chr(a)
	return result

################################################################################
class tplink_smartplug():
	####################################################################
	def __init__(self, address, port, deviceID = None, childID = None):
		self.address  = address
		self.port 	  = port
		self.deviceID = deviceID
		self.childID  = childID
 
		# both or neither deviceID and childID should be set
		if (deviceID is not None and childID is not None) or (deviceID is None and childID is None):
			pass # both combinations are ok
		else:
			quit("ERROR: both deviceID and childID must be set together")

	# Send command and receive reply
	def send(self, request):
		if request in commands:
			cmd = commands[request]
		else:
			cmd = request

		# if both deviceID and childID are set, { context... } is prepended to the command
		if self.deviceID is not None and self.childID is not None:
			context = '{"context":{"child_ids":["' + self.deviceID + "{:02d}".format(int(self.childID)) +'"]},'
			# now replace the initial '{' of the command with that string
			cmd = context + cmd[1:]

		if istty: print "Sent:     ", cmd 
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.settimeout(3.0)
			sock.connect((self.address, 9999))
			sock.send(encrypt(cmd))

			buffer = bytes()
			# Some devices send responses with a length header of 0 and
			# terminate with a zero size chunk. Others send the length and
			# will hang if we attempt to read more data.
			length = -1
			while True:
				chunk = sock.recv(4096)
				if length == -1:
					length = struct.unpack(">I", chunk[0:4])[0]
				buffer += chunk
				if (length > 0 and len(buffer) >= length + 4) or not chunk:
					break
		except socket.timeout:
			return json.dumps({'error': 'TP-Link connection timeout'})
		except Exception as e:
			return json.dumps({'error': "TP-Link error: " + str(e)})
	
		finally:
			try:
				if sock:
					sock.shutdown(socket.SHUT_RDWR)
			except OSError:
				# OSX raises OSError when shutdown() gets called on a closed
				# socket. We ignore it here as the data has already been read
				# into the buffer at this point.
				pass

			finally:
				if sock:
					sock.close()

		response = decrypt(buffer[4:])

		return response

	def discover(self):
		cmd = commands['discover']
		address = '255.255.255.255'
		port = 9999
		timeout = 4.0
		discovery_packets = 3
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.settimeout(float(timeout))

		if istty: print("Sending discovery to %s:%s   %s" % (address, port, cmd))

		encrypted_cmd = encrypt(cmd)
		for _ in range(discovery_packets):
			sock.sendto(encrypted_cmd[4:], (address, port))

		if istty: print("Waiting %s seconds for responses..." % timeout)

		foundDevs = {}
		try:
			while True:
				data, addr = sock.recvfrom(4096)
				ip, port = addr
				info = json.loads(decrypt(data))
				# print("%s\n%s\n" % (ip, info))
				if not ip in foundDevs:
					foundDevs[ip] = info
		except:
			pass
			
		return foundDevs

	def listCommands(self):
		return commands
