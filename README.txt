12.07.2017 - Edward C. (MorningOwl)
This project was created for the Raspberry Pi and the PiCamera module. The idea is to
create a camera monitoring system with a user interface. There is a streaming feature
that lets the user watch a video stream from the application. You can also record
the video. A new video gets recorded every set interval (will be able to configure later,
an hour for as hard-coded).

Requirements:
1. Raspberry Pi 3 (should be able to work on any)
2. PiCamera (NoIR highly recommended for low light and IR light implementations for night vision)
3. Python 3.6 (should be able to run 3.x)
4. picamera - library supporting PiCamera module
5. OpenCV - robust open-source library for image processing, 
	     see https://www.pyimagesearch.com/2015/07/20/install-opencv-3-0-and-python-3-4-on-ubuntu/
6. PIL/Pillow - a python imaging library that adds support for opening, manipulating, 
                and saving many different image file formats
7. MP4Box - a software that wraps h264 files that the picamera records in MP4 format

More info:
I highly recommend reading PyImageSearch (http://pyimagesearch.com/) tutorials and blogs.
The author, Adrian Rosebrock, is an amazing image processing expert and a lot of my work
were based from my learning from his site. He covers a wide range of OpenCV topics
and other interesting fields like deep machine learning.

Future implementation:
I am currently looking for ways to implement an external source of IR lighting for night
vision for the NoIR Camera. I will also implement other modules such as temperature
and humidity reading for a full home monitoring system. They will be projects 
that will be implemented in on top of this.