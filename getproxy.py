import urllib
import string
import re

def gethostfromurl(url):
	req=urllib.urlopen(url)
	s=req.read()
	list = s.split('\n')
	hostlist = []

	ip_str = 0
	reip = re.compile('\d+\.\d+\.\d+\.\d+')
	report = re.compile('\d+')
	for host in list:
		mip = 0
		mport = 0
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
	
def savelisttofile(list,filepath):
	try:
		f = open(filepath,'w')
	except:
		return
	for ip,port in list:
		f.write('%s:%d\n'%(ip,port))
	f.close()

s_urls = [
		'http://pachong.org',
		'http://www.proxy360.cn/'
		]

s_savefile = 'proxylist.txt'

def getproxy():
	global s_urls,s_savefile
	list = []
	for url in s_urls:
		print 'read:',url,
		hostlist = gethostfromurl(url)
		print len(hostlist),'hosts'
		list.extend(hostlist)
	print 'total:',len(list),'hosts'
	savelisttofile(list,s_savefile)

if __name__=='__main__':
	getproxy()
