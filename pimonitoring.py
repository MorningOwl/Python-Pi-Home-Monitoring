"""
12.07.2017 - Edward C. (MorningOwl)
This project was created for the Raspberry Pi and the PiCamera module. The idea is to
create a camera monitoring system with a user interface. There is a streaming feature
that lets the user watch a video stream from the application. You can also record
the video. A new video gets recorded every set interval (will be able to configure later,
an hour for now).

Requirements:
1. Raspberry Pi 3 (should be able to work on any)
2. PiCamera (NoIR highly recommended for low light and IR light implementations for night vision)
3. Python 3.6 (should be able to run 3.x)
4. picamera - library supporting PiCamera module
5. cv2 - robust open-source library for image processing, 
	     see https://www.pyimagesearch.com/2015/07/20/install-opencv-3-0-and-python-3-4-on-ubuntu/
6. PIL/Pillow - a python imaging library that adds support for opening, manipulating, 
                and saving many different image file formats
7. MP4Box - a software that wraps h264 files that the picamera records in MP4 format

More info:
I highly recommend reading PyImageSearch (http://pyimagesearch.com/) tutorials and blogs.
The author, Adrian Rosebrock, is an amazing image processing expert a lot of my work
were based from my learning from his site. He covers a wide range of OpenCV topics
and other interesting fields like deep machine learning.

Future implementation:
I am currently looking for ways to implement an external source of IR lighting for night
vision for the NoIR Camera. I will also implement other modules such as temperature
and humidity reading for a full home monitoring system. They will be projects 
that will be implemented in on top of this.

"""

from __future__ import print_function
from threading import Thread
from tkinter import messagebox, Tk, Frame, Button, Label
from PIL import ImageTk, Image
from picamera.array import PiRGBArray
import picamera
import datetime
import time
import cv2
import os

'''
START: Utility Classes
'''

'''This is the PiCamVideoStreamer class that handles the streaming activity using a thread.'''
class PiCamVideoStreamer:
	def __init__(self, camera):
		self.camera = camera
		self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
		self.frame = None
		self.stopped = False
		self.thread = None
	
	def start(self):
		self.stopped = False
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True, splitter_port=0)
		self.thread = Thread(target=self.update, args=())
		self.thread.daemon = True
		self.thread.start()
		return self

	def update(self):
		#show time stamp		
		for f in self.stream:
			self.camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			self.frame = f.array
			self.rawCapture.truncate(0)
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				return

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True

	def is_stopped(self):
		return self.stopped

	def destroy(self):
		print('destroying')
		self.thread.join()

class PiCamVideoRecording:

	def __init__(self, camera, framerate, interval):
		self.camera = camera
		self.framerate = framerate
		self.interval = interval
		self.stopped = False
		self.thread = None

	def start(self):
		self.stopped = False
		Thread(target=self.update, args=()).start()
		return self
		
	def update(self):					
		filename = 'recording-' + datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')		
		self.camera.start_recording(filename +'.h264',format='h264',splitter_port=1)
		self.start = datetime.datetime.now()	
		while True:
			self.camera.annotate_text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')			
			total_seconds = (datetime.datetime.now() - self.start).total_seconds()
			#interval is finished
			if (abs(total_seconds) >= self.interval):
				self.camera.stop_recording()
				self.start = datetime.datetime.now()			
						
				Thread(target=lambda:self.createoutput(filename)).start()
				filename = 'recording-' + datetime.datetime.now().strftime('%Y-%m-%d-%H_%M_%S')	
				self.camera.start_recording(filename +'.h264',format='h264',splitter_port=1)
				self.start = datetime.datetime.now()
									
			if (self.stopped == True):
				self.camera.stop_recording()
				Thread(target=lambda:self.createoutput(filename)).start()
				return

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		
	def createoutput(self, filename):
		os.system('MP4Box -add '+ filename +'.h264'+':fps='+ str(self.framerate) + ' ' + filename +'.mp4')
		os.system('sudo rm ' + filename + '.h264')
		return

	def is_stopped(self):
		return self.stopped

"""A class that provides statuses for the Pi itself. Currently it provides CPU and GPU temperatures"""
class PiUtility:
	
	def __init__(self):
		self.cpu_temperature_f = ' F'
		self.cpu_temperature_c = ' C'
		self.gpu_temperature_f = ' F'
		self.gpu_temperature_c = ' C'
		
	# Set temperatures
	def set_temperatures(self):
		self.set_CPU_temperatures()
		self.set_GPU_tempuratures()
	
	# Updates ARM CPU temperature in Fahrenheit and Celsius                                
	def set_CPU_temperatures(self):
		reading = os.popen('vcgencmd measure_temp').readline()
		reading = reading.replace("temp=","").replace("'C","").strip()
		try:
			cpu = float(reading)
			self.cpu_temperature_c = str(int(cpu)) + ' C'
			cpu = cpu * 1.8 + 32
			self.cpu_temperature_f = str(int(cpu)) + ' F'
		except ValueError:
			self.cpu_temperature_c = 'N/A C'
			self.cpu_temperature_f = 'N/A F'
			return

	# Updates GPU temperature in Fahrenheit and Celsius 
	def set_GPU_tempuratures(self):
		reading = os.popen('').readline()
		try:
			gpu = float(reading)
			self.gpu_temperature_c = str(int(gpu)) + ' C'
			gpu = gpu/1000 * 1.8 + 32
			self.gpu_temperature_f = str(int(gpu)) + ' F'
		except ValueError:
			self.gpu_temperature_c = 'N/A C'
			self.gpu_temperature_f = 'N/A F'
			return

"""A class that provides a set of data for global use."""
class GlobalSettings:
	def __init__(self,camera):
		self.camera = camera #--------------------The camera object itself
		self.camera_resolution = (480,320) #------The camera resolution for video and record	
		self.camera_framerate = 32 #--------------The camera frame rate
		self.button_stream_pressed_on = False #---The boolean status if the streaming button was pressed ON
		self.pi_cam_video_streamer = None #-------The PiCamVideoStreamer object used in this session
		self.streaming_on = False #---------------The boolean status if streaming is on
		self.button_record_pressed_on = False #---The boolean status if the recording button was pressed On
		self.pi_cam_video_recording = None #------The PiCamVideoRecording object used in this session
		self.recording_on = False #---------------The boolean status if the recording button was pressed ON
		self.recording_interval = 3600 #----------The interval of recording in seconds
		self.pi_utility = None #------------------The PiUtility object used in this session
		self.app_done = False #-------------------The boolean signal if app is done
		
		self.camera.resolution = self.camera_resolution
		self.camera.framerate = self.camera_framerate
		self.camera.annotate_background = picamera.Color('black')
		self.camera.annotate_text_size = 24
	
'''
END: Utility Classes
'''
'''
START: GUI Methods
'''
"""Toggles the streaming session."""
def togglestreamer(global_settings,stream_viewer_panel,button_stream):		
	if(global_settings.button_stream_pressed_on):
		if(messagebox.askyesno('Info','Are you sure you want to end the stream?',parent=button_stream)):
			messagebox.askquestion('Info','Streaming will end.',type='ok',parent=button_stream)
			button_stream['text'] = 'ON'
			global_settings.button_stream_pressed_on = False
			stop_streaming_thread = Thread(target=stopstream, args=(global_settings,stream_viewer_panel,button_stream))
			stop_streaming_thread.daemon = True
			stop_streaming_thread.start()
	else:
		messagebox.askquestion('Info','Streaming has started.',type='ok',parent=button_stream)
		button_stream['text'] = 'OFF'
		global_settings.button_stream_pressed_on = True
		start_streaming_thread = Thread(target=startstream, args=(global_settings,stream_viewer_panel,button_stream))
		start_streaming_thread.daemon = True
		start_streaming_thread.start()

"""Toggles the recording session."""
def togglerecorder(global_settings, recording_notification, button_record):
	if(global_settings.button_record_pressed_on):
		if(messagebox.askyesno('Info','Are you sure you want to end the recording?',parent=button_stream)):
			messagebox.askquestion('Info','Recording will end.',type='ok',parent=button_stream)
			button_record['text'] = 'ON'
			global_settings.button_record_pressed_on = False
			#stop recording method
			stoprecording(global_settings, recording_notification)			
	else:
		messagebox.askquestion('Info','Recording has started.',type='ok',parent=button_stream)
		button_record['text'] = 'OFF'
		global_settings.button_record_pressed_on = True
		#start recording method
		startrecording(global_settings, recording_notification)

"""Starts the streaming activity."""
def startstream(global_settings,stream_viewer_panel,button_stream):
	camera = global_settings.camera
	resolution = global_settings.camera_resolution
	framerate = global_settings.camera_framerate
	
	#disable button until streamin_on signal is triggered
	button_stream.configure(state='disabled')
	
	#rev up the streamer
	global_settings.pi_cam_video_streamer = PiCamVideoStreamer(camera).start()
	
	#warm up the camera
	stream_viewer_panel.configure(text='Warming up camera...')
	time.sleep(3)

	#signal streaming as on and switch on button
	global_settings.streaming_on = True
	button_stream.configure(state='normal')
	
	#retrieve the frames from PiCamVideoStreamer and convert
	#to frame
	while (global_settings.pi_cam_video_streamer.is_stopped() == False):
		#grab the frame from the threaded video stream
		#and slap datetime annotation
		frame = global_settings.pi_cam_video_streamer.read()
		try:		
			image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			image = Image.fromarray(image)
			image = ImageTk.PhotoImage(image)
		
			stream_viewer_panel.configure(image = image)
			stream_viewer_panel.image = image
		except PiCameraValueError:
			pass

	#signal streaming as off
	global_settings.streaming_on = False

	return

"""Stops the streaming activity."""
def stopstream(global_settings,stream_viewer_panel,button_stream):

	global_settings.pi_cam_video_streamer.stop() #signal stream to turn off

	#wait until vs is stopped
	while(global_settings.streaming_on == True):
		continue

	stream_viewer_panel['text'] = 'Stream off.'
	stream_viewer_panel.configure(image='')
	stream_viewer_panel.image = ''
	
	return

"""Starts the recording activity."""
def startrecording(global_settings, recording_notification):
	global_settings.pi_cam_video_recording = PiCamVideoRecording(global_settings.camera,global_settings.camera_framerate, global_settings.recording_interval)
	global_settings.pi_cam_video_recording.start()
	global_settings.recording_on = True
	recording_notification.configure(text = 'Recording...')
	return
	
"""Stops the recording activity."""
def stoprecording(global_settings, recording_notification):
	global_settings.pi_cam_video_recording.stop()
	recording_notification.configure(text = '')	
	global_settings.recording_on = False
	return

"""Keeps updating the PI status"""
def trackpistatus(global_settings, label_pi_temperatures):
	global_settings.pi_utility = PiUtility()
	
	while(global_settings.app_done == False):
		global_settings.pi_utility.set_temperatures()
		temp_text = 'PI CPU: ' + global_settings.pi_utility.cpu_temperature_f + ' (' + global_settings.pi_utility.cpu_temperature_c +')' 
		label_pi_temperatures.configure(text = temp_text)

		time.sleep(5)
		
"""Actions after exit"""
def closeall(global_settings, root):
	global_settings.app_done= True
	if(global_settings.streaming_on == True):
		global_settings.pi_cam_video_streamer.stop()
		time.sleep(1) #wait for thread to close
	if(global_settings.pi_cam_video_recording != None):
		while(global_settings.pi_cam_video_recording.is_stopped() == False):
			global_settings.pi_cam_video_recording.stop()
			time.sleep(1) #wait for thread to close	

	global_settings.camera.close()
	root.destroy()
	exit(0)

'''
END: GUI Methods
'''
'''
START: Main
'''

def main():
	#set globals
	global button_stream, button_record, stream_viewer_panel

	global_settings = GlobalSettings(picamera.PiCamera())

	#creating the window and setting properties
	root = Tk()
	#root.geometry('600x400+200+200')
	root.title('Home Monitoring')
	root.resizable(0,0)

	#add and configure a frame/window
	window = Frame(root,bg='light grey')

	#add label
	label_stream = Label(window,text = 'Stream toggle:', bg='light grey')
	label_record = Label(window,text = 'Recording toggle:', bg='light grey')

	#add stream viewer
	stream_viewer_frame = Frame(window, width= 480, height= 320) 
	stream_viewer_panel = Label(stream_viewer_frame, image = None, text='Stream off.',bg = 'light grey')  	

	#add recording notification
	recording_notification = Label(window, bg='light grey', fg='red')
	
	#add PI temperature lables
	label_pi_temperatures = Label(window,bg = 'light grey', text = '', fg= 'green')

	Thread(target = lambda:trackpistatus(global_settings,label_pi_temperatures), daemon=True).start()
	
	#add buttons
	button_stream = Button(window, bg = 'white', text = 'ON')
	button_stream["command"] = lambda: togglestreamer(global_settings,stream_viewer_panel,button_stream)

	button_record = Button(window, bg = 'white', text = 'ON')
	button_record["command"] = lambda: togglerecorder(global_settings,recording_notification,button_record)

	#place items on grid
	label_stream.grid(row=0, column=0, pady=5, padx=5, ipadx = 5, sticky='w')
	label_record.grid(row=1, column=0, pady=5, padx=5, ipadx = 5, sticky='w')
	button_stream.grid(row=0, column=1, columnspan=2, pady=5, padx=5, ipadx = 60, sticky='w')
	button_record.grid(row=1, column=1, columnspan=2, pady=5, padx=5, ipadx = 60, sticky='w')
	
	stream_viewer_frame.grid(row=2, column=0, columnspan=3)
	stream_viewer_panel.grid()

	recording_notification.grid(row=3, column=0, sticky='w')
	
	label_pi_temperatures.grid(row=3, column=2, sticky='e')
	window.grid()

	#set up closing protocol
	root.protocol('WM_DELETE_WINDOW', lambda: closeall(global_settings, root))

	#start event loop    
	window.mainloop()

if(__name__ == "__main__"):
	main()
