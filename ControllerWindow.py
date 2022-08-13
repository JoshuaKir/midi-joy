from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy, QComboBox, QCheckBox, QSpinBox
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
controllerCount = gameManager.get_controllers().get_count()
for controllerID in range(controllerCount):
    #controller->button->action
    print(controllerID)
    globalButtonActionList.append([])
    globalAxisActionList.append([])
mm = midiManager.midiManager()
start = time.time()
end = time.time()

class pyGame_qthread(QObject):
    buttonPressedSignal = pyqtSignal(int)
    buttonReleasedSignal = pyqtSignal(int)

    def __init__(self, controllerID):

        self.controllerID = controllerID
        self.running = True
        super(pyGame_qthread, self).__init__()

    def pyGame(self):
        global start
        lastFrameButtonIDs = []
        while(self.running):
            start = time.time()
            button, state = gameManager.get_active_button(self.controllerID)
            #newButtons = set(currentButtonIDs).difference(lastFrameButtonIDs) #sets are faster
            if (button > -1 and state):
                controllerButtonPressed(self.controllerID, button)
                self.buttonPressedSignal.emit(button)

            if (button > -1 and not state):
                controllerButtonReleased(self.controllerID, button)
                #self.buttonReleasedSignal.emit(button)
            #time.sleep(.05)

    def quit(self):
        self.running = False

class controllerWindow(QWidget):

    def __init__(self, controllerName, controllerID, controllerGUID):
        self.controller = controllerName
        self.isClosed = False
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
            globalAxisActionList.append([])
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerAxes[i].clicked.connect(lambda checked, name=controllerName, id=i, guid=controllerGUID: self.axisClicked(name, id, guid))
            rowCount = i%2
            self.axes.addWidget(self.controllerAxes[i], i-rowCount, rowCount)

        #Add hats and buttons
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(self.axes)
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/1.75, screenSize.height()/1.75)
        self.setLayout(self.layout)

        self.thread = QThread()
        self.pyGame_thread = pyGame_qthread(controllerID)
        self.pyGame_thread.moveToThread(self.thread)
        self.pyGame_thread.buttonPressedSignal.connect(self.animateButton)
        self.thread.started.connect(self.pyGame_thread.pyGame)
        self.thread.start()

    def buttonClicked(self, controllerID, buttonID):
        self.actionWindows.append(ButtonWindow(controllerID=controllerID, buttonID=buttonID))


    def animateButton(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()

        self.controllerButtons[button].fullAnimatedClick.start()

    def closeEvent(self, event):
        self.pyGame_thread.quit()
        self.thread.quit()
        self.thread.wait()
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
            if(globalAction.inputIndex == buttonID):
                actionList = QGridLayout()
                mute = QCheckBox()
                mute.setText("Mute")
                mute.setToolTip("Mute")
                ###
                noteSpin = QSpinBox()
                noteSpin.setMinimum(0)
                noteSpin.setMaximum(127)

                noteBox = QComboBox()
                noteList = list(midiManager.sharpsList.values())
                noteBox.setToolTip("Midi Note")
                noteBox.addItems(noteList)
                #noteBox.setCurrentIndex(-1)
                noteBox.setCurrentIndex(globalAction.midiAction.get_note())
                noteBox.currentIndexChanged.connect(lambda state, controller=controllerID, button=buttonID, action=i, noteIndex=noteBox:
                    self.addMidiNoteTest(controller, button, action, noteBox.currentIndex()))
                    #print(globalAct.get_midiAction(), noteIndex.currentIndex()))
                    #globalAct.get_midiAction().set_note(noteIndex.currentIndex()))

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
                actionType.currentIndexChanged.connect(lambda action, buttonID=buttonID, actionID=i, newAction=actionType: 
                    globalAction.set_midiAction(newAction.currentIndex()))
                ###
                actionList.addWidget(mute, i, 0)
                actionList.addWidget(noteBox, i, 1)
                actionList.addWidget(midiPort, i+1, 1)
                actionList.addWidget(actionType, i+1, 0)
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

    def addMidiNoteTest(self, controllerID, buttonID, actionID, noteBoxIndex):
        global globalButtonActionList
        x = noteBoxIndex
        print(x)
        globalButtonActionList[controllerID][buttonID][actionID].get_midiAction().set_note(noteBoxIndex)

    def changeMute(self, buttonID, actionID, newState):
        pass

def get_output_list():
    return mido.get_output_names()

def controllerButtonPressed(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        #print(globalButtonActionList[controllerID][buttonID])
        for action in globalButtonActionList[controllerID][buttonID]:
            print(action.midiAction.midoMessageOn)
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
        end = time.time()
        print(end - start)

def controllerButtonReleased(controllerID, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        for action in globalButtonActionList[controllerID][buttonID]:
            #print(mm.send_midi_message(action.midiPortName, action.midiAction.midoMessageOff))
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)