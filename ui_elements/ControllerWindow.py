from PyQt6.QtWidgets import QApplication, QVBoxLayout, QGridLayout, QWidget, QSizePolicy, \
    QComboBox, QCheckBox, QSpinBox, QSpacerItem, QFrame, QMenuBar, QFileDialog
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt
import mido
import time
import os
from midi_and_controller import game_inputs as game
from ui_elements import ButtonWindow
from ui_elements import midi_joy_style as mjs
import pickle

globalButtonActionList = []
globalAxisActionList = []
globalHatActionList = []
gameManager = game.GameManager()
joyDown = gameManager.get_joy_down_type()
joyUp = gameManager.get_joy_up_type()
axisMotion = gameManager.get_axis_motion_type()
hatMotion = gameManager.get_hat_motion_type()
controllerCount = gameManager.get_controllers().get_count()

for controllerID in range(controllerCount):
    #controller->button->action
    globalButtonActionList.append([])
    globalAxisActionList.append([])
    globalHatActionList.append([])
start = time.time()
end = time.time()

class ControllerWindow(QWidget):

    def __init__(self, controllerName, controllerID, controllerGUID, midiManager):
        super().__init__()
        for controller in range(controllerCount):
            #controller->button->action
            self.buttonActionList = []
            self.axisActionList = []
            self.hatActionList = []
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.controller = controllerName
        self.midi = midiManager
        self.isClosed = False
        self.axisAnimationArray = []
        self.hatAnimationArray = []
        self.currentFrameAnimationArray = []
        self.lastFrameAxisAnimationArray = []
        self.lastFrameHatAnimationArray = []
        self.layout = QVBoxLayout()
        self.setWindowTitle("Midi Joy: " + self.controller)
        self.controllerID = controllerID
        self.actionWindows = []
        self.controllerAxes = []
        self.controllerButtons = []
        self.controllerHats = []
        self.midiActions = []
        colorArray = mjs.colorArray
        axes, buttons, hats = gameManager.get_controller_inputs(controllerID)

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
            self.buttonActionList.append([])
            self.controllerButtons.append(mjs.AnimatedButton("Button: " + str(i+1)))
            self.controllerButtons[i].set_animation_color(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, controller=self.controllerID, button=i: self.button_clicked(controller, button))
            rowCount = i//4
            self.buttons.addWidget(self.controllerButtons[i], rowCount, i-rowCount*4)

        self.axesAndHats = QGridLayout()
        axisLastRow = 0
        for i in range(0, axes):
            self.axisActionList.append([])
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].set_animation_color(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            self.controllerAxes[i].clicked.connect(lambda checked, controller=self.controllerID, axis=i: self.axis_clicked(controller, axis))
            rowCount = i//2
            axisLastRow = rowCount
            self.axesAndHats.addWidget(self.controllerAxes[i], rowCount, i-rowCount*2)

        for i in range(0, hats):
            self.hatActionList.append([])
            self.controllerHats.append(mjs.AnimatedButton("Hats: " + str(i + 1)))
            self.controllerHats[i].set_animation_color(colorArray[i % len(colorArray)])
            self.controllerHats[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            self.controllerHats[i].clicked.connect(
                lambda checked, controller=self.controllerID, hat=i: self.hat_clicked(controller, hat))
            rowCount = i//2
            self.axesAndHats.addWidget(self.controllerHats[i], rowCount+axisLastRow+1, i, 1, 2)

        #Add hats and buttons
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(self.axesAndHats)
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/1.75, screenSize.height()/1.75)
        self.layout.setSpacing(8)
        self.setLayout(self.layout)

    def button_clicked(self, controllerID, buttonID):
        windowAlreadyOpen = False
        for i, window in enumerate(self.actionWindows):
            if window.buttonID == buttonID and not window.isClosed:
                windowAlreadyOpen = True
            if window.isClosed:
                self.actionWindows.pop(i)

        if not windowAlreadyOpen:
            self.actionWindows.append(ButtonWindow.ButtonWindow(controllerID=controllerID, buttonID=buttonID, actionList=self.buttonActionList, midiManager=self.midi))

    def axis_clicked(self, controllerID, axisID):
        windowAlreadyOpen = False
        for i, window in enumerate(self.actionWindows):
            if window.buttonID == axisID and not window.isClosed:
                windowAlreadyOpen = True
            if window.isClosed:
                self.actionWindows.pop(i)

        if not windowAlreadyOpen:
            self.actionWindows.append(ButtonWindow.AxisWindow(controllerID=controllerID, axisID=axisID, actionList=self.axisActionList, midiManager=self.midi))

    def hat_clicked(self, controllerID, hatID):
        windowAlreadyOpen = False
        for i, window in enumerate(self.actionWindows):
            if window.buttonID == hatID and not window.isClosed:
                windowAlreadyOpen = True
            if window.isClosed:
                self.actionWindows.pop(i)

        if not windowAlreadyOpen:
            self.actionWindows.append(ButtonWindow.HatWindow(controllerID=controllerID, axisID=hatID, actionList=self.hatActionList, midiManager=self.midi))

    def process_game_events(self, event):
        global start
        start = time.time()
        # newButtons = set(currentButtonIDs).difference(lastFrameButtonIDs) #sets are faster
        if (event.joy == self.controllerID):
            if (event.type == joyDown):
                self.controller_button_pressed(event.button)
                self.animate_button(event.button)

            elif (event.type == joyUp):
                self.controller_button_released(event.button)

            elif (event.type == axisMotion):
                newAxis = set([event.axis]).difference(self.lastFrameAxisAnimationArray)  # sets are faster
                if (len(newAxis) > 0 and abs(event.value) > 0.2):
                    self.controller_axis_activated(event.axis, event.value)
                    self.animate_axis_on(event.axis)
                    self.axisAnimationArray.append(event.axis)

                else:
                    for i, axis in enumerate(self.axisAnimationArray):
                        if (abs(event.value) < 0.2 and event.axis == axis):
                            self.controller_axis_deactivated(event.axis, event.value)
                            self.animate_axis_off(event.axis)
                            self.axisAnimationArray.pop(i)

                self.lastFrameAxisAnimationArray = self.axisAnimationArray

            elif (event.type == hatMotion):
                newHat = set([event.hat]).difference(self.lastFrameHatAnimationArray)  # sets are faster
                if (len(newHat) > 0 and (abs(event.value[0]) > 0 or abs(event.value[1]) > 0)):
                    self.controller_hat_activated(event.hat, event.value)
                    self.animate_hat_on(event.hat)
                    self.hatAnimationArray.append(event.hat)

                else:
                    for i, hat in enumerate(self.hatAnimationArray):
                        if (event.hat == hat and (abs(event.value[0]) == 0 or abs(event.value[1]) == 0)):
                            self.controller_hat_deactivated(event.hat, event.value)
                            self.animate_hat_off(event.hat)
                            self.hatAnimationArray.pop(i)

                self.lastFrameHatAnimationArray = self.hatAnimationArray

    def animate_button(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()
        self.controllerButtons[button].fullAnimatedClick.start()

    def animate_axis_on(self, axis):
        self.controllerAxes[axis].secondAnimation.stop()
        self.controllerAxes[axis].firstAnimation.start()

    def animate_axis_off(self, axis):
        self.controllerAxes[axis].firstAnimation.stop()
        self.controllerAxes[axis].secondAnimation.start()

    def animate_hat_on(self, hat):
        self.controllerHats[hat].secondAnimation.stop()
        self.controllerHats[hat].firstAnimation.start()

    def animate_hat_off(self, hat):
        self.controllerHats[hat].firstAnimation.stop()
        self.controllerHats[hat].secondAnimation.start()

    def close_event(self, event):
        self.isClosed = True
        event.accept()

    def save_controller_configuration(self):
        #save function saves a nested array of every action for every button and axis to a file
        currentDir = os.path.dirname(os.path.realpath(__file__))
        fileName = QFileDialog.getSaveFileName(None, 'Save Configuration:', currentDir, 'Midi Joy Save File (*.mj_controller)')
        if (fileName[0] == ''):
            return 1

        with open(fileName[0], 'wb') as mj_file:
            pickle.dump([self.buttonActionList, self.axisActionList, self.hatActionList], mj_file)

        return 0 #successful save

    def load_controller_configuration(self):
        currentDir = os.path.dirname(os.path.realpath(__file__))
        fileName = QFileDialog.getOpenFileName(None, 'Load Configuration:', currentDir, 'Midi Joy Save File (*.mj_controller)')
        if (fileName[0] == ''):
            return 1
        with open(fileName[0], 'rb') as mj_file:
            buttonList, axisList, hatList = pickle.load(mj_file)

        #remove current configuration
        for button in self.buttonActionList:
            button = []

        for button in buttonList:
            if button and button[0].inputIndex < len(self.buttonActionList):
                self.buttonActionList[button[0].inputIndex] = button
                for action in button:
                    self.midi.open_port_with_name(action.midiPortName) #need to open ports in case not yet open

        # remove current configuration
        for axis in self.axisActionList:
            axis = []

        for axis in axisList:
            if axis and axis[0].inputIndex < len(self.axisActionList):
                self.axisActionList[axis[0].inputIndex] = axis
                for action in axis:
                    self.midi.open_port_with_name(action.midiPortName) #need to open ports in case not yet open

        # remove current configuration
        for hat in self.hatActionList:
            hat = []

        for hat in hatList:
            if hat and hat[0].inputIndex < len(self.hatActionList):
                self.hatActionList[hat[0].inputIndex] = hat
                for action in hat:
                    self.midi.open_port_with_name(action.midiPortName)  # need to open ports in case not yet open

        return 0 #successful load

    def get_output_list(self):
        return mido.get_output_names()

    def controller_button_pressed(self, buttonID):
            #if (globalButtonActionList[buttonID] != []):
            #print(globalButtonActionList[controllerID][buttonID])
            for action in self.buttonActionList[buttonID]:
                #print(action.midiAction.midoMessageOn.note)
                if (not action.isMuted):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
            end = time.time()
            print(end - start)

    def controller_button_released(self, buttonID):
            #if (globalButtonActionList[buttonID] != []):
            for action in self.buttonActionList[buttonID]:
                if (not action.isMuted):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)


    def controller_axis_activated(self, axisID, value):
        self.midiedNoteBool = False
        for action in self.axisActionList[axisID]:
            if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(self.controllerID)):
                self.midiedNoteBool = True

        for action in self.axisActionList[axisID]:
            if (not action.isMuted and action.actionType == 0):
                if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(self.controllerID)):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
                    self.midiedNoteBool = True
                if (action.get_connectedButtonIndex() == -1 and not self.midiedNoteBool):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)

            elif (action.actionType == 1):
                action.get_midiAction().set_value(int(abs(value) * 127))
                self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)

    def controller_axis_deactivated(self, axisID, value):
        for action in self.axisActionList[axisID]:
            if (not action.isMuted):
                self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)

    def controller_hat_activated(self, hatID, value):
        self.midiedNoteBool = False
        for action in self.hatActionList[hatID]:
            if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(self.controllerID)):
                self.midiedNoteBool = True

        for action in self.hatActionList[hatID]:
            if (not action.isMuted and action.actionType == 0):
                if (action.get_connectedButtonIndex() in gameManager.get_active_buttons(self.controllerID)):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)
                    self.midiedNoteBool = True
                if (action.get_connectedButtonIndex() == -1 and not self.midiedNoteBool):
                    self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOn)

            elif (not action.isMuted and action.actionType == 1):
                action.get_midiAction().set_value(int(abs(value) * 127))

    def controller_hat_deactivated(self, hatID, value):
        for action in self.hatActionList[hatID]:
            if (not action.isMuted):
                self.midi.send_midi_message(action.midiPortOpenPortsIndex, action.midiAction.midoMessageOff)

    def closeEvent(self, event):
        #qwidget close window override
        for window in self.actionWindows:
            window.close()
        self.isClosed = True
        event.accept()
