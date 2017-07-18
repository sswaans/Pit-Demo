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
PLATFORM_MAX_HEIGHT = 15
INITIAL_HEIGHT = 0

labRoom = viz.addChild("scaledNew.osgb")
city = viz.addChild('piazza.osgb')
city.setPosition([0,-7,0])
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
riseTimerPlatform = None
platformRaised = False
platformLevel = 0

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
	
	#set initial height; later used for buffer
	global INITIAL_HEIGHT
	if INITIAL_HEIGHT == 0:
		INITIAL_HEIGHT = viz.MainView.getPosition()[1]
	
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
	
	floorCorner1.visible(viz.OFF)
	floorCorner2.visible(viz.OFF)
	floorCorner3.visible(viz.OFF)
	floorCorner4.visible(viz.OFF)

	yield viztask.waitActionEnd(floorCorner1, moveAction)
	
	global checkForFallTimer
	checkForFallTimer = vizact.ontimer(0, checkForFall)
	print 'NUMBER 1'


def openCeiling():
	leftLights = labRoom.getTransform("LightsLeft")
	rightLights = labRoom.getTransform("LightsRight")
	leftPiece = labRoom.getTransform("RoofLeft")
	rightPiece = labRoom.getTransform("roofRight")

	leftPiece.addAction(vizact.spin(0,0,1,20,10.5))
	rightPiece.addAction(vizact.spin(0,0,1,20,10.5))

	
def checkForFall():
	userOnPlank = checkUserOnPlank()
	userOnPlatform = checkUserOnPlatform()
	userOnSurroundingGround = checkUserOnSurroundingGround()
	
	if platformRaised and not checkUserOnPlatform():
		if platformLevel is not 0 and not userOnPlank:
			checkForFallTimer.setEnabled(viz.OFF)
			print 'something went wrong with the platforms'
			makeUserFall()
			return
		
	if (not floorOpened) or userOnPlatform or userOnPlank or userOnSurroundingGround:
		return
	# Floor is open and user is not on plank or surrounding ground, so user should fall
	checkForFallTimer.setEnabled(viz.OFF)
	print 'something went wrong with the normal'
	makeUserFall()
	
def checkUserOnPlatform():
	headLoc = viz.MainView
	rightFootOnPlatform = isOnObject(rightFootTracker,labRoom.getChild('Platform'))
	leftFootOnPlatform = isOnObject(leftFootTracker,labRoom.getChild('Platform'))

	headOnPlatform = isOnObject(headLoc, labRoom.getChild('Platform'))
	if headOnPlatform:
		print 'on Platform'
	return headOnPlatform


	
def checkUserOnPlank():
	rightFootOnPlank = isOnObject(rightFootTracker,labRoom.getChild('Plank'))
	leftFootOnPlank = isOnObject(leftFootTracker,labRoom.getChild('Plank'))
	
	headLoc = viz.MainView
	headOnPlank = isOnObject(headLoc, labRoom.getChild('Plank'))
#	return ((rightFootOnPlank or rightFootOnPlatform) or (leftFootOnPlank or leftFootOnPlatform)) and (headOnPlank or headOnPlatform)
	return headOnPlank

	
def checkUserOnSurroundingGround():
	rightFootOnGround = not isAboveObject(rightFootTracker,labRoom.getChild('pit'))	
	leftFootOnGround = not isAboveObject(leftFootTracker,labRoom.getChild('pit'))
	headOnGround = not isAboveObject(viz.MainView, labRoom.getChild('pit'))
	#return (rightFootOnGround or leftFootOnGround) and headOnGround
	return headOnGround

def isOnObject(aboveObject, belowObject):
	boundingBox = belowObject.getBoundingBox()
	buffer = INITIAL_HEIGHT 

	if isAboveObject(aboveObject, belowObject):
		if aboveObject.getPosition()[1] > boundingBox.ymax and aboveObject.getPosition()[1] < boundingBox.ymax+buffer:
			return True
		
	return False
	
def isAboveObject(aboveObject, belowObject):
	boundingBox = belowObject.getBoundingBox()

	if aboveObject.getPosition()[0] >= boundingBox.xmin and aboveObject.getPosition()[0] <= boundingBox.xmax:
		if aboveObject.getPosition()[2] >= boundingBox.zmin and aboveObject.getPosition()[2] <= boundingBox.zmax:
				return True
	return False
	
def checkFallingOnObject():
	global checkForFallTimer
	userOnPlank = checkUserOnPlank()
	userOnPlatform = checkUserOnPlatform()
	userOnSurroundingGround = checkUserOnSurroundingGround()
	
	if userOnPlank:
		print 'plank'
	if userOnSurroundingGround:
		print 'surroundingGround'
	if userOnPlatform: 
		print 'platform'
	
	
	if userOnPlank or userOnPlatform or userOnSurroundingGround:
		fallTimer.setEnabled(viz.OFF)
		THUD_SOUND.play()
		collidingObjectTimer.setEnabled(viz.OFF)
		
		if not checkForFallTimer.getEnabled():
			checkForFallTimer = vizact.ontimer(0, checkForFall)
	
	
def makeUserFall():
	pitBoundingBox = labRoom.getChild('pit').getBoundingBox()
	curHeight = viz.MainView.getPosition()[1]
	
	global distanceToFall, velocity, totalDistanceFallen
	distanceToFall = -pitBoundingBox.ymin + curHeight - INITIAL_HEIGHT
	velocity = 0.0
	totalDistanceFallen = 0.0
	
	global fallTimer, collidingObjectTimer
	fallTimer = vizact.ontimer(0, updateFallPosition)
	collidingObjectTimer = vizact.ontimer(.05, checkFallingOnObject)
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
		collidingObjectTimer.setEnabled(viz.OFF)
		#print "THUD"
		
	# User hasn't hit the floor yet
	navigationNode.setPosition(nextPosition)
	totalDistanceFallen += fallDistance
	

def raisePit():
	pitFloor = labRoom.getChild("PitFloor")
	timeToRaisePit = (-pitFloor.getBoundingBox().ymax) / RAISE_PIT_VELOCITY
	pitFloor.addAction(vizact.move(0,pitFloor.getBoundingBox().ymax,0, timeToRaisePit))
	
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
	
def lowerPlatform():
		
	global platformLevel
	if platformLevel == -1:
		return
		
	platformLevel = platformLevel - 1
	
	platform = labRoom.getChild('Platform')
	stand = labRoom.getChild('Stand')
	pit = labRoom.getChild('PitFloor')
	viz.link(platform, stand)
	
	timeToLowerPlatform = PLATFORM_MAX_HEIGHT/RAISE_PLATFORM_VELOCITY
	platform.addAction(vizact.move([0, -0.9, 0], timeToLowerPlatform))
	
	
def raisePlatform():
	global INITIAL_HEIGHT
	if INITIAL_HEIGHT == 0:
		INITIAL_HEIGHT = viz.MainView.getPosition()[1]	
	
	global platformLevel
	global totalDistanceRisenPlatform, distanceToRisePlatform, riseTimerPlatform

	if riseTimerPlatform is not None:
		if platformLevel == 1 or riseTimerPlatform.getEnabled():
			return
	
	platformLevel = platformLevel + 1
	
	
	platform = labRoom.getChild('Platform')
	stand = labRoom.getChild('Stand')
	mainview = viz.MainView
	viz.link(platform, stand)
	
	timeToRaisePlatform = PLATFORM_MAX_HEIGHT / RAISE_PLATFORM_VELOCITY
	platform.addAction(vizact.move(0, .9, 0, timeToRaisePlatform))
	
	totalDistanceRisenPlatform = 0.0
	distanceToRisePlatform = 6.75
	
	#If the user is on the platform, and not already checking for fall, check for fall.
	if platform.getPosition()[1] < mainview.getPosition()[1] and isOnObject(mainview, platform):
		riseTimerPlatform = vizact.ontimer(0, updateRisePositionPlatform)
		
		global platformRaised
		platformRaised = True
		
		global checkForFallTimer
		if not checkForFallTimer.getEnabled():
			checkForFallTimer = vizact.ontimer(0, checkForFall)
	
def updateRisePositionPlatform():
	global totalDistanceRisenPlatform
	global checkForFallTimer
	dt = viz.getFrameElapsed()
	riseDistance = .9 * dt
	curPosition = navigationNode.getPosition()
	nextPosition = [curPosition[0], curPosition[1] + riseDistance, curPosition[2]]
		
	#if user fell while platform was rising, stop user from rising
	if not checkForFallTimer.getEnabled():
		riseTimerPlatform.setEnabled(viz.OFF)

	
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

view = viz.MainView	
	
vizact.onkeydown("f", viztask.schedule,openFloor)
vizact.onkeydown("q", openCeiling)
vizact.onkeydown("r", raisePit)
vizact.onkeydown("e", raisePlatform)
vizact.onkeydown("g", lowerPlatform)