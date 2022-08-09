import mido

class ButtonAction():
	def __init__(self, inputIndex=99, midiAction=mido.Message('note_on', note=100, velocity=100), midiPort=0, actionType=0, previousState=False, isMuted=False):

		self.inputIndex = inputIndex
		self.midiAction = midiAction #velocity is 0-127
		self.midiPort = midiPort
		self.actionType = actionType
		self.previousState = previousState
		self.isMuted = isMuted		
		print(self.midiPort)
		#self.port = mido.open_output(self.midiPort)

	def send_message(self):
		if (not isMuted):
			msg = mido.Message(self.midiAction)
			self.port.send(msg)

	def set_mute(self, newState):
		self.isMuted = newState

	def set_midiAction(self, newState):
		#cursed, but had to send the whole pyqt widget
		#this is because at time of onIndexChanged, the widget does not update
		#might be unreliable
		self.actionType = newState.currentIndex()
		if (newState.currentIndex() == 0):
			self.midiAction = mido.Message('note_on', note=100, velocity=100)
		
		elif (newState.currentIndex() == 1):
			self.midiAction = mido.Message('pitchwheel', pitch=0)

		elif (newState.currentIndex() == 2):
			self.midiAction = mido.Message('control_change', control=1, value=100)
		print(newState)

	def set_midiPort(self, newState):
		#see set_midiAction
		self.midiPort = newState.currentIndex()

	def set_previousState(self, newState):
		self.previousState = newState

#helper functions
def get_output_list():
	return mido.get_output_names()

def get_actionType_list():
	return ['Midi Note', 'Midi Effect', 'Control Change']

