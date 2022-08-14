from PyQt6.QtWidgets import QApplication, QVBoxLayout, QGridLayout, QWidget, QSizePolicy, QComboBox, QCheckBox, QSpinBox, QSpacerItem
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup
from midi_and_controller import game_inputs as game
from midi_and_controller import InputButton as inputs
from midi_and_controller import midiManager
from ui_elements import midi_joy_style as mjs
import mido
import time

globalButtonActionList = []
globalAxisActionList = []
gameManager = game.GameManager()
joyDown = gameManager.get_joy_down_type()
joyUp = gameManager.get_joy_up_type()
axisMotion = gameManager.get_axis_motion_type()
controllerCount = gameManager.get_controllers().get_count()

for controllerID in range(controllerCount):
    #controller->button->action
    print(controllerID)
    globalButtonActionList.append([])
    globalAxisActionList.append([])
mm = midiManager.midiManager()
start = time.time()
end = time.time()

class controllerWindow(QWidget):

    def __init__(self, controllerName, controllerID, controllerGUID):
        self.controller = controllerName
        self.isClosed = False
        self.axisAnimationArray = []
        self.currentFrameAnimationArray = []
        self.lastFrameAnimationArray = []
        super().__init__()
        #self.layout = QGridLayout()
        self.layout = QVBoxLayout()
        self.setWindowTitle("Midi Joy: "+ self.controller)
        self.controllerID = controllerID
        self.actionWindows = []
        self.controllerAxes = []
        self.controllerButtons = []
        self.midiActions = []
        colorArray = mjs.colorArray
        axes,buttons = gameManager.get_controller_inputs(controllerID)
        self.buttons = QGridLayout()
        for i in range(0, buttons):
            globalButtonActionList[controllerID].append([])
            self.controllerButtons.append(mjs.AnimatedButton("Button: " + str(i+1)))
            self.controllerButtons[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, controller=self.controllerID, button=i: self.buttonClicked(controller, button))
            rowCount = i//4
            self.buttons.addWidget(self.controllerButtons[i], rowCount, i-rowCount*4)

        self.axes = QGridLayout()
        for i in range(0, axes):
            globalAxisActionList[controllerID].append([])
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerAxes[i].clicked.connect(lambda checked, controller=self.controllerID, axis=i: self.axisClicked(controller, axis))
            rowCount = i%2
            self.axes.addWidget(self.controllerAxes[i], i-rowCount, rowCount)

        #Add hats and buttons
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(self.axes)
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/1.75, screenSize.height()/1.75)
        self.setLayout(self.layout)

    def buttonClicked(self, controllerID, buttonID):
        self.actionWindows.append(ButtonWindow(controllerID=controllerID, buttonID=buttonID))

    def axisClicked(self, controllerID, axisID):
        self.actionWindows.append(AxisWindow(controllerID=controllerID, axisID=axisID))

    def process_game_events(self, events):
        global start
        start = time.time()
        # newButtons = set(currentButtonIDs).difference(lastFrameButtonIDs) #sets are faster
        for event in events:
            if (event.joy == self.controllerID):
                if (event.type == joyDown):
                    controllerButtonPressed(self.controllerID, event.button)
                    self.animateButton(event.button)

                elif (event.type == joyUp):
                    controllerButtonReleased(self.controllerID, event.button)

                elif (event.type == axisMotion):
                    newAxis = set([event.axis]).difference(self.lastFrameAnimationArray)  # sets are faster
                    if (len(newAxis) > 0 and abs(event.value) > 0.2):
                        controllerAxisActivated(self.controllerID, event.axis, event.value)
                        self.animateAxisOn(event.axis)
                        self.axisAnimationArray.append(event.axis)


                    else:
                        for i, axis in enumerate(self.axisAnimationArray):
                            if (abs(event.value) < 0.2 and event.axis == axis):
                                controllerAxisDeactivated(self.controllerID, event.axis, event.value)
                                self.animateAxisOff(event.axis)
                                self.axisAnimationArray.pop(i)

                    self.lastFrameAnimationArray = self.axisAnimationArray

    def animateButton(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()
        self.controllerButtons[button].fullAnimatedClick.start()

    def animateAxisOn(self, axis):
        self.controllerAxes[axis].secondAnimation.stop()
        self.controllerAxes[axis].firstAnimation.start()

    def animateAxisOff(self, axis):
        self.controllerAxes[axis].firstAnimation.stop()
        self.controllerAxes[axis].secondAnimation.start()

    def closeEvent(self, event):
        self.isClosed = True
        event.accept()

class ButtonWindow(QWidget):

    def __init__(self, controllerID, buttonID):
        super().__init__()
        self.setWindowTitle("Midi Joy: button: " + str(buttonID+1))
        self.layout = QVBoxLayout()
        self.actionTest = []
        #add actionlist populating
        global globalButtonActionList
        for i in range(0, len(globalButtonActionList[controllerID][buttonID])):
            globalAction = globalButtonActionList[controllerID][buttonID][i]
            lastCol = 1
            if(globalAction.inputIndex == buttonID):
                actionList = QGridLayout()
                muteBox = QCheckBox()
                muteBox.setText("Mute")
                muteBox.setToolTip("Mute")
                muteBox.stateChanged.connect(lambda mute, controller=controllerID, button=buttonID, actionID=i, muteState=muteBox: 
                    globalButtonActionList[controllerID][buttonID][actionID].set_mute(muteState.isChecked()))
                ###
                if (globalAction.actionType == 0):
                    noteBox = QComboBox()
                    noteList = list(midiManager.flatsList.values())
                    noteBox.setToolTip("Midi Note")
                    noteBox.addItems(noteList)
                    noteBox.setCurrentIndex(-1)
                    noteBox.setCurrentIndex(globalAction.midiAction.get_note())
                    noteBox.activated.connect(lambda state, controller=controllerID, button=buttonID, actionID=i, note=noteBox:
                        globalButtonActionList[controllerID][buttonID][actionID].get_midiAction().set_note(note.currentIndex()))
                    actionList.addWidget(noteBox, i, 1)
                ###
                if (globalAction.actionType == 1):
                    lastCol = 2
                    controlBox = QSpinBox()
                    controlBox.setToolTip("Control Type")
                    controlBox.setMinimum(0)
                    controlBox.setMaximum(127)
                    controlBox.setPrefix('Control Change Type: ')
                    controlBox.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
                    controlBox.valueChanged.connect(lambda state, controller=controllerID, button=buttonID, actionID=i, value=controlBox:
                        globalButtonActionList[controllerID][buttonID][actionID].get_midiAction().set_control(value.value()))
                    actionList.addWidget(controlBox, i, 1)

                    controlValue = QSpinBox()
                    controlValue.setToolTip("Control Value")
                    controlValue.setMinimum(0)
                    controlValue.setMaximum(127)
                    controlValue.setPrefix('Control Change Value: ')
                    controlValue.valueChanged.connect(
                        lambda state, controller=controllerID, button=buttonID, actionID=i, value=controlValue:
                        globalButtonActionList[controllerID][buttonID][actionID].get_midiAction().set_value(
                            value.value()))
                    actionList.addWidget(controlValue, i, lastCol)
                ###
                midiPort = QComboBox()
                midiPortList = mm.get_output_list()
                midiPort.addItems(midiPortList)
                midiPort.setCurrentIndex(midiPortList.index(globalAction.midiPortName))
                mm.open_port_with_name(globalAction.midiPortName)
                midiPort.currentIndexChanged.connect(lambda port, buttonID=buttonID, actionID=i, newAction=midiPort: 
                    globalButtonActionList[controllerID][buttonID][actionID].set_midiPort(newAction.currentIndex()))
                midiPort.currentIndexChanged.connect(lambda port, actionID=i, newAction=midiPort: 
                    globalButtonActionList[controllerID][buttonID][actionID].set_midiPortOpenPortsIndex(mm.open_port_with_name(newAction.currentText())))
                ###
                actionType = QComboBox()
                actionTypeList = inputs.get_actionType_list()
                actionType.setToolTip("Midi Message Type")
                actionType.addItems(actionTypeList)
                actionType.setCurrentIndex(globalAction.actionType)
                actionType.currentIndexChanged.connect(lambda type, action=globalAction, controller=controllerID, button=buttonID, newAction=actionType:
                    self.controlChange(action, controller, button, newAction))
                ###
                actionList.addWidget(muteBox, i+1, 0)
                actionList.addWidget(midiPort, i+1, lastCol)
                actionList.addWidget(actionType, i, 0)
                actionSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
                actionList.addItem(actionSpacer, i+2, 0)
                self.layout.addLayout(actionList)

        addActionButtonLayout = QGridLayout()
        addActionButton = mjs.AnimatedButton("Add Midi Action")
        addActionButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        addActionButton.clicked.connect(lambda checked, button=buttonID, controller=controllerID: self.addAction(controller, button))
        addActionButtonLayout.addWidget(addActionButton)
        self.layout.addLayout(addActionButtonLayout)
        screenSize = QApplication.primaryScreen().size()
        #self.setMinimumSize(screenSize.width()/3.75, screenSize.height()/3.75)
        self.setLayout(self.layout)
        self.show()

    def addAction(self, controllerID, buttonID):
        global globalButtonActionList
        globalAction = globalButtonActionList[controllerID][buttonID]
        globalAction.append(inputs.ButtonAction(inputIndex=buttonID)) #what
        print(globalAction[len(globalAction)-1].get_midiAction().get_note())
        portIndex = mm.open_port_with_name(globalAction[len(globalAction)-1].midiPortName)
        globalAction[len(globalAction)-1].set_midiPortOpenPortsIndex(portIndex)
        self.hide()
        self.__init__(controllerID, buttonID)

    def controlChange(self, action, controllerID, buttonID, newAction):
        action.set_midiAction(newAction.currentIndex())
        self.hide()
        self.__init__(controllerID, buttonID)

class AxisWindow(QWidget):
    def __init__(self, controllerID, axisID):
        super().__init__()
        self.setWindowTitle("Midi Joy: Axis: " + str(axisID+1))
        self.layout = QVBoxLayout()
        #add actionlist populating
        global globalAxisActionList
        for i in range(0, len(globalAxisActionList[controllerID][axisID])):
            globalAction = globalAxisActionList[controllerID][axisID][i]
            lastCol = 1
            if(globalAction.inputIndex == axisID):
                actionList = QGridLayout()
                muteBox = QCheckBox()
                muteBox.setText("Mute")
                muteBox.setToolTip("Mute")
                muteBox.stateChanged.connect(lambda mute, controller=controllerID, axis=axisID, actionID=i, muteState=muteBox:
                    globalAxisActionList[controllerID][axis][actionID].set_mute(muteState.isChecked()))
                ###
                lastCol = 2
                if (globalAction.actionType == 0):
                    noteBox = QComboBox()
                    noteList = list(midiManager.flatsList.values())
                    noteBox.setToolTip("Midi Note")
                    noteBox.addItems(noteList)
                    noteBox.setCurrentIndex(-1)
                    noteBox.setCurrentIndex(globalAction.midiAction.get_note())
                    noteBox.activated.connect(lambda state, controller=controllerID, axis=axisID, actionID=i, note=noteBox:
                        globalAxisActionList[controllerID][axis][actionID].get_midiAction().set_note(note.currentIndex()))
                    actionList.addWidget(noteBox, i, 1)

                    buttonList = ["Button 0: Open Strum"]
                    for button in range(0, len(globalButtonActionList[controllerID])):
                        buttonList.append('Button ' + str(button+1)) #this gives us open + all buttons
                    buttonBox = QComboBox()
                    buttonBox.setToolTip("Connected Button Box")
                    buttonBox.addItems(buttonList) #list of 0 -> num of buttons: 0 will be open strum (-1)
                    buttonBox.setCurrentIndex(-1)
                    buttonBox.setCurrentIndex(globalAction.get_connectedButtonIndex() + 1)
                    buttonBox.activated.connect(lambda state, controller=controllerID, axis=axisID, actionID=i, note=buttonBox:
                        globalAxisActionList[controllerID][axis][actionID].set_connectedButtonIndex(buttonBox.currentIndex() - 1))
                    actionList.addWidget(buttonBox, i, lastCol)
                ###
                if (globalAction.actionType == 1):
                    controlBox = QSpinBox()
                    controlBox.setToolTip("Control Type")
                    controlBox.setMinimum(0)
                    controlBox.setMaximum(127)
                    controlBox.setPrefix('Control Change Type: ')
                    controlBox.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
                    controlBox.valueChanged.connect(lambda state, controller=controllerID, axis=axisID, actionID=i, value=controlBox:
                        globalAxisActionList[controllerID][axis][actionID].get_midiAction().set_control(value.value()))
                    actionList.addWidget(controlBox, i, 1)

                    controlValue = QSpinBox()
                    controlValue.setToolTip("Control Value")
                    controlValue.setMinimum(0)
                    controlValue.setMaximum(127)
                    controlValue.setPrefix('Control Change Value: ')
                    controlValue.valueChanged.connect(
                        lambda state, controller=controllerID, axis=axisID, actionID=i, value=controlValue:
                        globalAxisActionList[controllerID][axis][actionID].get_midiAction().set_value(
                            value.value()))
                    actionList.addWidget(controlValue, i, lastCol)
                ###
                midiPort = QComboBox()
                midiPortList = mm.get_output_list()
                midiPort.addItems(midiPortList)
                midiPort.setCurrentIndex(midiPortList.index(globalAction.midiPortName))
                mm.open_port_with_name(globalAction.midiPortName)
                midiPort.currentIndexChanged.connect(lambda port, axis=axisID, actionID=i, newAction=midiPort:
                    globalAxisActionList[controllerID][axis][actionID].set_midiPort(newAction.currentIndex()))
                midiPort.currentIndexChanged.connect(lambda port, actionID=i, newAction=midiPort:
                    globalAxisActionList[controllerID][axisID][actionID].set_midiPortOpenPortsIndex(mm.open_port_with_name(newAction.currentText())))
                ###
                actionType = QComboBox()
                actionTypeList = inputs.get_actionType_list()
                actionType.setToolTip("Midi Message Type")
                actionType.addItems(actionTypeList)
                actionType.setCurrentIndex(globalAction.actionType)
                actionType.currentIndexChanged.connect(lambda type, action=globalAction, controller=controllerID, axis=axisID, newAction=actionType:
                    self.controlChange(action, controller, axis, newAction))
                ###
                actionList.addWidget(muteBox, i+1, 0)
                actionList.addWidget(midiPort, i+1, lastCol)
                actionList.addWidget(actionType, i, 0)
                actionSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
                actionList.addItem(actionSpacer, i+2, 0)
                self.layout.addLayout(actionList)

        addActionButtonLayout = QGridLayout()
        addActionButton = mjs.AnimatedButton("Add Midi Action")
        addActionButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        addActionButton.clicked.connect(lambda state, axis=axisID, controller=controllerID: self.addAction(controller, axis))
        addActionButtonLayout.addWidget(addActionButton)
        self.layout.addLayout(addActionButtonLayout)
        screenSize = QApplication.primaryScreen().size()
        #self.setMinimumSize(screenSize.width()/3.75, screenSize.height()/3.75)
        self.setLayout(self.layout)
        self.show()

    def addAction(self, controllerID, axisID):
        global globalAxisActionList
        globalAction = globalAxisActionList[controllerID][axisID]
        globalAction.append(inputs.AxisAction(inputIndex=axisID))  # what
        print(globalAction[len(globalAction) - 1].get_midiAction().get_note())
        portIndex = mm.open_port_with_name(globalAction[len(globalAction) - 1].midiPortName)
        globalAction[len(globalAction) - 1].set_midiPortOpenPortsIndex(portIndex)
        self.hide()
        self.__init__(controllerID, axisID)

    def controlChange(self, action, controllerID, axisID, newAction):
        action.set_midiAction(newAction.currentIndex())
        self.hide()
        self.__init__(controllerID, axisID)


def get_output_list():
    return mido.get_output_names()

def controllerButtonPressed(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        #print(globalButtonActionList[controllerID][buttonID])
        for action in globalButtonActionList[controllerID][buttonID]:
            #print(action.midiAction.midoMessageOn.note)
            if (not action.isMuted):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
        end = time.time()
        print(end - start)

def controllerButtonReleased(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        for action in globalButtonActionList[controllerID][buttonID]:
            if (not action.isMuted):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)


def controllerAxisActivated(controllerID, axisID, value):
    strummedNoteBool = False
    openNoteIndex = -1
    for i, action in enumerate(globalAxisActionList[controllerID][axisID]):
        # print(action.midiAction.midoMessageOn.note)
        if (not action.isMuted):
            if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(controllerID)):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
                strummedNoteBool = True
            if (action.get_connectedButtonIndex() == -1 and not action.isMuted):
                openNoteIndex = i
            if (action.actionType == 1):
                action.get_midiAction().set_value(int(abs(value) * 127))
    if (not strummedNoteBool and openNoteIndex > -1):
        action = globalAxisActionList[controllerID][axisID][openNoteIndex]
        mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
    end = time.time()

def controllerAxisDeactivated(controllerID, axisID, value):
    # if (globalButtonActionList[buttonID] != []):
    # print(globalButtonActionList[controllerID][buttonID])
    for action in globalAxisActionList[controllerID][axisID]:
        # print(action.midiAction.midoMessageOn.note)
        if (not action.isMuted):
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)