# -*- coding: utf-8 -*-

import socket
import select
import threading
import sys

#get incomming socket

class listener:
	def __init__(self,ip_port):
		self.s = socket.socket()
		self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.s.bind(ip_port)
		self.s.listen(100000)
		self.s.setblocking(0)

	def on_accept(self,addr):
		sys.stdout.write('[+] Listen: %s:%d Connect in\n'%addr)

	def __call__(self):
		while True:
			try:
				ac,addr = self.s.accept()
				break
			except socket.error, arg:
				errno,err_msg = arg
				if errno != 10035:
					raise socket.error(arg)
		ac.setblocking(0)
		self.on_accept(addr)
		return ac

#get connect socket

class connector:
	timeout = 5
	ip_port = 0
	def __init__(self,ip_port):
		self.ip_port = ip_port
	
	def on_connect(self,addr):
		sys.stdout.write('[+] Connect: Linking %s:%d ...\n'%addr)

	def on_connect_success(self,addr):
		sys.stdout.write('[+] Connect: %s:%d Link Success\n'%addr)

	def on_connect_failed(self,addr):
		sys.stdout.write('[-] Connect  %s:%d Link Failed\n'%addr)

	def __call__(self):
		s = socket.socket()
		s.setblocking(0)
		self.on_connect(self.ip_port)
		try:
			s.connect(self.ip_port)
		except socket.error, arg:
			errno,err_msg = arg
			if errno != 10035:
				raise socket.error(arg)
		timeout = self.timeout
		while timeout>0:
			rs,ws,es = select.select([],[s],[s],0.1)
			timeout -= 0.1
			if len(ws)>0:
				self.on_connect_success(self.ip_port)
				break
			if len(es)>0:
				self.on_connect_failed(self.ip_port)
				raise socket.error(10061,'')
		return s

#transmit data between two sockets

class socktransfer:
	buf_len = 8192
	def on_data_tran(self,sock1,sock2,data):
		ip1,port1 = sock1.getpeername()
		ip2,port2 = sock2.getpeername()
		sys.stdout.write('[+] Data: %s:%d >>> %s:%d, %d Bytes\n' %(ip1,port1,ip2,port2,len(data)) )

	def on_tran_close(self,sock1,sock2):
		ip1,port1 = sock1.getpeername()
		ip2,port2 = sock2.getpeername()
		sys.stdout.write('[-] Quit: %s:%d <-> %s:%d\n' %(ip1,port1,ip2,port2))

	def __call__(self,sock1,sock2):# return transfer result
		data1 = 0
		data2 = 0

		# recv
		try:
			data1 = sock1.recv(self.buf_len)
		except socket.error, arg:
			errno,err_msg = arg
			if errno != 10035: 
				self.on_tran_close(sock1,sock2)
				return False

		try:
			data2 = sock2.recv(self.buf_len)
		except socket.error, arg:
			errno,err_msg = arg
			if errno != 10035:
				self.on_tran_close(sock1,sock2)
				return False
		# send
		try:
			if data1:
				self.on_data_tran(sock1,sock2,data1)
				sock2.send(data1)
			if data2:
				self.on_data_tran(sock2,sock1,data2)
				sock1.send(data2)
		except socket.error:
			self.on_tran_close(sock1,sock2)
			return False
		return True

#portmaper

class portmaper(threading.Thread):
	sockgeter1 = 0
	sockgeter2 = 0
	socktransfer = socktransfer()

	still_run = 0
	list_mutex = threading.Lock()
	socks_list = []

	def __init__(self,sockgeter1,sockgeter2):
		threading.Thread.__init__(self)
		self.sockgeter1 = sockgeter1
		self.sockgeter2 = sockgeter2
		self.socks_list = []

	#start mapping
	def start(self):
		self.setDaemon(True)
		self.still_run = True
		threading.Thread.start(self)
		try:
			while self.still_run:
				sock1 = 0
				sock2 = 0

				#get socks
				try:
					sock1 = self.sockgeter1()
				except socket.error:
					continue

				try:
					sock2 = self.sockgeter2()
				except socket.error:
					sock1.close()
					continue

				#append to socks_list
				if len(self.socks_list)>0:
					self.list_mutex.acquire()

				self.socks_list.append((sock1,sock2))

				self.list_mutex.release()
		finally:
			self.still_run = False
			try:
				self.list_mutex.release()
			except:
				pass

	def run(self):
		index = 0
		sock1 = 0
		sock2 = 0

		while self.still_run:
			# get socks
			self.list_mutex.acquire()
			if len(self.socks_list)==0:
				continue #lock itself
			if index >= len(self.socks_list):
				index = 0
			sock1,sock2 = self.socks_list[index]
			try:
				self.list_mutex.release()
			except:
				pass

			#transmit data
			if self.socktransfer(sock1,sock2):
				index += 1
			else:
				sock1.close()
				sock2.close()
				del self.socks_list[index]

		#clean
		try:
			self.list_mutex.release()
		except:
			pass
		for sock1,sock2 in self.socks_list:
			sock1.close()
			sock2.close()
		self.socks_list = []

# # # # # # # # # # # # # # # # # # # #
# use function

def listen_on_port(ip_port):
	l = False
	try:
		l = listener(ip_port)
		sys.stdout.write('[+] Listen: on %s:%d Success\n' % ip_port)
	except:
		sys.stdout.write('[-] Listen: on %s:%d Failed\n' % ip_port)
	return l

def start_portmap(get1,get2):
	try:
		p = portmaper(get1,get2)
		sys.stdout.write('[+] Port Map Start\n')
		p.start()
	except KeyboardInterrupt:
		sys.stdout.write('[-] Accept Ctrl+C, Quiting...\n')
		p.join()

def getipaddr(ifname):
	# in linux
	import fcntl
	import struct
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(
        	s.fileno(),
	        0x8915,  # SIOCGIFADDR
        	struct.pack('256s', ifname[:15])
			)[20:24])

def getlocalip():
	ip_str = socket.gethostbyname(socket.gethostname())
	if '127' in ip_str >=0 :
		try:
			ip_str = getipaddr('eth0')
		except:
			try:
				ip_str = getipaddr('wlan0')
			except:
				pass
	return ip_str

def listen(port1,port2):
	localip = getlocalip()
	l1 = listen_on_port((localip,port1))
	if not l1:
		return
	l2 = listen_on_port((localip,port2))
	if not l2:
		return
	start_portmap(l1,l2)
	l1.s.close()
	l2.s.close()

def tran(port1,ip2,port2):
	localip = getlocalip()
	l = listen_on_port((localip,port1))
	if not l:
		return
	c = connector((ip2,port2))
	start_portmap(l,c)

def slave(ip1,port1,ip2,port2):
	c1 = connector((ip1,port1))
	c2 = connector((ip2,port2))
	start_portmap(c1,c2)

def help():
	print '	Port Maper v1.0'
	print 'usage: python -i me.py\n'
	print ' listen(port1,port2):\n	listen on ports,transmit connect-in socket data\n'
	print ' tran(port1,ip2,port2):\n	listen on port1, transport to ip2:port2\n'
	print ' slave(ip1,port1,ip2,port2):\n	connect to ip1:port1 & ip2:port2, transmit data\n'
	print ''
	print ' help(): call this page\n'

if __name__ == "__main__":
	help()
