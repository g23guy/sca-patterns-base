"""
Supportconfig Analysis Library for HAE python patterns

Library of functions for creating python patterns specific to 
High Availability Extension (HAE) clustering
"""
##############################################################################
#  Copyright (C) 2014 SUSE LLC
##############################################################################
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, see <http://www.gnu.org/licenses/>.
#
#  Authors/Contributors:
#    Jason Record (jrecord@suse.com)
#
#  Modified: 2014 Jun 12
#
##############################################################################

import sys
import re
import Core
import string

def getSBDInfo():
	"""
	Gets split brain detection partition information. Gathers information from the sbd dump command and the /etc/sysconfig/sbd file. SBD partitions with invalid sbd dump output are ignored.

	Args:		None
	Returns:	List of SBD Dictionaries with keys
		SBD_DEVICE (String) - The /etc/sysconfig/sbd SDB_DEVICE variable. This value applies to all and is stored with each sbd device.
		SBD_OPTS (String) - The /etc/sysconfig/sbd SBD_OPTS variable
		Version (Int) - The SDB header version string
		Slots (Int) - The number of SDB slots
		Sector_Size (Int) - The SBD sector size
		Watchdog (Int) - The SBD watchdog timeout
		Allocate (Int) - The SBD allocate timeout
		Loop (Int) - The SBD loop timeout
		MsgWait (Int) - The SBD msgwait timeout
	Example:

	SBD = HAE.getSBDInfo()
	MSG_WAIT_MIN = 300
	MSG_WAIT_OVERALL = MSG_WAIT_MIN
	# Find the smallest msgwait value among the SBD partitions
	for I in range(0, len(SBD)):
		if( SBD[I]['MsgWait'] < MSG_WAIT_OVERALL ):
			MSG_WAIT_OVERALL = SBD[I]['MsgWait']
	# See if the smallest msgwait is less than the minimum required
	if ( MSG_WAIT_OVERALL < MSG_WAIT_MIN ):
		Core.updateStatus(Core.REC, "Consider changing your msgwait time")
	else:
		Core.updateStatus(Core.IGNORE, "The msgwait is sufficient")
	"""
	SBD_LIST = []
	SBD_DICTIONARY = { 
		'Device': '',
		'SBD_DEVICE': '',
		'SBD_OPTS': '',
		'Version': '',
		'Slots': -1,
		'Sector_Size': -1,
		'Watchdog': -1,
		'Allocate': -1,
		'Loop': -1,
		'MsgWait': -1,
	}
	FILE_OPEN = "ha.txt"
	CONTENT = {}
	IDX_PATH = 3
	IDX_KEY = 0
	IDX_VALUE = 1
	SYSCONFIG_FOUND = False
	DUMP_FOUND = False

	try:
		FILE = open(Core.path + "/" + FILE_OPEN)
	except Exception, error:
#		print "Error opening file: %s" % error
		Core.updateStatus(Core.ERROR, "ERROR: Cannot open " + FILE_OPEN)

	SBD_PATH = ''
	SBD_DEVICE = ''
	SBD_OPTS = ''
	DUMPCMD = re.compile("/usr/sbin/sbd -d .* dump")
	SYSCONFIG = re.compile("^# /etc/sysconfig/sbd")
	INVALID = re.compile("Syntax", re.IGNORECASE)
	for LINE in FILE:
		if DUMP_FOUND:
#			print "Dump: " + str(LINE)
			if "#==[" in LINE:
				DUMP_FOUND = False
				#append SBD_DICTIONARY to SBD_LIST
				SBD_DICTIONARY['Device'] = SBD_PATH
				SBD_DICTIONARY['SBD_DEVICE'] = SBD_DEVICE
				SBD_DICTIONARY['SBD_OPTS'] = SBD_OPTS
				SBD_LIST.append(dict(SBD_DICTIONARY))
#				print "SBD_DICTIONARY = " + str(SBD_DICTIONARY)
				SBD_PATH = ''
				SBD_DICTIONARY = { 
					'Device': '',
					'SBD_DEVICE': '',
					'SBD_OPTS': '',
					'Version': '',
					'Slots': -1,
					'Sector_Size': -1,
					'Watchdog': -1,
					'Allocate': -1,
					'Loop': -1,
					'MsgWait': -1,
				}
			elif INVALID.search(LINE):
				DUMP_FOUND = False
				SBD_PATH = ''
				SBD_DICTIONARY = { 
					'Device': '',
					'SBD_DEVICE': '',
					'SBD_OPTS': '',
					'Version': '',
					'Slots': -1,
					'Sector_Size': -1,
					'Watchdog': -1,
					'Allocate': -1,
					'Loop': -1,
					'MsgWait': -1,
				}
			elif LINE.startswith('Header'):
				SBD_DICTIONARY['Version'] = LINE.split(':')[IDX_VALUE].strip()
			elif LINE.startswith('Number'):
				SBD_DICTIONARY['Slots'] = int(LINE.split(':')[IDX_VALUE].strip())
			elif LINE.startswith('Sector'):
				SBD_DICTIONARY['Sector_Size'] = int(LINE.split(':')[IDX_VALUE].strip())
			elif "watchdog" in LINE:
				SBD_DICTIONARY['Watchdog'] = int(LINE.split(':')[IDX_VALUE].strip())
			elif "allocate" in LINE:
				SBD_DICTIONARY['Allocate'] = int(LINE.split(':')[IDX_VALUE].strip())
			elif "loop" in LINE:
				SBD_DICTIONARY['Loop'] = int(LINE.split(':')[IDX_VALUE].strip())
			elif "msgwait" in LINE:
				SBD_DICTIONARY['MsgWait'] = int(LINE.split(':')[IDX_VALUE].strip())				
		elif SYSCONFIG_FOUND:
			if "#==[" in LINE:
				SYSCONFIG_FOUND = False
			elif LINE.startswith('SBD_DEVICE'):
				SBD_DEVICE = re.sub("\n|\"|\'", '', LINE.split('=')[IDX_VALUE])
			elif LINE.startswith('SBD_OPTS'):
				SBD_OPTS = re.sub("\n|\"|\'", '', LINE.split('=')[IDX_VALUE])
		elif SYSCONFIG.search(LINE):
			SYSCONFIG_FOUND = True
		elif DUMPCMD.search(LINE):
			SBD_PATH = LINE.split()[IDX_PATH].strip()
			DUMP_FOUND = True

#	print "SBD_LIST Size = " + str(len(SBD_LIST))
#	print "SBD_LIST = " + str(SBD_LIST) + "\n"
	return SBD_LIST

def getClusterConfig():
	IDX_KEY = 0
	IDX_VALUE = 1
	CLUSTER = {}
	FILE_OPEN = 'ha.txt'
	CONTENT = {}
	inBootStrap = False
	if Core.getSection(FILE_OPEN, 'cibadmin -Q', CONTENT):
		for LINE in CONTENT:
			if inBootStrap:
				if "</cluster_property_set>" in CONTENT[LINE]:
					inBootStrap = False
					break
				elif "<nvpair" in CONTENT[LINE]:
					PARTS = CONTENT[LINE].replace('"', '').strip().split()
					print "cibadmin PARTS = " + str(PARTS)
					KEY = ''
					VALUE = ''
					for I in range(0, len(PARTS)):
						if "name" in PARTS[I].lower():
							KEY = PARTS[I].split("=")[IDX_VALUE]
						elif "value" in PARTS[I].lower():
							VALUE = re.sub('/>.*$', '', PARTS[I].split("=")[IDX_VALUE])
					CLUSTER.update({KEY:VALUE})
			elif "<cluster_property_set" in CONTENT[LINE]:
				inBootStrap = True
			elif "<cib " in CONTENT[LINE]:
				PARTS = re.sub('<cib|>', '', CONTENT[LINE]).strip().split()
				print "cibadmin PARTS = " + str(PARTS)

	print "CLUSTER Size = " + str(len(CLUSTER))
	print "CLUSTER =      " + str(CLUSTER)
	return CLUSTER

