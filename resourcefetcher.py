#!/usr/bin/python
# SatMapper - 2012-2013 Carlos del Ojo and John Cole.
# This code is part of the SATMAPPER software and governed by its
# license.  Please see the LICENSE file that should have been included
# as part of this package.

import os
import logging
import sys
import bz2
from lib.fastgzip import FastGzip
import urllib2
import re
import socket
import tempfile
socket.setdefaulttimeout(10)

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

class Resource:
	def __init__(self,individual,res):
		self.individual=individual	
		self.res=res
		self.linecount=0

		if re.match("^(http|ftp|https):",res,re.I):
			try: urllib2.urlopen(res).read(100)
			except: raise Exception("Resource not found: {0}".format(res))
			self.restype="URL"
		else:
			if not os.path.isfile(res):
				raise Exception("File not found: {0}".format(res))
			self.restype="FILE"

		if res.lower().endswith(".gz"):
			self.compression="GZ"
		elif res.lower().endswith(".bz2"):
			self.compression="BZ2"
		else:
			self.compression="RAW"

	def __iter__(self):
		if self.restype=="URL":
			self.tempfile=self.resfile=tempfile.NamedTemporaryFile(mode="w+b")
			resource=urllib2.urlopen(self.res)
			data=resource.read(1024*1024)
			while data:
				self.resfile.write(data)
				data=resource.read(1024*1024)
			self.resfile.seek(0)
			if self.compression=="GZ":
				self.resfile = FastGzip(fileobj=self.resfile)
			elif self.compression=="BZ2":
				self.resfile = bz2.BZ2File(self.resfile.name,mode='rb')

		else:
			if self.compression=="GZ":
				self.resfile = FastGzip(self.res)
			elif self.compression=="BZ2":
				self.resfile = bz2.BZ2File(self.res,mode='rb')
			else:
				self.resfile=open(self.res)

		self.nextobj=self.resfile.__iter__()
		return self

	def next(self):
		line=self.nextobj.next()
		if not self.linecount % 4:
			line="@"+self.individual+"@"+line
		self.linecount+=1
		return line

	def close(self):
		if self.restype=="URL":
			if self.compression!="RAW":
				self.resfile.close()
			self.tempfile.close()
		else:
			self.resfile.close()

def usage():
	print "You need to provide a file with the FastQ file input information, please read REAME.txt\nUsage: {0} resources.txt\n".format(sys.argv[0])
	sys.exit(-1)


if __name__=="__main__":

	if len(sys.argv)<2:
		usage()
	
	try:
		f=open(sys.argv[1])
	except:
		print "File {0} does not exist!".format(sys.argv[1])
		sys.exit(-1)
	
	resources=[]
	
	for i in f:
		if i.strip().startswith("#"): continue
		j=i.strip().split()
		if not j: continue
		if len(j)!=2 or "@" in j[0]:
			logging.error( "ERROR --> {0}".format(i))
			logging.error( "Invalid format, please read README.txt")
			sys.exit(-1)
		try:
			resources.append(Resource(j[0],j[1]))
		except Exception as e:
			logging.error( "Resource error:" + str(e))
		
	for i in resources:
		try:
			for k in i:
				sys.stdout.write(k)
			i.close()
		except:
			fil=open("errors.txt","a")
			fil.write("Error in resource {0} \n".format(str(i.res)))
			fil.close()
