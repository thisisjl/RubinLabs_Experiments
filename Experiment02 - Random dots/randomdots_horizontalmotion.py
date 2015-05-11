import os, sys

lib_path = os.path.abspath(os.path.join('..','_Libraries'))
sys.path.append(lib_path)

from rlabs_libutils import *
from rlabs_libtobii import EyetrackerBrowser, MyTobiiController             			# this is OUR library for the tobii eyetracker

from pyglet.window import Window, mouse
from pyglet.gl import *
from pyglet import clock
import time
import numpy as np


def main(
	ExpName = 'random_dots',
	num_dots=100, 
	Tau = 100, 
	haveeyetracker = 0,
	bgcolor = (0.88,0.88,0.88), 
	speed = 500,
	framerate = 60.0,
	subjectname = 'None',
	timeCurrentTrial = 10,
	dotcolor = (0,0,0)
	):
	
	# Load parameters ------------------------------------------------------------------
    if getattr(sys, 'frozen', False):                                       			# path is different
        application_path = os.path.dirname(sys.executable)                  			# if its an executable
    elif __file__:                                                          			# or a Python script,
        application_path = os.path.dirname(__file__)                        			# look for it

	screens = pyglet.window.get_platform().get_default_display().get_screens()			# get number of screens
	win = MyWindow(fullscreen = True, screen = screens[0], visible = 0)					# create window
	clockDisplay = clock.ClockDisplay(color=(1,1,1,1))                      			# to display frames per second
	clock.set_fps_limit(framerate)                                          			# set limit for frames per second
	frameMs = 1.0/framerate                                        						# manual frame rate control: frameMs is the time in ms a frame will be displayed

	parameters = {}

	# Initialize text to be shown at startup (not whown right now)
	textInstruc = "Continually report the predominant motion.\nPress the left mouse button for left-ward motion.\nPress the right mouse button for right-ward motion\n\nClick mouse-wheel to start"
	lbl_instr = pyglet.text.Label(text=textInstruc, font_name='Times New Roman', font_size=36,
		color=(0, 0, 0, 255), x = win.width/2+120, y = win.height/2, anchor_x='center', anchor_y='center', width=win.width/1, multiline=True)

	# Initialize variables for data file -----------------------------------------------
	filename_data = os.path.join(application_path, os.path.join('data',(ExpName + "-" + time.strftime("%y.%m.%d_%H.%M", time.localtime()) + "_" + subjectname + "_" + "button_press_data" + ".txt")))
	data_folder   = os.path.join(application_path, 'data')								# data folder name
	if not os.path.isdir(data_folder): os.makedirs(data_folder)                    		# if there is not a folder called 'data', create it
	
	# define the limits of the area where the dots will move ---------------------------
	liml, limr = win.width/4,  win.width - win.width/4 									# set left, liml, and right, limr, limits
	limu, limd = win.height/4, win.height - win.height/4 								# set upper, limu, down, limd, limits
	cycle      = limr - liml 															# compute cycle length

	# compute dots position: liml < x < limr -------------------------------------------
	x = np.random.rand(num_dots) * (limr - liml) + liml									# compute horizontal position, 
	y = np.random.rand(num_dots) * (limd - limu) + limu 								# compute vertical position
	z_fb = 2 * np.mod(np.random.permutation(num_dots),2) - 1 							# compute direction of movement
	age = np.random.randint(Tau, size=num_dots) 										# compute dot ages

	vertices = np.empty((x.size + y.size,), dtype=x.dtype)               				# create empty array to allocate x and y coordinates	
	dx = np.empty(z_fb.size) 															# initialize dx, to compute movement
	
	# handling events ------------------------------------------------------------------
	events_struct = []                                                      			# list that contains event that the event handler sends.
	eventcount = 0                                                          			# counter of the events

	events_handler = {                                                      			# events handler (it needs to be set to window)
	    'on_mouse_press'    : lambda e: events_struct.append(e),            			# append on_mouse_press event to events_struct
	    'on_mouse_release'  : lambda e: events_struct.append(e),}           			# append on_mouse_release event to events_struct

	events_handler_with_ET = {                                                      	# if using eyetracker, this will add
	    'on_mouse_press'    : lambda e: (events_struct.append(e), 						# to events_struct and it will also
	    	controller.myRecordEvent2(event = e)),    
	    'on_mouse_release'  : lambda e: (events_struct.append(e),						# call MyRecordEvent2 with the event
	    	controller.myRecordEvent2(event = e)),}   


    # prepare for eyetracker -----------------------------------------------------------
	if haveeyetracker:
		if not os.path.isdir('data'):                                           		# if there is not a folder called 'data',
		    os.makedirs('data')                                                 		# create it
		eyetrackeroutput   = os.path.join('data',										# eyetracker data file name
			("Randomdots" + "-" + time.strftime( 			
			"%y.%m.%d_%H.%M",
			time.localtime()) + "_" + subjectname + "_" + "eyetracker_data" + ".txt"))	#
		eb = EyetrackerBrowser()														# Create an EyetrackerBrowser
		eb.main()																		# display EyetrackerBrowser

		controller = MyTobiiController( 												# create Tobii controller
			datafilename=eyetrackeroutput, 												# pass it data file name
			parameters=parameters)       												# pass it parameters
		controller.waitForFindEyeTracker()                                  			# wait to find eyetracker
		controller.activate(controller.eyetrackers.keys()[0])               			# activate eyetracker

		controller.startTracking()                                                   	# start the eye tracking recording
		time.sleep(0.2)                                                                 # wait for the eytracker to warm up
		controller.myRecordEvent2(EventItem(name = 'TrialEvent', counter = 0, 
			timestamp = time.time(), etype = 0, eid = 'START'))

		win.events_handler = events_handler_with_ET                       				# set window events_handler with eye tracker
	else:
		win.events_handler = events_handler                               				# set window events_handler

	# Wait for go Loop ---------------------------------------------------------------------------------------------
	win.set_visible(True) 																# set window to visible
	win.set_mouse_visible(False)                                          				# set mouse to not visible
	wait = True                                                         				# wait for go condition: wait
	while wait and not win.has_exit:
		glClearColor(bgcolor[0],bgcolor[1],bgcolor[2],1)                 				# set background color
		win.clear()                                                   					# clear window
		win.dispatch_events()                                         					# dispatch window events (very important call)
	    
		lbl_instr.draw()                                            					# show instructions number 1

		last_event = win.get_last_event()                                                 	# get last event on MyWin
		if last_event and last_event.id == mouse.MIDDLE and last_event.type == 'Mouse_UP':  # if id and type match to the release of middle button,
		    wait = False                                                                    # do not wait, exit wait for go loop

		win.flip()                                                    				# flip window

	# Stimulus loop  -------------------------------------------------------------------
	timestart = time.time() 															# get time stamp for start
	while (time.time() - timestart) < timeCurrentTrial and not win.has_exit:
		glClearColor(bgcolor[0],bgcolor[1],bgcolor[2],1)                 				# set background color
		win.clear()                                                         			# clear window
		win.dispatch_events()                                               			# dispatch window events (very important call)
		timenow = time.time() 															# get time of iteration
		
		# Check if dots are dead -------------------------------------------------------
		newdots    = (age == 0) 														# to the dots whose age is zero, 
		x[newdots] = np.random.rand(np.sum(newdots)) * (limr - liml) + liml          	# compute new horizontal position
		y[newdots] = np.random.rand(np.sum(newdots)) * (limd - limu) + limu				# compute new vertical position

		# update position --------------------------------------------------------------
		dividend       = x + z_fb * (speed * (timenow - timestart))  					#
		dx[z_fb == 1]  = np.fmod(dividend[z_fb == 1], cycle) + liml 					#
		dx[z_fb == -1] = limr - np.fmod(limr - dividend[z_fb == -1], cycle) 			#
		dotxpos        = dx 															#

		# Update ages ------------------------------------------------------------------
		age          = age - 1 															# decrease age
		age[age==-1] = Tau - 1  														# resuscitate dots
		
		# Draw dots --------------------------------------------------------------------
		vertices[0::2] = dotxpos														# x coords will be in even indices
		vertices[1::2] = y																# y coords will be in odd indices
		drawpoints(vertices, color = dotcolor, size = 5)  								# draw dots

		# flip window and show fps -----------------------------------------------------
		clock.tick() 																	# to show fps
		clockDisplay.draw()                                                 			# display frames per second
		win.flip()                                                          			# flip window
		
		# manual frame control ---------------------------------------------------------
		endMs = time.time() 															# manual frame rate control: time point when frame ends.
		delaytime = frameMs - (endMs - timenow) 										# manual frame rate control: time time frame must be frozen.
		if delaytime > 0: time.sleep(delaytime)											# manual frame rate control: freeze frame


	# Stop eyetracker processes, save data and close pyglet window ------------------------------------------------------------------------
    if haveeyetracker:
        controller.stopTracking()                                               		# stop eye tracking and write output file
        controller.destroy()                                                    		# destroy controller

    write_data_file_with_parameters(filename_data, events_struct, parameters)   		# write data file, it has raw and formatted data
    
    win.close()                                                               			# close pyglet window

if __name__ == '__main__':
    main()