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
	def __init__(self):
		#strange python behaviour where using the parameters didn't work so we set them here :)
		self.midoMessageOn = mido.Message('note_on', note=36, velocity=100)
		self.midoMessageOff = mido.Message('note_off', note=36)

	def get_note(self):
		return self.midoMessageOn.note

	def get_velocity(self):
		return self.midoMessageOn.velocity

	def set_note(self, note):
		self.midoMessageOn.note = note
		self.midoMessageOff.note = note

	def set_note_from_string(self, noteStr):
		note = list(sharpsList.values()).index(noteStr)
		self.midoMessageOn.note = note
		self.midoMessageOff.note = note

	def set_velocity(self, velocity):
		self.midoMessageOn.velocity = velocity
		self.midoMessageOff.velocity = velocity

	def set_time(self, time):
		self.midoMessageOn.time = time

	def set_channel(self, channel):
		#not used currently
		self.midoMessageOn.channel = channel
		self.midoMessageOff.channel = channel

class midiControlChange(midiAction):
	def __init__(self, midoMessageOn=mido.Message('control_change', control=1, value=100), midoMessageOff=mido.Message('control_change', control=1, value=0)):
		self.midoMessageOn = midoMessageOn
		self.midoMessageOff = midoMessageOff

	def set_control(self, control):
		self.midoMessageOn.control = control
		self.midoMessageOff.control = control

	def set_value(self, value):
		self.midoMessageOn.value = value
		self.midoMessageOff.value = value

	def set_time(self, time):
		self.midoMessageOn.time = time

	def set_channel(self, channel):
		#not used currently
		self.midoMessageOn.channel = channel
		self.midoMessageOff.channel = channel

#will automate in future lol
sharpsList = {}
for i in range(9): #9octaves
	sharpsList[0+(12*i)] = ('C ' + str(i+1))
	sharpsList[1+(12*i)] = ('C#' + str(i+1))
	sharpsList[2+(12*i)] = ('D ' + str(i+1))
	sharpsList[3+(12*i)] = ('D#' + str(i+1))
	sharpsList[4+(12*i)] = ('E ' + str(i+1))
	sharpsList[5+(12*i)] = ('F ' + str(i+1))
	sharpsList[6+(12*i)] = ('F#' + str(i+1))
	sharpsList[7+(12*i)] = ('G ' + str(i+1))
	sharpsList[8+(12*i)] = ('G#' + str(i+1))
	sharpsList[9+(12*i)] = ('A ' + str(i+1))
	sharpsList[10+(12*i)] = ('A#' + str(i+1))
	sharpsList[11+(12*i)] = ('B ' + str(i+1))