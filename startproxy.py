import portmaper
import random
import string

def readaddrlist(listfile):
	print 'File',listfile,
	try:
		f = open(listfile,'r')
		print 'Read Success',
	except:
		print 'Read Failed'
		return False
	list = []
	total = 0
	for line in f.readlines():
		if line[-1] == '\n':
			line = line[0:-1]
		ip = 0
		port = 0
		addr_iter = iter(line.split(':'))
		try:
			ip = addr_iter.next()
			port = addr_iter.next()
		except:
			break

		total += 1
		port = string.atoi(port)
		list.append( (ip,port) )
	print 'Add',total,'addr'
	return list

def startproxy():
	readfile = 'proxylist.txt'
	listenport = 5555
	list = readaddrlist(readfile)
	print ''
	while list:
		ip,port = random.choice(list)
		print 'Set Proxy:%s:%d,Starting...'%(ip,port)
		portmaper.tran(listenport,ip,port)
		print 'Stopped, Enter for restart,Ctrl+C quit'
		try:
			input()
		except KeyboardInterrupt:
			break
		except:
			pass

if __name__ == '__main__':
	startproxy()
