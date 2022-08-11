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

	def send_on_message(self):
		if (not self.isMuted):
			msg = self.midiAction.get_on_message()
			self.midiPort.send(msg)

	def send_off_message(self):
		if (not self.isMuted):
			msg = self.midiAction.get_off_message()
			self.midiPort.send(msg)
	
	def set_mute(self, newState):
		self.isMuted = newState

	def set_midiAction(self, newState):
		#cursed, but had to send the whole pyqt widget
		#this is because at time of onIndexChanged, the widget does not update
		#might be unreliable
		self.actionType = newState.currentIndex()
		if (newState.currentIndex() == 0):
			self.midiAction = midiNote()
		elif (newState.currentIndex() == 1):
			self.midiAction = midiControlChange()

	def set_midiPort(self, newState):
		#see set_midiAction
		self.midiPort = newState.currentIndex()
		self.midiPortName = midiManager.get_output_list(self)[self.midiPort]

	def set_midiPortOpenPortsIndex(self, newState):
		#see set_midiAction
		self.midiPortOpenPortsIndex = newState

	def set_previousState(self, newState):
		self.previousState = newState

	def set_midiParameterValue(self, newState):
		self.midiParameterValue = newState


def get_actionType_list():
	return ['Midi Note', 'Control Change']

