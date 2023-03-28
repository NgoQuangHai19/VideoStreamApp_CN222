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

	checkSocketIsOpen = False
	isFirstPlay = False
	counter = 0
	
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.currentTime = 0
		self.frameNbr = 0
		self.totalTime = 0
		self.isForward = False
		self.isBackward = False
		self.createWidgets()

		#static data

		self.countTotalPacket = 0
		self.timerBegin = 0
		self.timerEnd = 0
		self.timer=0
		self.bytes = 0
		self.packets = 0
		self.packetsLost = 0
		self.lastSequence = 0
		self.totalJitter = 0
		self.arrivalTimeofPreviousPacket = 0
		self.lastPacketSpacing = 0
		
	def createWidgets(self):
		"""Build GUI."""
		# Create Setup button
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["bg"] = "#ffc107"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=2, column=0, padx=2, pady=2)
		
		# Create Play button		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "▷"
		self.start["bg"] = "#ffc107"
		self.start["command"] = self.playMovie
		self.start.grid(row=2, column=1, padx=2, pady=2)
		
		# Create Pause button			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "▐ ▌"
		self.pause["bg"] = "#ffc107"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=2, column=2, padx=2, pady=2)
		
		# Create Teardown button
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "↺"
		self.teardown["bg"] = "#ffc107"
		self.teardown["command"] =  self.resetMovie
		self.teardown.grid(row=2, column=3, padx=2, pady=2)

		# Create Describe button
		self.describe = Button(self.master, width=20, padx=3, pady=3)
		self.describe["text"] = "Describe ♬"
		self.describe["bg"] = "#ffc107"
		self.describe["command"] = self.describeMovie
		self.describe.grid(row=2, column=4, padx=2, pady=2)
		
		# Create forward button:
		self.forward = Button(self.master, width=20, padx=3, pady=3)
		self.forward["text"] = "▷▷"
		self.forward["bg"] = "#ffc107"
		self.forward["command"] = self.forwardMovie
		self.forward["state"] = "disabled"
		self.forward.grid(row=1, column=3, padx=2, pady=2)

		# Create backward button:
		self.backward = Button(self.master, width=20, padx=3, pady=3)
		self.backward["text"] = "◁◁"
		self.backward["bg"] = "#ffc107"
		self.backward["command"] = self.backwardMovie
		self.backward["state"] = "disabled"
		self.backward.grid(row=1, column=1, padx=2, pady=2)	

		# Create a label to display the movie
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
		
		# Create a label to display total time
		self.totalTimeBox = Label(self.master, width=20, padx=3, pady=3)
		self.totalTimeBox["text"] = "Total time: 00:00"
		self.totalTimeBox["bg"] = "#4CAF50"
		self.totalTimeBox.grid(row=1, column=0,padx=3, pady=3)

		# Create a label to display remaining time
		self.totalTimeBox = Label(self.master, width=20, padx=3, pady=3)
		self.totalTimeBox["text"] = "Remaining: 00:00"
		self.totalTimeBox["bg"] = "#4CAF50"
		self.totalTimeBox.grid(row=1, column=4,padx=2, pady=2)
	
	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	def resetMovie(self):
		"""Teardown button handler."""
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.TEARDOWN)
			try:
				for f in os.listdir():
					if f.find(CACHE_FILE_NAME) == 0:
						os.remove(f)
			except:
				pass
			self.forward["state"], self.backward["state"] = "disabled", "disabled"
			self.rtspSeq = 0
			self.sessionId = 0
			self.requestSent = -1
			self.teardownAcked = 0
			self.counter = 0
			self.isFirstPlay = True
			self.isForward = False
			self.isBackward = False
			self.currentTime = 0
		self.state = self.INIT

	def describeMovie(self):
		"""Describe button handler. """
		self.sendRtspRequest(self.DESCRIBE)

	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:
			self.forward["state"], self.backward["state"] = "disabled", "disabled"
			self.sendRtspRequest(self.PAUSE)
	
	def playMovie(self):
		"""Play button handler."""
		if self.state == self.READY:
			self.forward["state"] = "normal"
			self.backward["state"] = "normal"
			self.describe["state"] = "normal"
			self.state = self.PLAYING
			threading.Thread(target=self.listenRtp).start()
			self.playingEvent = threading.Event()
			self.playingEvent.clear()
			self.sendRtspRequest(self.PLAY)

	
	def forwardMovie(self):
		"""Forward button handler."""
	#TODO

	def backwardMovie(self):
		"""Backward button handler"""
	#TODO

	def listenRtp(self):		
		"""Listen for RTP packets."""
	#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
	#TODO

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		request = ""
		self.rtspSeq += 1
		match requestCode:
			case self.SETUP:
				# Create a thread
				threading.Thread(target=self.recvRtspReply).start()
				request = f"SETUP {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nTRANSPORT: RTP/UDP; Client_port= {self.rtpPort}"
			case self.PLAY:
				request = f"PLAY {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			case self.PAUSE:
				request = f"PAUSE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			case self.TEARDOWN:
				request = f"TEARDOWN {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			case self.DESCRIBE:
				request = f"DESCRIBE {self.fileName} RTSP/1.0\nCSeq: {self.rtspSeq}\nSESSION: {self.sessionId}"
			case self.FORWARD:
				pass
			case self.BACKWARD:
				# Decrease sequence number to restore the old number, because backward does not need to send rstp
				self.rtspSeq -= 1
				pass
			case _:
				self.rtspSeq -= 1
				return
		self.requestSent = requestCode
		self.rtspSocket.send(request.encode())
		print('\nDu lieu gui: \n' + request)
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
	#TODO
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
	#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
    
		#-------------
		# TO COMPLETE
		#-------------
        
        
		# Create a new datagram socket to receive RTP packets from the server
	#TODO

	def displayDescription(self, lines):
		"""Display the description of movie"""
	#TODO

	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
			self.master.destroy()
			sys.exit(0)
			self.sendRtspRequest(self.TEARDOWN)
			if self.state != self.INIT and self.checkSocketIsOpen == True:
				self.rtpSocket.shutdown(socket.SHUT_RDWR)
				self.rtpSocket.close()
			

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