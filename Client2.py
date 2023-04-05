from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import datetime
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client2:

	SETUP_STR = 'SETUP'
	PLAY_STR = 'PLAY'
	PAUSE_STR = 'PAUSE'
	TEARDOWN_STR = 'TEARDOWN'
	FORWARD_STR = 'FORWARD'
	BACKWARD_STR = 'BACKWARD'
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	DESCRIBE = 4
	FORWARD = 5
	BACKWARD = 6

	#checkSocketIsOpen=False
	#checkPlay=False
	#isFirstPlay=False
	counter=0

	RTSP_VER = "RTSP/1.0"
	TRANSPORT = "RTP/UDP"


	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.state = self.INIT
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = f'./videos/{filename}'
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1 
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.counter = 0
		self.totalTime = 0
		self.currentTime = 0
		#static data

		self.countTotalPacket = 0
		self.timerBegin = 0
		self.timerEnd = 0
		self.timer=0
		self.bytes = 0
		self.packets = 0
		self.packetsLost = 0
		self.lastSequence = 0
		
		
	def createWidgets(self):
		"""Build GUI."""
        # # Create Setup button
		# self.setup = Button(self.master, width=20, padx=3, pady=3)
		# self.setup["text"] = "Setup"
		# self.setup["bg"] = "#ffc107"
		# self.setup["command"] = self.setupMovie
		# self.setup.grid(row=2, column=0, padx=2, pady=2)
        
        # Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play ▷"
		self.start["bg"] = "#ffc107"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=0, padx=2, pady=2)
        
        # Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause ▐ ▌"
		self.pause["bg"] = "#ffc107"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=2, column=1, padx=2, pady=2)
        
        # Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Stop ↺"
		self.teardown["bg"] = "#ffc107"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=2, column=2, padx=2, pady=2)
        
        # Create Describe button
		self.describe = Button(self.master, width=20, padx=3, pady=3)
		self.describe["text"] = "Describe ♬"
		self.describe["bg"] = "#ffc107"
		self.describe["command"] = self.describeMovie
		self.describe["state"] = "disabled"
		self.describe.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
		self.label = Label(self.master, height=30)
		self.label.grid(row=0, column=0, columnspan=5, sticky=W+E+N+S, padx=5, pady=5) 

        # Create a label to display total time of the movie
		self.totaltimeBox = Label(self.master, width=20, text="Total time: 00:00", bg= "#4CAF50")
		self.totaltimeBox.grid(row=1, column=3, columnspan=1, padx=5, pady=5)
        
		#Create a lable to display remaining time of the movie  
		self.remainTimeBox = Label(self.master, width=20, text="Remaining time: 00:00", bg="#4CAF50")
		self.remainTimeBox.grid(row=1, column=0, columnspan=1, padx=5, pady=5)

        # Create forward button
		self.forward = Button(self.master, width=20, padx=3, pady=3)
		self.forward["text"] = "▷▷"
		self.forward["bg"] = "#ffc107"
		self.forward["command"] = self.forwardMovie
		self.forward["state"] = "disabled"
		self.forward.grid(row=1, column=2, padx=2, pady=2)

        # Create backward button
		self.backward = Button(self.master, width=20, padx=3, pady=3)
		self.backward["text"] = "◁◁"
		self.backward["bg"] = "#ffc107"
		self.backward["command"] = self.backwardMovie
		self.backward["state"] = "disabled"
		self.backward.grid(row=1, column=1, padx=2, pady=2)

	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def exitClient(self):
		"""Teardown button handler."""
		self.sendRtspRequest(self.TEARDOWN)		
		#self.master.destroy() # Close the gui window
		#os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Delete the cache image from video
		for i in os.listdir():
				if i.find(CACHE_FILE_NAME) == 0:
					os.remove(i)
		time.sleep(1)
		self.state = self.INIT
		# self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.rtspSeq = 0
		self.currentTime = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.frameNbr = 0
		self.counter = 0
		self.countTotalPacket=0
		self.packets=0
		self.forward["state"] = "disabled"
		self.backward["state"] = "disabled"
		#self.checkPlay = False
		self.connectToServer()
		self.rtpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		self.label.pack_forget()
		self.label.image = ''

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.forward["state"]= "disabled"
			self.backward["state"] = "disabled"
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.INIT:
			self.setupMovie()
			# Avoid race condition
			while self.state != self.READY:
				pass
		if self.state == self.READY:
			# Create a new thread to listen for RTP packets
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
			self.forward["state"] = "normal"
			self.backward["state"] = "normal"
			self.describe["state"] = "normal"

	def forwardMovie(self):
		"""Forward button handler."""
		self.sendRtspRequest(self.FORWARD)


	def backwardMovie(self):
		"""Backward button handler"""
		self.sendRtspRequest(self.BACKWARD)
		if self.frameNbr <= 50:
			self.frameNbr = 0
		else:
			self.frameNbr -= 50

	def describeMovie(self):
		"""Describe button handler. """
		self.sendRtspRequest(self.DESCRIBE)

	def listenRtp(self):		
		"""Listen for RTP packets."""
		while True:
			try:
				print("LISTENING...")
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					if (self.frameNbr + 1 != rtpPacket.seqNum()):
						self.counter += 1

					currFrameNbr = rtpPacket.seqNum()
					print ("CURRENT SEQUENCE NUM: " + str(currFrameNbr))
					self.bytes += len(rtpPacket.getPacket())	
					self.currentTime = int(currFrameNbr * 0.05)
					
					# Update remaining time
					self.totaltimeBox.configure(text="Total time: %02d:%02d" % (self.totalTime // 60, self.totalTime % 60))
					self.remainTimeBox.configure(text="Remaining time: %02d:%02d" % ((self.totalTime - self.currentTime)// 60, (self.totalTime - self.currentTime) % 60))			

					if currFrameNbr > self.frameNbr: # Discard the late packet
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
						#StaticUpdate
						self.countTotalPacket += 1
						self.packets += 1
						self.packetsLost += currFrameNbr - self.lastSequence - 1
						
					self.lastSequence=currFrameNbr
			
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet(): 
					self.displayStatics()
					break
				
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					self.displayStatics()
					# self.checkSocketIsOpen = False
					try:
						self.rtpSocket.shutdown(socket.SHUT_RDWR)
						self.rtpSocket.close()
					except:
						pass
					break
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		# self.checkSocketIsOpen = True
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' %self.serverAddr)
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()       
			# Update RTSP sequence number.
			self.rtspSeq+=1	
			# Viet RTSP request
			request = f"SETUP {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nTRANSPORT: RTP/UDP; Client_port= {self.rtpPort}"
			# Keep track of the sent request.
			self.requestSent = self.SETUP
			# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq+=1
			# Viet RTSP request
			request = f"PLAY {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			# Keep track of the sent request.
			self.requestSent = self.PLAY
                  
            # Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq+=1	
			# Viet RTSP request
			request = f"PAUSE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			# Keep track of the sent request.
			self.requestSent = self.PAUSE
			
			# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq+=1
			# Viet RTSP request
			request = f"TEARDOWN {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			# Keep track of the sent request.
			self.requestSent = self.TEARDOWN

		elif requestCode == self.DESCRIBE:
			self.rtspSeq += 1
			request = f"DESCRIBE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			self.requestSent = self.DESCRIBE

		elif requestCode == self.FORWARD and not self.state == self.INIT:
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1
			# Viet RTSP request
			request = "%s %s %s" % (self.FORWARD_STR, self.fileName, self.RTSP_VER) + "\nCSeq: %d" % self.rtspSeq + "\nSession: %d" % self.sessionId
			# Keep track of the sent request.
			self.requestSent = self.FORWARD
		
		elif requestCode == self.BACKWARD:
            # Update RTSP sequence number.
			# Neu so luong frame truoc do khong duoc 10%, thi tra ve frame dau tien
			if self.rtspSeq <= 50:
				self.rtspSeq = 0
			else:
				self.rtspSeq = self.rtspSeq - 50
            #Viet RTSP request
			request = "%s %s %s" % (self.BACKWARD_STR, self.fileName, self.RTSP_VER) + "\nCSeq: %d" % self.rtspSeq + "\nSession: %d" % self.sessionId
            # Keep track of the sent request.
			self.requestSent = self.BACKWARD


		else:
			return	
		# Send the RTSP request using rtspSocket.
		self.rtspSocket.send(str(request).encode())
		
		print ('\nData Sent:\n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply.decode())
			
			# Close the RTSP socket upon requesting Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session		
			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.state = self.READY
						self.totalTime = float(lines[3].split(' ')[1])
						#print("Total time: ", lines)
						# Open RTP port.
						self.openRtpPort() 
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						if self.timerBegin == 0:
							self.timerBegin = time.perf_counter()
			
					elif self.requestSent == self.PAUSE:
						self.state = self.READY					
						if self.timerBegin > 0:
							self.timerEnd = time.perf_counter()
							self.timer += self.timerEnd - self.timerBegin
							self.timerBegin = 0						
						self.playEvent.set()

					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT

						self.timerEnd = time.perf_counter()
						self.timer += self.timerEnd - self.timerBegin
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1 
					elif self.requestSent == self.DESCRIBE:
                        # self.state = ...
						self.displayDescription(lines)			
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		# Create a new datagram socket to receive RTP packets from the server
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		# Set the timeout value of the socket to 0.5sec
		self.rtpSocket.settimeout(0.5)
		try:
			# Bind the socket to the address using the RTP port given by the client user.
			self.state=self.READY
			self.rtpSocket.bind(('',self.rtpPort))
		except:
			tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' %self.rtpPort)

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			##self.sendRtspRequest(self.TEARDOWN)
			self.exitClient()
			self.rtpSocket.shutdown(socket.SHUT_RDWR)
			self.rtpSocket.close()
			self.master.destroy()
		else: # When the user presses cancel, resume playing.
			self.playMovie()

	def displayStatics(self):
		totalPacket = ((self.counter) / (self.countTotalPacket)) * 100
		top1 = Toplevel()
		top1.title("Statistics")
		top1.geometry('300x170')
		Lb2 = Listbox(top1, width=80, height=20)
		Lb2.insert(1, "Current Packets No.%d " % self.frameNbr)
		Lb2.insert(2, "Total Streaming Packets: %d packets" % self.countTotalPacket)
		Lb2.insert(3, "Packets Received: %d packets" % self.packets)
		Lb2.insert(4, "Packets Lost: %d packets" % self.counter)
		Lb2.insert(5, "Packet Loss Rate: %d%%" % totalPacket)
		Lb2.insert(8, "Video Data Rate: %d bytes per second" % (self.bytes / self.timer))
		Lb2.pack()

	def displayDescription(self, lines):
		top = Toplevel()
		top.title("Description")
		top.geometry('300x180')
		Lb1 = Listbox(top, width=50, height=30)
		Lb1.insert(1, "Describe: ")
		Lb1.insert(2, "Video name: " + str(self.fileName))
		Lb1.insert(3, lines[1])
		Lb1.insert(4, lines[2])
		Lb1.insert(5, lines[3])
		Lb1.insert(6, lines[4])
		Lb1.insert(7, lines[5])
		Lb1.insert(8, lines[6])
		Lb1.insert(9, lines[7])
		Lb1.insert(10, lines[8])
		Lb1.insert(11, "Current time: " + "%02d:%02d" % (self.currentTime // 60, self.currentTime % 60))
		Lb1.pack()

	