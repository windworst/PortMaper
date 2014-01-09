import urllib
import string
import re
import sys

def remove_brackets(line):
	host = ''
	flag = False
	for c in line:
		if not flag:
			if c == '<':
				flag = True
			else:
				host += c
		else:
			if c == '>':
				flag = False
				host += ' '
	return host

def gethostfrompage(page):
	list = page.split('\n')
	hostlist = []

	ip_str = 0
	reip = re.compile('\d+\.\d+\.\d+\.\d+')
	report = re.compile('\d+')
	for line in list:
		mip = 0
		mport = 0
		flag = False
		host = remove_brackets(line)

		if not ip_str:
			mip = reip.search(host)
			if mip:
				ip_str = mip.string[mip.start():mip.end()]
				mport = report.search(host[mip.end():len(host)])
		else:
			mport = report.search(host)
		if mport:
			port = string.atoi(mport.string[mport.start():mport.end()])
			addr = (ip_str,port)
			hostlist.append(addr)
			ip_str = 0
	return hostlist

def gethostfromurl(url):
	data = 0
	try:
		req=urllib.urlopen(url)
		data=req.read()
	except:
		f = open(url,'r')
		data = f.read()

	return gethostfrompage(data)
	
def savelisttofile(list,filepath):
	try:
		f = open(filepath,'w')
	except:
		return
	for ip,port in list:
		f.write('%s:%d\n'%(ip,port))
	f.close()

s_savefile = 'proxylist.txt'
s_urlfile = 'proxyurl.txt'

def getproxy():
	global s_savefile,s_urlfile
	urls = 0
	try:
		f = open(s_urlfile,'r')
		urls = f.readlines()
		print 'Reading',s_urlfile,"Success"
	except:
		print 'Error: Reading',s_urlfile
		return
	list = []
	for url in urls:
		if url[0] == '#':
			continue
		if url[-1] == '\n':
			url = url[0:-1]
		sys.stdout.write( '[+] read:%s\n'%url )
		hostlist = gethostfromurl(url)
		sys.stdout.write( '[+] get %d hosts\n'%len(hostlist))
		list.extend(hostlist)
	print '[+] total:',len(list),'hosts'
	savelisttofile(list,s_savefile)

if __name__=='__main__':
	getproxy()
