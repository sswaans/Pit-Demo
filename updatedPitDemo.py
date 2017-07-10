import viz
import vizact
import vizshape
import viztask

import vizsonic
import steamvr

PPT_HOSTNAME = '171.64.33.43'
GRAVITY_CONSTANT = 9.8
TERMINAL_VELOCITY = 60.0
RAISE_PIT_VELOCITY = 2.0
RAISE_PLATFORM_VELOCITY = 2.0
PLATFORM_MAX_HEIGHT = 15.0

labRoom = viz.addChild("scaledTest.OSGB")
viz.go()

vizsonic.setReverb(6.0, 0.2, 0.5, 0.9, 0.0)
vizsonic.setSimulatedRoomRadius(6.5,4.5)

hmd = steamvr.HMD()
navigationNode = viz.addGroup()
viewLink = viz.link(navigationNode, viz.MainView)
viewLink.preMultLinkable(hmd.getSensor())
headLight = viz.MainView.getHeadLight() 
headLight.disable() 

vrpn = viz.add('vrpn7.dle')
rightFootTracker = vrpn.addTracker('PPT0@' + PPT_HOSTNAME,3)
leftFootTracker = vrpn.addTracker('PPT0@' + PPT_HOSTNAME,4)
if rightFootTracker.valid():
	print 'connection established with right foot tracker'
else:
	print 'right foot tracker failed'

if leftFootTracker.valid():
	print 'connection established with left foot tracker'
else:
	print 'left foot tracker failed'
	
floorOpened = False
checkForFallTimer = None

# Audio
FLOOR_OPENING_SOUND = labRoom.getChild('FloorCorner1').playsound('Resources/Audio/doorsMoving.wav')
FLOOR_OPENING_SOUND.stop()
WHOOSH_SOUND = navigationNode.playsound('Resources/Audio/swoosh.wav')
WHOOSH_SOUND.stop()
THUD_SOUND = navigationNode.playsound('Resources/Audio/body_crash.wav')
THUD_SOUND.stop()
ELEVATOR_START_SOUND = labRoom.getChild('PitFloor').playsound('Resources/Audio/elevatorStart.wav')
ELEVATOR_START_SOUND.stop()
ELEVATOR_RISE_SOUND = labRoom.getChild('PitFloor').playsound('Resources/Audio/elevatorRunning.wav')
ELEVATOR_RISE_SOUND.stop()
ELEVATOR_STOP_SOUND = labRoom.getChild('PitFloor').playsound('Resources/Audio/elevatorStop.wav')
ELEVATOR_STOP_SOUND.stop()


def openFloor():
	carpetCorner1 = labRoom.getChild("CarpetCorner1")
	floorCorner1 = labRoom.getChild("FloorCorner1")
	viz.link(floorCorner1, carpetCorner1)
	moveAction = vizact.move(0.7,0,0,time=5)
	floorCorner1.addAction(moveAction)
	
	carpetCorner2 = labRoom.getChild("CarpetCorner2")
	floorCorner2 = labRoom.getChild("FloorCorner2")
	viz.link(floorCorner2, carpetCorner2)
	floorCorner2.addAction(vizact.move(0,0,-0.7,time=5))
	
	carpetCorner3 = labRoom.getChild("CarpetCorner3")
	floorCorner3 = labRoom.getChild("FloorCorner3")
	viz.link(floorCorner3, carpetCorner3)
	floorCorner3.addAction(vizact.move(-0.7,0,0,time=5))
	
	carpetCorner4 = labRoom.getChild("CarpetCorner4")
	floorCorner4 = labRoom.getChild("FloorCorner4")
	viz.link(floorCorner4, carpetCorner4)
	floorCorner4.addAction(vizact.move(0,0,0.7,time=5))
	
	FLOOR_OPENING_SOUND.play()
	
	global floorOpened
	floorOpened = True

	yield viztask.waitActionEnd(floorCorner1, moveAction)
	global checkForFallTimer
	checkForFallTimer = vizact.ontimer(0, checkForFall)



def openCeiling():
	leftLights = labRoom.getTransform("LightsLeft")
	rightLights = labRoom.getTransform("LightsRight")
	leftPiece = labRoom.getTransform("RoofLeft")
	rightPiece = labRoom.getTransform("roofRight")

	rightPiece.addAction(vizact.spin(0,0,1,-20,10.5))
	leftPiece.addAction(vizact.spin(0,0,1,20,10.5))
	
def checkForFall():
	print 'feetpos:'
	print leftFootTracker.getPosition()
	print rightFootTracker.getPosition()
	print labRoom.getChild('Platform').getBoundingBox()
	userOnPlank = checkUserOnPlank()
	userOnSurroundingGround = checkUserOnSurroundingGround()
	if floorOpened:
		print 'floorOpened!'
	
	if userOnPlank:
		print 'UserOnPlank!'
		
	if userOnSurroundingGround:
		print 'UserOnSurroundingGround!'
	
	if (not floorOpened) or userOnPlank or userOnSurroundingGround:
		return
	# Floor is open and user is not on plank or surrounding ground, so user should fall
	checkForFallTimer.setEnabled(viz.OFF)
	makeUserFall()
	
def checkUserOnPlank():
	rightFootOnPlank = isAboveObject(rightFootTracker,labRoom.getChild('Plank'))
	rightFootOnPlatform = isAboveObject(rightFootTracker,labRoom.getChild('Platform'))
	leftFootOnPlank = isAboveObject(leftFootTracker,labRoom.getChild('Plank'))
	leftFootOnPlatform = isAboveObject(leftFootTracker,labRoom.getChild('Platform'))
	return (rightFootOnPlank or rightFootOnPlatform) or (leftFootOnPlank or leftFootOnPlatform)

	
def checkUserOnSurroundingGround():
	rightFootOnGround = not isAboveObject(rightFootTracker,labRoom.getChild('pit'))	
	leftFootOnGround = not isAboveObject(leftFootTracker,labRoom.getChild('pit'))
	return rightFootOnGround or leftFootOnGround

def isAboveObject(aboveObject, belowObject):
	boundingBox = belowObject.getBoundingBox()
	if belowObject is labRoom.getChild('pit'):
		print 'XBounds', boundingBox.xmin, boundingBox.xmax
		print 'ZBounds', boundingBox.zmin, boundingBox.zmax
	if aboveObject.getPosition()[0] >= boundingBox.xmin and aboveObject.getPosition()[0] <= boundingBox.xmax:
		if aboveObject.getPosition()[2] >= boundingBox.zmin and aboveObject.getPosition()[2] <= boundingBox.zmax:
			return True
	return False
	
def makeUserFall():
	pitBoundingBox = labRoom.getChild('pit').getBoundingBox()
	
	global distanceToFall, velocity, totalDistanceFallen
	distanceToFall = -pitBoundingBox.ymin
	velocity = 0.0
	totalDistanceFallen = 0.0
	
	global fallTimer
	fallTimer = vizact.ontimer(0, updateFallPosition)
	WHOOSH_SOUND.play()
	print "WHOOSH"


def updateFallPosition():
	global velocity, totalDistanceFallen
	dt = viz.getFrameElapsed()
	velocity = min(velocity + (GRAVITY_CONSTANT * dt),TERMINAL_VELOCITY)
	fallDistance = velocity * dt
	curPosition = navigationNode.getPosition()
	nextPosition = [curPosition[0], curPosition[1] - fallDistance, curPosition[2]]
	
	# Don't let user fall through the floor, clamp falling at floor
	if totalDistanceFallen + fallDistance > distanceToFall:
		distanceLeftToFall = distanceToFall - totalDistanceFallen
		nextPosition[1] = curPosition[1] - distanceLeftToFall
		# Stop falling
		fallTimer.setEnabled(viz.OFF)
		THUD_SOUND.play()
		print "THUD"
		
	# User hasn't hit the floor yet
	navigationNode.setPosition(nextPosition)
	totalDistanceFallen += fallDistance
	

def raisePit():
	pitFloor = labRoom.getChild("PitFloor")
	timeToRaisePit = (-pitFloor.getBoundingBox().ymax) / RAISE_PIT_VELOCITY
	pitFloor.addAction(vizact.move([0,RAISE_PIT_VELOCITY], timeToRaisePit))
	
	global totalDistanceRisenPit, distanceToRisePit, riseTimerPit
	totalDistanceRisenPit = 0.0
	distanceToRisePit = -pitFloor.getBoundingBox().ymax
	
	riseTimerPit = vizact.ontimer(0, updateRisePositionPit)
	ELEVATOR_START_SOUND.play()
	ELEVATOR_RISE_SOUND.loop()
	print "NYERRRR"

def updateRisePositionPit():
	global totalDistanceRisenPit
	dt = viz.getFrameElapsed()
	riseDistance = RAISE_PIT_VELOCITY * dt
	curPosition = navigationNode.getPosition()
	nextPosition = [curPosition[0], curPosition[1] + riseDistance, curPosition[2]]
	
	# Don't let user rise above the floor, clamp rising at floor
	if totalDistanceRisenPit + riseDistance > distanceToRisePit:
		distanceLeftToRise = distanceToRisePit - totalDistanceRisenPit
		nextPosition[1] = curPosition[1] + distanceLeftToRise
		# Stop rising
		riseTimerPit.setEnabled(viz.OFF)
		ELEVATOR_RISE_SOUND.stop()
		ELEVATOR_STOP_SOUND.play()
		print "KADUNK"
		
	# User hasn't risen all the way up yet
	navigationNode.setPosition(nextPosition)
	totalDistanceRisenPit += riseDistance
	
def raisePlatform():
	platform = labRoom.getChild('Platform')
	stand = labRoom.getChild('Stand')
	viz.link(platform, stand)
	
	timeToRaisePlatform = PLATFORM_MAX_HEIGHT / RAISE_PLATFORM_VELOCITY
	platform.addAction(vizact.move(0,RAISE_PLATFORM_VELOCITY, 0, timeToRaisePlatform))
	
	global totalDistanceRisenPlatform, distanceToRisePlatform, riseTimerPlatform
	totalDistanceRisenPlatform = 0.0
	distanceToRisePlatform = PLATFORM_MAX_HEIGHT
	
	riseTimerPlatform = vizact.ontimer(0, updateRisePositionPlatform)
	
def updateRisePositionPlatform():
	global totalDistanceRisenPlatform
	dt = viz.getFrameElapsed()
	riseDistance = RAISE_PIT_VELOCITY * dt
	curPosition = navigationNode.getPosition()
	nextPosition = [curPosition[0], curPosition[1] + riseDistance, curPosition[2]]
	
	# Don't let user rise above max height
	if totalDistanceRisenPlatform + riseDistance > distanceToRisePlatform:
		distanceLeftToRise = distanceToRisePlatform - totalDistanceRisenPlatform
		nextPosition[1] = curPosition[1] + distanceLeftToRise
		# Stop rising
		riseTimerPlatform.setEnabled(viz.OFF)
		ELEVATOR_RISE_SOUND.stop()
		ELEVATOR_STOP_SOUND.play()
		print "KADUNK"
		
	# User hasn't risen all the way up yet
	navigationNode.setPosition(nextPosition)
	totalDistanceRisenPlatform += riseDistance
	
def WSADTracking(): 
	view = viz.MainView	
	if viz.key.isDown(viz.KEY_UP):
		view.move([0,0,5*viz.elapsed()],viz.BODY_ORI)
		navigationNode.setPosition([0, 0, 5*viz.elapsed()])
		
	elif viz.key.isDown(viz.KEY_DOWN):
		view.move([0,0,-5*viz.elapsed()],viz.BODY_ORI)
		navigationNode.setPosition([0, 0, -5*viz.elapsed()])
		
	elif viz.key.isDown(viz.KEY_RIGHT):
		view.setEuler([10*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
		navigationNode.setEuler([10*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
		
	elif viz.key.isDown(viz.KEY_LEFT):
		view.setEuler([-10*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)
		navigationNode.setEuler([-10*viz.elapsed(),0,0],viz.BODY_ORI,viz.REL_PARENT)

view = viz.MainView
vizact.ontimer(0, WSADTracking)
	
	
	
vizact.onkeydown("f", viztask.schedule,openFloor)
vizact.onkeydown("q", openCeiling)
vizact.onkeydown("r", raisePit)
vizact.onkeydown("e", raisePlatform)