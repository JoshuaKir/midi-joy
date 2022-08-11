import mido

class midiManager():
	#class for handling midi sends and opens
	def __init__(self):
		self.openOutputPorts = []

	def send_midi_message(self, openPortIndex, msg):
		'''
		portIndex = -1
		for i, port in enumerate(self.openOutputPorts):
			if port.name == portName:
				portIndex = i
				break
		
		if (portIndex > -1): #port exists
			if (self.openOutputPorts[portIndex].closed):
				mido.open_output(portName)
		else:
			self.openOutputPorts.append(mido.open_output(portName))
		'''	
		self.openOutputPorts[openPortIndex].send(msg)
			
	def open_port_with_name(self, portName):
		portIndex = -1
		for i, port in enumerate(self.openOutputPorts):
			if port.name == portName:
				portIndex = i
				break
		
		if (portIndex > -1): #port exists
			if (self.openOutputPorts[portIndex].closed):
				mido.open_output(portName)
				return portIndex
		else:
			self.openOutputPorts.append(mido.open_output(portName))
			return len(self.openOutputPorts)-1

	def open_port_with_widget(self, newState):
		portName = newState.currentText()
		portIndex = -1
		for i, port in enumerate(self.openOutputPorts):
			if port.name == portName:
				portIndex = i
				break
		
		if (portIndex > -1): #port exists
			if (self.openOutputPorts[portIndex].closed):
				mido.open_output(portName)
				return portIndex
		else:
			self.openOutputPorts.append(mido.open_output(portName))
			return len(self.openOutputPorts)-1

	def get_output_list(self):
		return mido.get_output_names()

class midiAction():
	#"abstract" class for midiAction because different types will have to be handled differently but have same functions
	def __init__(self, midoMessageOn=None, midoMessageOff=None):
		self.midoMessageOn = midoMessageOn
		self.midoMessageOff = midoMessageOff

	def get_on_message(self):
		return self.midoMessageOn

	def get_off_message(self):
		return self.midoMessageOff

class midiNote(midiAction):
	def __init__(self, midoMessageOn=mido.Message('note_on', note=60, velocity=100), midoMessageOff=mido.Message('note_off', note=60)):
		self.midoMessageOn = midoMessageOn
		self.midoMessageOff = midoMessageOff

	def set_note(note):
		self.midoMessageOn.note = note
		self.midoMessageOff.note = note

	def set_velocity(velocity):
		self.midoMessageOn.velocity = velocity
		self.midoMessageOff.velocity = velocity

	def set_time(time):
		self.midoMessageOn.time = time

	def set_channel(channel):
		#not used currently
		self.midoMessageOn.channel = channel
		self.midoMessageOff.channel = channel

class midiControlChange(midiAction):
	def __init__(self, midoMessageOn=mido.Message('control_change', control=1, value=100), midoMessageOff=mido.Message('control_change', control=1, value=0)):
		self.midoMessageOn = midoMessageOn
		self.midoMessageOff = midoMessageOff

	def set_control(control):
		self.midoMessageOn.control = control
		self.midoMessageOff.control = control

	def set_value(value):
		self.midoMessageOn.value = value
		self.midoMessageOff.value = value

	def set_time(time):
		self.midoMessageOn.time = time

	def set_channel(channel):
		#not used currently
		self.midoMessageOn.channel = channel
		self.midoMessageOff.channel = channel