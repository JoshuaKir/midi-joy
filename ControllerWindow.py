from PyQt6.QtWidgets import QApplication, QVBoxLayout, QGridLayout, QWidget, QSizePolicy, \
    QComboBox, QCheckBox, QSpinBox, QSpacerItem, QFrame, QMenuBar, QFileDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
import mido
import time
import os
from midi_and_controller import game_inputs as game
from midi_and_controller import InputButton as inputs
from midi_and_controller import midiManager
from ui_elements import midi_joy_style as mjs
import pickle

globalButtonActionList = []
globalAxisActionList = []
gameManager = game.GameManager()
joyDown = gameManager.get_joy_down_type()
joyUp = gameManager.get_joy_up_type()
axisMotion = gameManager.get_axis_motion_type()
controllerCount = gameManager.get_controllers().get_count()

for controllerID in range(controllerCount):
    #controller->button->action
    globalButtonActionList.append([])
    globalAxisActionList.append([])
mm = midiManager.midiManager()
start = time.time()
end = time.time()

class ControllerWindow(QWidget):

    def __init__(self, controllerName, controllerID, controllerGUID):
        super().__init__()
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.controller = controllerName
        self.isClosed = False
        self.axisAnimationArray = []
        self.currentFrameAnimationArray = []
        self.lastFrameAnimationArray = []
        self.layout = QVBoxLayout()
        self.setWindowTitle("Midi Joy: "+ self.controller)
        self.controllerID = controllerID
        self.actionWindows = []
        self.controllerAxes = []
        self.controllerButtons = []
        self.midiActions = []
        colorArray = mjs.colorArray
        axes, buttons = gameManager.get_controller_inputs(controllerID)

        # Save action
        saveAction = QAction('&Save', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip('Create Controller Save File')
        saveAction.triggered.connect(self.save_controller_configuration)

        # Load action
        loadAction = QAction('&Load', self)
        loadAction.setShortcut('Ctrl+O')
        loadAction.setStatusTip('Load Controller Save File')
        loadAction.triggered.connect(self.load_controller_configuration)

        menuBar = QMenuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(saveAction)
        fileMenu.addAction(loadAction)
        menuBar.addMenu(fileMenu)
        self.layout.setMenuBar(menuBar)

        self.buttons = QGridLayout()
        for i in range(0, buttons):
            globalButtonActionList[controllerID].append([])
            self.controllerButtons.append(mjs.AnimatedButton("Button: " + str(i+1)))
            self.controllerButtons[i].set_animation_color(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, controller=self.controllerID, button=i: self.button_clicked(controller, button))
            rowCount = i//4
            self.buttons.addWidget(self.controllerButtons[i], rowCount, i-rowCount*4)

        self.axes = QGridLayout()
        for i in range(0, axes):
            globalAxisActionList[controllerID].append([])
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].set_animation_color(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerAxes[i].clicked.connect(lambda checked, controller=self.controllerID, axis=i: self.axis_clicked(controller, axis))
            rowCount = i%2
            self.axes.addWidget(self.controllerAxes[i], i-rowCount, rowCount)

        #Add hats and buttons
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(self.axes)
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/1.75, screenSize.height()/1.75)
        self.setLayout(self.layout)

    def button_clicked(self, controllerID, buttonID):
        self.actionWindows.append(ButtonWindow(controllerID=controllerID, buttonID=buttonID, globalActionList=globalButtonActionList[self.controllerID]))

    def axis_clicked(self, controllerID, axisID):
        self.actionWindows.append(AxisWindow(controllerID=controllerID, axisID=axisID, globalActionList=globalAxisActionList[self.controllerID]))

    def process_game_events(self, event):
        global start
        start = time.time()
        # newButtons = set(currentButtonIDs).difference(lastFrameButtonIDs) #sets are faster
        if (event.joy == self.controllerID):
            if (event.type == joyDown):
                controller_button_pressed(self.controllerID, event.button)
                self.animate_button(event.button)

            elif (event.type == joyUp):
                controller_button_released(self.controllerID, event.button)

            elif (event.type == axisMotion):
                newAxis = set([event.axis]).difference(self.lastFrameAnimationArray)  # sets are faster
                if (len(newAxis) > 0 and abs(event.value) > 0.2):
                    controller_axis_activated(self.controllerID, event.axis, event.value)
                    self.animate_axis_on(event.axis)
                    self.axisAnimationArray.append(event.axis)

                else:
                    for i, axis in enumerate(self.axisAnimationArray):
                        if (abs(event.value) < 0.2 and event.axis == axis):
                            controller_axis_deactivated(self.controllerID, event.axis, event.value)
                            self.animate_axis_off(event.axis)
                            self.axisAnimationArray.pop(i)

                self.lastFrameAnimationArray = self.axisAnimationArray

    def animate_button(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()
        self.controllerButtons[button].fullAnimatedClick.start()

    def animate_axis_on(self, axis):
        self.controllerAxes[axis].secondAnimation.stop()
        self.controllerAxes[axis].firstAnimation.start()

    def animate_axis_off(self, axis):
        self.controllerAxes[axis].firstAnimation.stop()
        self.controllerAxes[axis].secondAnimation.start()

    def close_event(self, event):
        self.isClosed = True
        event.accept()

    def save_controller_configuration(self):
        #save function saves a nested array of every action for every button and axis to a file
        buttonSaveList = []
        currentDir = os.path.dirname(os.path.realpath(__file__))
        fileName = QFileDialog.getSaveFileName(None, 'Save Configuration:', currentDir, 'Midi Joy Save File (*.mj_controller)')
        if (fileName[0] == ''):
            return 1
        for i, button in enumerate(globalButtonActionList[self.controllerID]):
            buttonSaveList.append([])
            for action in button:
                buttonSaveList[i].append(action)

        axisSaveList = []
        for i, axis in enumerate(globalAxisActionList[self.controllerID]):
            axisSaveList.append([])
            for action in axis:
                axisSaveList[i].append(action)

        with open(fileName[0], 'wb') as mj_file:
            pickle.dump([buttonSaveList, axisSaveList], mj_file)

        return 0 #successful save

    def load_controller_configuration(self):
        currentDir = os.path.dirname(os.path.realpath(__file__))
        fileName = QFileDialog.getOpenFileName(None, 'Load Configuration:', currentDir, 'Midi Joy Save File (*.mj_controller)')
        if (fileName[0] == ''):
            return 1
        with open(fileName[0], 'rb') as mj_file:
            buttonList, axisList = pickle.load(mj_file)

        #remove current configuration
        for button in globalButtonActionList[self.controllerID]:
            button = []

        for button in buttonList:
            if button and button[0].inputIndex < len(globalButtonActionList[self.controllerID]):
                globalButtonActionList[self.controllerID][button[0].inputIndex] = button
                for action in button:
                    mm.open_port_with_name(action.midiPortName) #need to open ports in case not yet open

        # remove current configuration
        for axis in globalAxisActionList[self.controllerID]:
            axis = []

        for axis in axisList:
            if axis and axis[0].inputIndex < len(globalAxisActionList[self.controllerID]):
                globalAxisActionList[self.controllerID][axis[0].inputIndex] = axis
                for action in axis:
                    mm.open_port_with_name(action.midiPortName) #need to open ports in case not yet open

        return 0 #successful load

class ButtonWindow(QWidget):

    def __init__(self, controllerID, buttonID, globalActionList):
        super().__init__()
        self.setWindowTitle("Midi Joy: button: " + str(buttonID+1))
        self.globalActionList = globalActionList
        self.layout = QVBoxLayout()
        self.controllerID = controllerID
        self.buttonID = buttonID
        self.actionTest = []
        self.add_action_button_ui()
        self.update_ui()
        self.show()

    def update_ui(self):
        #add actionlist populating
        global globalButtonActionList
        for i in range(0, len(self.globalActionList[self.buttonID])):
            self.add_action_ui(i)

    def add_action_ui(self, actionID):
        global globalButtonActionList
        globalAction = self.globalActionList[self.buttonID][actionID]
        actionList = QGridLayout()
        lastCol = 1
        muteBox = self.add_mute_box(actionID)
        ###
        if (globalAction.actionType == 0):
            actionList.addWidget(self.add_note_box(actionID), actionID, 1)
        ###
        if (globalAction.actionType == 1):
            lastCol = 2
            actionList.addWidget(self.add_control_type_box(actionID), actionID, 1)
            actionList.addWidget(self.add_control_value_box(actionID), actionID, lastCol)
        ###
        midiPort = self.add_midi_port_box(actionID)
        ###
        actionType = self.add_actionType_box(actionID)
        ###
        lineSpacer = QFrame()
        lineSpacer.setFrameShape(QFrame.Shape.HLine)
        lineSpacer.setFrameShadow(QFrame.Shadow.Sunken)
        firstSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        secondSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actionList.addWidget(muteBox, actionID + 1, 0)
        actionList.addWidget(midiPort, actionID + 1, lastCol)
        actionList.addWidget(actionType, actionID, 0)
        self.layout.addLayout(actionList)
        self.layout.addItem(firstSpacer)
        self.layout.addWidget(lineSpacer)
        self.layout.addItem(secondSpacer)
        self.layout.removeWidget(self.add_actionButton)
        self.add_action_button_ui()

    def add_action_button_ui(self):
        add_actionButtonLayout = QGridLayout()
        self.add_actionButton = mjs.AnimatedButton("Add Midi Action")
        self.add_actionButton.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.add_actionButton.clicked.connect(
            lambda checked, button=self.buttonID, controller=self.controllerID: self.add_action(controller, button))
        add_actionButtonLayout.addWidget(self.add_actionButton)
        self.layout.addLayout(add_actionButtonLayout)
        self.setLayout(self.layout)

    def add_mute_box(self, actionID):
        muteBox = QCheckBox()
        muteBox.setText("Mute")
        muteBox.setToolTip("Mute")
        muteBox.stateChanged.connect(
            lambda mute, controller=self.controllerID, button=self.buttonID, actionID=actionID, muteState=muteBox:
            self.globalActionList[self.buttonID][actionID].set_mute(muteState.isChecked()))
        return muteBox

    def add_note_box(self, actionID):
        noteBox = QComboBox()
        noteList = list(midiManager.flatsList.values())
        noteBox.setToolTip("Midi Note")
        noteBox.addItems(noteList)
        noteBox.setCurrentIndex(-1)
        noteBox.setCurrentIndex(self.globalActionList[self.buttonID][actionID].midiAction.get_note())
        noteBox.activated.connect(
            lambda state, note=noteBox:
            self.globalActionList[self.buttonID][actionID].get_midiAction().set_note(note.currentIndex()))
        return noteBox

    def add_control_type_box(self, actionID):
        controlBox = QSpinBox()
        controlBox.setToolTip("Control Type")
        controlBox.setMinimum(0)
        controlBox.setMaximum(127)
        controlBox.setPrefix('Control Change Type: ')
        controlBox.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        controlBox.valueChanged.connect(
            lambda state, value=controlBox:
            self.globalActionList[self.buttonID][actionID].get_midiAction().set_control(value.value()))
        return controlBox

    def add_control_value_box(self, actionID):
        controlValue = QSpinBox()
        controlValue.setToolTip("Control Value")
        controlValue.setMinimum(0)
        controlValue.setMaximum(127)
        controlValue.setPrefix('Control Change Value: ')
        controlValue.valueChanged.connect(
            lambda state, value=controlValue:
            self.globalActionList[self.buttonID][actionID].get_midiAction().set_value(
                value.value()))
        return controlValue

    def add_midi_port_box(self, actionID):
        midiPort = QComboBox()
        midiPortList = mm.get_output_list()
        midiPort.addItems(midiPortList)
        midiPort.setCurrentIndex(midiPortList.index(self.globalActionList[self.buttonID][actionID].midiPortName))
        mm.open_port_with_name(self.globalActionList[self.buttonID][actionID].midiPortName)
        midiPort.currentIndexChanged.connect(lambda port, newAction=midiPort:
                                             self.globalActionList[self.buttonID][actionID].set_midiPort(
                                                 newAction.currentIndex()))
        midiPort.currentIndexChanged.connect(lambda port, actionID=actionID, newAction=midiPort:
                                             self.globalActionList[self.buttonID][actionID].set_midiPortOpenPortsIndex(
                                                 mm.open_port_with_name(newAction.currentText())))
        return midiPort

    def add_actionType_box(self, actionID):
        actionType = QComboBox()
        actionTypeList = inputs.get_actionType_list()
        actionType.setToolTip("Midi Message Type")
        actionType.addItems(actionTypeList)
        actionType.setCurrentIndex(self.globalActionList[self.buttonID][actionID].actionType)
        actionType.currentIndexChanged.connect(
            lambda type, action=self.globalActionList[self.buttonID][actionID], controller=self.controllerID, button=self.buttonID, newAction=actionType:
            self.control_change(action, controller, button, newAction))
        return actionType

    def add_action(self, controllerID, buttonID):
        #needs to be overriden
        globalAction = self.globalActionList[buttonID]
        globalAction.append(inputs.ButtonAction(inputIndex=buttonID))
        newActionID = len(globalAction) - 1
        print(globalAction[newActionID].get_midiAction().get_note())
        portIndex = mm.open_port_with_name(globalAction[newActionID].midiPortName)
        globalAction[newActionID].set_midiPortOpenPortsIndex(portIndex)
        self.add_action_ui(newActionID)

    def control_change(self, action, controllerID, buttonID, newAction):
        action.set_midiAction(newAction.currentIndex())
        self.hide()
        self.__init__(controllerID, buttonID, self.globalActionList)

class AxisWindow(ButtonWindow):
    def __init__(self, controllerID, axisID, globalActionList):
        super().__init__(controllerID, axisID, globalActionList)
        self.setWindowTitle("Midi Joy: Axis: " + str(axisID+1))

    def add_action_ui(self, actionID):
        global globalButtonActionList
        globalAction = self.globalActionList[self.buttonID][actionID]
        actionList = QGridLayout()
        lastCol = 2
        muteBox = self.add_mute_box(actionID)
        ###
        if (globalAction.actionType == 0):
            actionList.addWidget(self.add_note_box(actionID), actionID, 1)
            actionList.addWidget(self.add_connected_button_box(actionID), actionID, lastCol)
        ###
        if (globalAction.actionType == 1):
            lastCol = 3
            actionList.addWidget(self.add_control_type_box(actionID), actionID, 1)
            actionList.addWidget(self.add_control_value_box(actionID), actionID, lastCol - 1)
            actionList.addWidget(self.add_connected_button_box(actionID), actionID, lastCol)
        ###
        midiPort = self.add_midi_port_box(actionID)
        ###
        actionType = self.add_actionType_box(actionID)
        ###
        lineSpacer = QFrame()
        lineSpacer.setFrameShape(QFrame.Shape.HLine)
        lineSpacer.setFrameShadow(QFrame.Shadow.Sunken)
        firstSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        secondSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actionList.addWidget(muteBox, actionID + 1, 0)
        actionList.addWidget(midiPort, actionID + 1, lastCol)
        actionList.addWidget(actionType, actionID, 0)
        self.layout.addLayout(actionList)
        self.layout.addItem(firstSpacer)
        self.layout.addWidget(lineSpacer)
        self.layout.addItem(secondSpacer)
        self.layout.removeWidget(self.add_actionButton)
        self.add_action_button_ui()

    def add_action(self, controllerID, buttonID):
        globalAction = self.globalActionList[buttonID]
        globalAction.append(inputs.AxisAction(inputIndex=buttonID))
        newActionID = len(globalAction) - 1
        print(globalAction[newActionID].get_midiAction().get_note())
        portIndex = mm.open_port_with_name(globalAction[newActionID].midiPortName)
        globalAction[newActionID].set_midiPortOpenPortsIndex(portIndex)
        self.add_action_ui(newActionID)

    def add_connected_button_box(self, actionID):
        buttonList = ["Button 0: Open Strum"]
        for button in range(0, len(globalButtonActionList[self.controllerID])):
            buttonList.append('Button ' + str(button + 1))  # this gives us open + all buttons
        buttonBox = QComboBox()
        buttonBox.setToolTip("Connected Button Box")
        buttonBox.addItems(buttonList)  # list of 0 -> num of buttons: 0 will be open strum (-1)
        buttonBox.setCurrentIndex(-1)
        buttonBox.setCurrentIndex(self.globalActionList[self.buttonID][actionID].get_connectedButtonIndex() + 1)
        buttonBox.activated.connect(
            lambda state, controller=controllerID, axis=self.buttonID, actionID=actionID, note=buttonBox:
            self.globalActionList[self.buttonID][actionID].set_connectedButtonIndex(
                buttonBox.currentIndex() - 1))
        return buttonBox

def get_output_list():
    return mido.get_output_names()

def controller_button_pressed(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        #print(globalButtonActionList[controllerID][buttonID])
        for action in globalButtonActionList[controllerID][buttonID]:
            #print(action.midiAction.midoMessageOn.note)
            if (not action.isMuted):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
        end = time.time()
        print(end - start)

def controller_button_released(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        for action in globalButtonActionList[controllerID][buttonID]:
            if (not action.isMuted):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)


def controller_axis_activated(controllerID, axisID, value):
    strummedNoteBool = False
    for action in globalAxisActionList[controllerID][axisID]:
        if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(controllerID)):
            strummedNoteBool = True

    for action in globalAxisActionList[controllerID][axisID]:
        if (not action.isMuted and action.actionType == 0):
            if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(controllerID)):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
                strummedNoteBool = True
            if (action.get_connectedButtonIndex() == -1 and not strummedNoteBool):
                mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)

        elif (action.actionType == 1):
            action.get_midiAction().set_value(int(abs(value) * 127))

def controller_axis_deactivated(controllerID, axisID, value):
    for action in globalAxisActionList[controllerID][axisID]:
        if (not action.isMuted):
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)