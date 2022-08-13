from .midiManager import midiNote, midiControlChange, midiManager

class ButtonAction():
	def __init__(self, inputIndex=99, midiPort=2, actionType=0, previousState=False, midiParameterValue=100, isMuted=False):

		self.inputIndex = inputIndex
		self.midiPortIndex = midiPort
		self.midiPortName = midiManager.get_output_list(self)[len(midiManager.get_output_list(self))-1]
		self.midiPortOpenPortsIndex = 0 #could be an issue setting this to 0
		self.actionType = actionType
		self.previousState = previousState
		self.midiParameterValue = midiParameterValue
		self.isMuted = isMuted		
		#print("test "+ str(self.midiPort))
		#self.midiPort = mido.open_output(get_output_list()[self.midiPortIndex])
		if (actionType == 0):
			self.midiAction = midiNote()
		elif (actionType == 1):
			self.midiAction = midiControlChange()

	def get_midiAction(self):
		return self.midiAction
	
	def set_mute(self, newState):
		self.isMuted = newState

	def set_midiAction(self, newState):
		if (newState == 0):
			self.midiAction = midiNote()
		elif (newState == 1):
			self.midiAction = midiControlChange()

	def set_midiPort(self, newState):
		self.midiPortName = midiManager.get_output_list(self)[newState]

	def set_midiPortOpenPortsIndex(self, newState):
		self.midiPortOpenPortsIndex = newState

	def set_previousState(self, newState):
		self.previousState = newState

	def set_midiParameterValue(self, newState):
		self.midiParameterValue = newState


def get_actionType_list():
	return ['Midi Note', 'Control Change']

