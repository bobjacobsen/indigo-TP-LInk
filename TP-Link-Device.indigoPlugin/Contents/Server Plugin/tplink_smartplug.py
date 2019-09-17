#!/usr/bin/env python
#
# based on work by by Lubomir Stroetmann
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

import socket
import sys
import argparse
import json
from protocol import tplink_smartplug

sys.path.append('./TP-Link-Device.indigoPlugin/Contents/Server Plugin')

version = 0.5

################################################################################
def main():
	####################################################################
	def check_server(address):
		# Create a TCP socket
		s = socket.socket()
		s.settimeout(2.0)
		port = 9999
		# print "Checking availability of %s on port %s" % (address, port)
		try:
			s.connect((address, port))
			# print "Connected to %s on port %s" % (address, port)
			return address
		except socket.error, e:
			print "Connection to %s on port %s failed: %s" % (address, port, e)
			parser.error("Invalid hostname.")
		finally:
			s.close()
	
	my_target = tplink_smartplug(None, None)

	# Parse commandline arguments
	parser = argparse.ArgumentParser(description="TP-Link Wi-Fi Smart Plug Client v" + str(version))
	parser.add_argument("-t", "--target", metavar="<hostname>", required=False, help="Target hostname or IP address", type=check_server)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-c", "--command", metavar="<command>", help="Preset command to send. Choices are: "+", ".join(my_target.listCommands()), choices=my_target.listCommands())
	group.add_argument("-C", "--CMD", metavar="<command>", help="unvalidated Command")
	group.add_argument("-j", "--json", metavar="<JSON string>", help="Full JSON string of command to send")
	parser.add_argument("-d", "--deviceID", metavar="<deviceID>", required=False, help="device ID for testing powerstrip")
	parser.add_argument("-p", "--childID", metavar="<childID>", required=False, help="port on device", type=int)

	args = parser.parse_args()

	my_target = tplink_smartplug(args.target, 9999, args.deviceID, args.childID)

	if args.command is None:
		response = my_target.send(args.json)
	elif args.command == 'discover':
		response = my_target.discover()
	else:
		response = json.loads(my_target.send(args.command))

	try:
		print "Received: ", json.dumps(response, sort_keys=True, indent=2, separators=(',', ': '))
	except ValueError, e:
		print ("Json value error: %s on %s" % (e, response) )


###### main for testing #####
if __name__ == '__main__' :
	main()
