from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy, QComboBox, QCheckBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup
from midi_and_controller import game_inputs as game
from midi_and_controller import InputButton as inputs
from midi_and_controller import midiManager
from ui_elements import midi_joy_style as mjs
import mido
import time

globalButtonActionList = []
globalAxisActionList = []
openMidiPorts = []
mm = midiManager.midiManager()
start = time.time()
end = time.time()
class pyGame_qthread(QObject):
    buttonPressedSignal = pyqtSignal(int)
    buttonReleasedSignal = pyqtSignal(int)

    def __init__(self, controllerID):

        self.controllerID = controllerID
        super(pyGame_qthread, self).__init__()

    def pyGame(self):
        lastFrameButtonIDs = []
        while(1):
            global start
            start = time.time()
            currentButtonIDs = game.get_active_buttons(self.controllerID)
            newButtons = set(currentButtonIDs).difference(lastFrameButtonIDs) #sets are faster
            for button in newButtons:
                self.buttonPressedSignal.emit(button)

            releasedButtons = set(lastFrameButtonIDs).difference(currentButtonIDs)
            for button in releasedButtons:
                self.buttonReleasedSignal.emit(button)
            
            lastFrameButtonIDs = currentButtonIDs
            time.sleep(.15)

class controllerWindow(QWidget):

    def __init__(self, controllerName, controllerID, controllerGUID):
        self.controller = controllerName
        super().__init__()
        #self.layout = QGridLayout()
        self.layout = QVBoxLayout()
        self.setWindowTitle("Midi Joy: "+ self.controller)
        self.actionWindows = []
        self.controllerAxes = []
        self.controllerButtons = []
        self.midiActions = []
        colorArray = mjs.colorArray
        axes,buttons = game.get_controller_inputs(controllerID)
        self.buttons = QGridLayout()
        for i in range(0, buttons):
            globalButtonActionList.append([])
            self.controllerButtons.append(mjs.AnimatedButton("Button: " + str(i+1)))
            self.controllerButtons[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, id=i: self.buttonClicked(id))
            rowCount = i//4
            self.buttons.addWidget(self.controllerButtons[i], rowCount, i-rowCount*4)

        self.axes = QGridLayout()
        for i in range(0, axes):
            globalAxisActionList.append([])
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Preferred)
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
        self.pyGame_thread.buttonPressedSignal.connect(self.controllerButtonPressed)
        self.pyGame_thread.buttonReleasedSignal.connect(self.controllerButtonReleased)
        self.pyGame_thread.buttonPressedSignal.connect(self.animateButton)
        self.thread.started.connect(self.pyGame_thread.pyGame)
        self.thread.start()

    def buttonClicked(self, buttonID):
        self.actionWindows.append(ButtonWindow(buttonID=buttonID))

    def controllerButtonPressed(self, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        for action in globalButtonActionList[buttonID]:
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
        end = time.time()
        print(end - start)

    def controllerButtonReleased(self, buttonID):
        #if (globalButtonActionList[buttonID] != []):
        for action in globalButtonActionList[buttonID]:
            #print(mm.send_midi_message(action.midiPortName, action.midiAction.midoMessageOff))
            mm.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)

    def animateButton(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()

        self.controllerButtons[button].fullAnimatedClick.start()

class ButtonWindow(QWidget):

    def __init__(self, buttonID):
        super().__init__()
        self.setWindowTitle("Midi Joy: button: " + str(buttonID+1))
        self.layout = QVBoxLayout()
        #add actionlist populating
        for i in range(0, len(globalButtonActionList[buttonID])):
            if(globalButtonActionList[buttonID][i].inputIndex == buttonID):
                actionList = QGridLayout()
                mute = QCheckBox()
                mute.setText("Mute")
                mute.setToolTip("Mute")
                ###
                midiPort = QComboBox()
                midiPortList = mm.get_output_list()
                midiPort.addItems(midiPortList)
                midiPort.setCurrentIndex(globalButtonActionList[buttonID][i].midiPortIndex)
                mm.open_port_with_name(globalButtonActionList[buttonID][i].midiPortName)
                midiPort.currentIndexChanged.connect(lambda port, buttonID=buttonID, actionID=i, newAction=midiPort: 
                    globalButtonActionList[buttonID][actionID].set_midiPort(newAction))
                midiPort.currentIndexChanged.connect(lambda port, newAction=midiPort: 
                    globalButtonActionList[buttonID][actionID].set_midiPortOpenPortsIndex(mm.open_port_with_widget(newAction)))
                ###
                actionType = QComboBox()
                actionTypeList = inputs.get_actionType_list()
                actionType.setToolTip("Midi Message Type")
                actionType.addItems(actionTypeList)
                actionType.setCurrentIndex(globalButtonActionList[buttonID][i].actionType)
                actionType.currentIndexChanged.connect(lambda action, buttonID=buttonID, actionID=i, newAction=actionType: 
                    globalButtonActionList[buttonID][actionID].set_midiAction(newAction))
                ###
                actionList.addWidget(mute, i, 0)
                actionList.addWidget(midiPort, i+1, 1)
                actionList.addWidget(actionType, i+1, 0)
                self.layout.addLayout(actionList)
        addActionButtonLayout = QGridLayout()
        addActionButton = mjs.AnimatedButton("Add Midi Action")
        addActionButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        addActionButton.clicked.connect(lambda checked, id=buttonID: self.addAction(id))
        addActionButtonLayout.addWidget(addActionButton)
        self.layout.addLayout(addActionButtonLayout)
        screenSize = QApplication.primaryScreen().size()
        #self.setMinimumSize(screenSize.width()/3.75, screenSize.height()/3.75)
        self.setLayout(self.layout)
        self.show()

    def addAction(self, buttonID):
        globalButtonActionList[buttonID].append(inputs.ButtonAction(inputIndex=buttonID))
        globalButtonActionList[buttonID][len(globalButtonActionList[buttonID])-1].set_midiPortOpenPortsIndex(mm.open_port_with_name(globalButtonActionList[buttonID][len(globalButtonActionList[buttonID])-1].midiPortName))
        self.hide()
        self.__init__(buttonID)

    def changeMute(self, buttonID, actionID, newState):
        pass

def get_output_list():
    return mido.get_output_names()
