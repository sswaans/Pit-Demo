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

labRoom = viz.addChild("NewVersion.OSGB")
viz.go()

vizsonic.setReverb(6.0, 0.2, 0.5, 0.9, 0.0)
vizsonic.setSimulatedRoomRadius(6.5,4.5)

hmd = steamvr.HMD()
navigationNode = viz.addGroup()
viewLink = viz.link(navigationNode, viz.MainView)
viewLink.preMultLinkable(hmd.getSensor())

vrpn = viz.add('vrpn7.dle')
rightFootTracker = vrpn.addTracker('PPT0@' + PPT_HOSTNAME,5)
leftFootTracker = vrpn.addTracker('PPT0@' + PPT_HOSTNAME,4)

floorOpened = False
checkForFallTimer = None

# Audio
FLOOR_OPENING_SOUND = labRoom.getChild('FloorCorner1').playsound('Resources/Audio/doorsMoving.wav')
FLOOR_OPENING_SOUND.stop()
WHOOSH_SOUND = navigationNode.playsound('Resources/Audio/swoosh.wav')
WHOOSH_SOUND.stop()
THUD_SOUND = navigationNode.playsound('Resources/Audio/body_crash.wav')
THUD_SOUND.stop()
#ELEVATOR_START_SOUND = labRoom.getChild('pitFloor').playsound('Resources/Audio/elevatorStart.wav')
#ELEVATOR_START_SOUND.stop()
#ELEVATOR_RISE_SOUND = labRoom.getChild('pitFloor').playsound('Resources/Audio/elevatorRunning.wav')
#ELEVATOR_RISE_SOUND.stop()
#ELEVATOR_STOP_SOUND = labRoom.getChild('pitFloor').playsound('Resources/Audio/elevatorStop.wav')
#ELEVATOR_STOP_SOUND.stop()


def openFloor():
	carpetCorner1 = labRoom.getChild("CarpetCorner1")
	floorCorner1 = labRoom.getChild("FloorCorner1")
	viz.link(floorCorner1, carpetCorner1)
	moveAction = vizact.move(0.66,0,0,time=5)
	floorCorner1.addAction(moveAction)
	
	carpetCorner2 = labRoom.getChild("CarpetCorner2")
	floorCorner2 = labRoom.getChild("FloorCorner2")
	viz.link(floorCorner2, carpetCorner2)
	floorCorner2.addAction(vizact.move(0,0,-0.66,time=5))
	
	carpetCorner3 = labRoom.getChild("CarpetCorner3")
	floorCorner3 = labRoom.getChild("FloorCorner3")
	viz.link(floorCorner3, carpetCorner3)
	floorCorner3.addAction(vizact.move(-0.66,0,0,time=5))
	
	carpetCorner4 = labRoom.getChild("CarpetCorner4")
	floorCorner4 = labRoom.getChild("FloorCorner4")
	viz.link(floorCorner4, carpetCorner4)
	floorCorner4.addAction(vizact.move(0,0,0.66,time=5))
	
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
	rightPiece = labRoom.getTransform("RoofRight")

	rightPiece.addAction(vizact.spin(0,0,1,-20,10.5))
	leftPiece.addAction(vizact.spin(0,0,1,20,10.5))
	
def checkForFall():
	userOnPlank = checkUserOnPlank()
	userOnSurroundingGround = checkUserOnSurroundingGround()
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
	if aboveObject.getPosition()[0] >= boundingBox.xmin and aboveObject.getPosition()[0] <= boundingBox.xmax:
		if aboveObject.getPosition()[2] >= boundingBox.zmin and aboveObject.getPosition()[2] <= boundingBox.zmax:
			return True
	return False
	
def makeUserFall():
	pitBoundingBox = labRoom.getChild('pit').getBoundingBox()
	
	global distanceToFall, velocity, totalDistanceFallen
	distanceToFall = -pitBoundingBox.ymin - 1
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
	# Placeholder until pit floor is separated in model
#	pitFloor = labRoom.getChild("pitFloor")
	timeToRaisePit = (-pitFloor.getBoundingBox().ymax) / RAISE_PIT_VELOCITY
	pitFloor.addAction(vizact.move([0,RAISE_PIT_VELOCITY], timeToRaisePit))
	
	global totalDistanceRisen, distanceToRise
	totalDistanceRisen = 0.0
	distanceToRise = pitFloor.getBoundingBox().ymax
	
	riseTimer = vizact.ontimer(0, updateRisePosition)
#	ELEVATOR_START_SOUND.play()
	# Wait for start sound to finish somehow
	#ELEVATOR_RISE_SOUND.loop()
	print "NYERRRR"

def updateRisePosition():
	global totalDistanceRisen
	dt = viz.getFrameElapsed()
	riseDistance = RAISE_PIT_VELOCITY * dt
	curPosition = navigationNode.getPosition()
	nextPosition = [curPosition[0], curPosition[1] + riseDistance, curPosition[2]]
	
	# Don't let user rise above the floor, clamp rising at floor
	if totalDistanceRisen + riseDistance > distanceToRise:
		distanceLeftToRise = distanceToRise - totalDistanceRisen
		nextPosition[1] = curPosition[1] + distanceLeftToRise
		# Stop rising
		riseTimer.setEnabled(viz.OFF)
		#ELEVATOR_RISE_SOUND.stop()
		#ELEVATOR_STOP_SOUND.play()
		print "KADUNK"
		
	# User hasn't risen all the way up yet
	navigationNode.setPosition(nextPosition)
	totalDistanceRisen += riseDistance
	
	
vizact.onkeydown(" ", viztask.schedule,openFloor)
vizact.onkeydown("q", openCeiling)
vizact.onkeydown("w", makeUserFall)
vizact.onkeydown(viz.KEY_UP, raisePit)