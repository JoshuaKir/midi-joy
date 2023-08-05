from PyQt6.QtWidgets import QVBoxLayout, QGridLayout, QWidget, QSizePolicy, \
    QComboBox, QCheckBox, QSpinBox, QSpacerItem, QFrame, QPushButton
from PyQt6.QtCore import Qt
from ui_elements import midi_joy_style as mjs
from midi_and_controller import InputButton as inputs
from midi_and_controller import midiManager

class ButtonWindow(QWidget):

    def __init__(self, controllerID, buttonID, actionList, midiManager):
        super().__init__()
        self.setWindowTitle("Midi Joy: button: " + str(buttonID+1))
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.isClosed = False
        self.actionList = actionList
        self.midi = midiManager
        self.layout = QVBoxLayout()
        self.controllerID = controllerID
        self.buttonID = buttonID
        self.add_action_button_ui()
        self.update_ui()
        self.show()

    def update_ui(self):
        #add actionlist populating
        global globalButtonActionList
        for i in range(0, len(self.actionList[self.buttonID])):
            self.add_action_ui(i)

    def add_action_ui(self, actionID):
        global globalButtonActionList
        action = self.actionList[self.buttonID][actionID]
        actionList = QGridLayout()
        lastCol = 2
        muteBox = self.add_mute_box(actionID)
        ###
        if (action.actionType == 0):
            actionList.addWidget(self.add_note_box(actionID), actionID, 1)
        ###
        if (action.actionType == 1):
            lastCol = 3
            actionList.addWidget(self.add_control_type_box(actionID), actionID, 1)
            actionList.addWidget(self.add_control_value_box(actionID), actionID, lastCol - 1)
        ###
        midiPort = self.add_midi_port_box(actionID)
        ###
        actionType = self.add_actionType_box(actionID)
        ###
        deleteActionBox = self.add_delete_action_button(actionID)
        lineSpacer = QFrame()
        lineSpacer.setFrameShape(QFrame.Shape.HLine)
        lineSpacer.setFrameShadow(QFrame.Shadow.Sunken)
        firstSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        secondSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actionList.addWidget(actionType, actionID, 0)
        actionList.addWidget(deleteActionBox, actionID, lastCol)
        actionList.addWidget(midiPort, actionID + 1, 0)
        actionList.addWidget(muteBox, actionID + 1, lastCol)
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
            self.actionList[self.buttonID][actionID].set_mute(muteState.isChecked()))
        return muteBox

    def add_delete_action_button(self, actionID):
        deletebox = QPushButton("&Delete")
        # deletebox.setText("Mute")
        deletebox.setToolTip("Delete Action")
        deletebox.clicked.connect(
            lambda delete, controller=self.controllerID, button=self.buttonID, actionID=actionID:
            self.delete_action(controller, button, actionID))
        return deletebox

    def add_note_box(self, actionID):
        noteBox = QComboBox()
        noteList = list(midiManager.flatsList.values())
        noteBox.setToolTip("Midi Note")
        noteBox.addItems(noteList)
        noteBox.setCurrentIndex(-1)
        noteBox.setCurrentIndex(self.actionList[self.buttonID][actionID].midiAction.get_note())
        noteBox.activated.connect(
            lambda state, note=noteBox:
            self.actionList[self.buttonID][actionID].get_midiAction().set_note(note.currentIndex()))
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
            self.actionList[self.buttonID][actionID].get_midiAction().set_control(value.value()))
        return controlBox

    def add_control_value_box(self, actionID):
        controlValue = QSpinBox()
        controlValue.setToolTip("Control Value")
        controlValue.setMinimum(0)
        controlValue.setMaximum(127)
        controlValue.setPrefix('Control Change Value: ')
        controlValue.valueChanged.connect(
            lambda state, value=controlValue:
            self.actionList[self.buttonID][actionID].get_midiAction().set_value(
                value.value()))
        return controlValue

    def add_midi_port_box(self, actionID):
        midiPort = QComboBox()
        midiPortList = self.midi.get_output_list()
        midiPort.addItems(midiPortList)
        midiPort.setCurrentIndex(midiPortList.index(self.actionList[self.buttonID][actionID].midiPortName))
        self.midi.open_port_with_name(self.actionList[self.buttonID][actionID].midiPortName)
        midiPort.currentIndexChanged.connect(lambda port, newAction=midiPort:
                                             self.actionList[self.buttonID][actionID].set_midiPort(
                                                 newAction.currentIndex()))
        midiPort.currentIndexChanged.connect(lambda port, actionID=actionID, newAction=midiPort:
                                             self.actionList[self.buttonID][actionID].set_midiPortOpenPortsIndex(
                                                 self.midi.open_port_with_name(newAction.currentText())))
        return midiPort

    def add_actionType_box(self, actionID):
        actionType = QComboBox()
        actionTypeList = inputs.get_actionType_list()
        actionType.setToolTip("Midi Message Type")
        actionType.addItems(actionTypeList)
        actionType.setCurrentIndex(self.actionList[self.buttonID][actionID].actionType)
        actionType.currentIndexChanged.connect(
            lambda type, action=self.actionList[self.buttonID][actionID], controller=self.controllerID, button=self.buttonID, newAction=actionType:
            self.control_change(action, controller, button, newAction))
        return actionType

    def add_action(self, controllerID, buttonID):
        #needs to be overriden
        globalAction = self.actionList[buttonID]
        globalAction.append(inputs.ButtonAction(inputIndex=buttonID))
        newActionID = len(globalAction) - 1
        print(globalAction[newActionID].get_midiAction().get_note())
        portIndex = self.midi.open_port_with_name(globalAction[newActionID].midiPortName)
        globalAction[newActionID].set_midiPortOpenPortsIndex(portIndex)
        self.add_action_ui(newActionID)

    def delete_action(self, controllerID, buttonID, actionID):
        self.actionList[buttonID].pop(actionID)
        self.hide()
        self.__init__(controllerID, buttonID, self.actionList, self.midi)

    def control_change(self, action, controllerID, buttonID, newAction):
        action.set_midiAction(newAction.currentIndex())
        self.hide()
        self.__init__(controllerID, buttonID, self.actionList, self.midi)

    def closeEvent(self, event):
        #qwidget close window override
        self.isClosed = True
        event.accept()

class AxisWindow(ButtonWindow):
    def __init__(self, controllerID, axisID, actionList, midiManager):
        super().__init__(controllerID, axisID, actionList, midiManager)
        self.setWindowTitle("Midi Joy: Axis: " + str(axisID+1))

    def add_action_ui(self, actionID):
        global globalButtonActionList
        globalAction = self.actionList[self.buttonID][actionID]
        actionList = QGridLayout()
        lastCol = 3
        muteBox = self.add_mute_box(actionID)
        ###
        if (globalAction.actionType == 0):
            actionList.addWidget(self.add_note_box(actionID), actionID, 1)
            actionList.addWidget(self.add_connected_button_box(actionID), actionID, lastCol - 1)
        ###
        if (globalAction.actionType == 1):
            lastCol = 4
            actionList.addWidget(self.add_control_type_box(actionID), actionID, 1)
            actionList.addWidget(self.add_control_value_box(actionID), actionID, lastCol - 2)
            actionList.addWidget(self.add_connected_button_box(actionID), actionID, lastCol - 1)
        ###
        midiPort = self.add_midi_port_box(actionID)
        ###
        actionType = self.add_actionType_box(actionID)
        ###
        deleteActionBox = self.add_delete_action_button(actionID)
        lineSpacer = QFrame()
        lineSpacer.setFrameShape(QFrame.Shape.HLine)
        lineSpacer.setFrameShadow(QFrame.Shadow.Sunken)
        firstSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        secondSpacer = QSpacerItem(20, 7, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actionList.addWidget(actionType, actionID, 0)
        actionList.addWidget(deleteActionBox, actionID, lastCol)
        actionList.addWidget(midiPort, actionID + 1, 0)
        actionList.addWidget(muteBox, actionID + 1, lastCol)
        self.layout.addLayout(actionList)
        self.layout.addItem(firstSpacer)
        self.layout.addWidget(lineSpacer)
        self.layout.addItem(secondSpacer)
        self.layout.removeWidget(self.add_actionButton)
        self.add_action_button_ui()

    def add_action(self, controllerID, buttonID):
        globalAction = self.actionList[buttonID]
        globalAction.append(inputs.AxisAction(inputIndex=buttonID))
        newActionID = len(globalAction) - 1
        print(globalAction[newActionID].get_midiAction().get_note())
        portIndex = self.midi.open_port_with_name(globalAction[newActionID].midiPortName)
        globalAction[newActionID].set_midiPortOpenPortsIndex(portIndex)
        self.add_action_ui(newActionID)

    def add_connected_button_box(self, actionID):
        buttonList = ["Button 0: Open Strum"]
        for button in range(0, len(self.actionList)):
            buttonList.append('Button ' + str(button + 1))  # this gives us open + all buttons
        buttonBox = QComboBox()
        buttonBox.setToolTip("Connected Button Box")
        buttonBox.addItems(buttonList)  # list of 0 -> num of buttons: 0 will be open strum (-1)
        buttonBox.setCurrentIndex(-1)
        buttonBox.setCurrentIndex(self.actionList[self.buttonID][actionID].get_connectedButtonIndex() + 1)
        buttonBox.activated.connect(
            lambda state, axis=self.buttonID, actionID=actionID, note=buttonBox:
            self.actionList[self.buttonID][actionID].set_connectedButtonIndex(
                buttonBox.currentIndex() - 1))
        return buttonBox

class HatWindow(AxisWindow):
    def __init__(self, controllerID, axisID, actionList, midiManager):
        super().__init__(controllerID, axisID, actionList, midiManager)
        self.setWindowTitle("Midi Joy: Hat: " + str(axisID+1))
