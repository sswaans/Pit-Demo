import viz
import vizact
import oculus
import vizconnect
import vizfx

DEBUG = False
PPT1 = True

viz.setOption('viz.glFinish', 1)
viz.setMultiSample(8)

if PPT1: 
	vizconnect.go('vizconnect_config_DK2_mirror_PPT1_nonOH.py')
	viz.window.setSize(1900,1000)
	import vizsonic
	vizsonic.setReverb(6.0, 0.2, 0.5, 0.9, 0.0)
	vizsonic.setSimulatedRoomRadius(6.5,4.5)
	
else:
	vizconnect.go('vizconnect_mobile_keyboard.py')

viz.MainView.getHeadLight().disable()

if DEBUG:
	world = vizfx.addChild('dojo.osgb')
	viz.setDebugSound3D(viz.ON)
else:
	print 'Loading lab room model, this might take a while...'
	world = vizfx.addChild('labroomTest.osgb')
	#Adjust these 
	world.setScale([80,80,80])
	#world.setPosition([-0.4,0,-0.4])

	vizfx.setAmbientColor( [.4,.4,.4] )
	
	viz.mouse.setTrap(viz.ON) 
	viz.mouse.setVisible(viz.OFF)