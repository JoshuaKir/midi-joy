import mido
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup
from ui_elements import midi_joy_style as mjs
from midi_and_controller import game_inputs as game


class pyGame_qthread(QObject):
    controllerSignal = pyqtSignal(int)

    def __init__(self, controllerButtons, joysticks, port):

        self.controllerButtons = controllerButtons
        self.joysticks = joysticks
        self.port = port
        super(pyGame_qthread, self).__init__()

    def pyGame(self):
        while(1):
            controller = game.get_active_controller()
            if (controller and controller > -1):
                self.controllerSignal.emit(controller)
                print(self.joysticks[controller].get_id())
            '''
            if (event.type == game.JOYBUTTONDOWN):
                msg = mido.Message('note_on', note=60)
                self.port.send(msg)
            '''

class AnotherWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self, controllerName, controllerID, controllerGUID):
        self.controller = controllerName
        super().__init__()
        #self.layout = QGridLayout()
        self.layout = QVBoxLayout()
        self.setWindowTitle("Midi Joy: "+ self.controller)
        self.controllerAxes = []
        self.controllerButtons = []
        colorArray = ['#bb14e0', '#ff0000', '#005100', '#0011fb']
        axes,buttons = game.get_controller_inputs(controllerID)
        print(axes,buttons)
        self.buttons = QGridLayout()
        for i in range(0, buttons):
            self.controllerButtons.append(mjs.AnimatedButton("Button: " + str(i+1)))
            self.controllerButtons[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            #self.controllerButtons[i].clicked.connect(lambda checked, name=controllerName, id=i, guid=controllerGUID: self.controllerClicked(name, id, guid))
            rowCount = i//4
            self.buttons.addWidget(self.controllerButtons[i], rowCount, i-rowCount*4)

        self.axes = QGridLayout()
        for i in range(0, axes):
            self.controllerAxes.append(mjs.AnimatedButton("Axis: " + str(i+1)))
            self.controllerAxes[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerAxes[i].setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            #self.controllerButtons[i].clicked.connect(lambda checked, name=controllerName, id=i, guid=controllerGUID: self.controllerClicked(name, id, guid))
            rowCount = i%2
            self.axes.addWidget(self.controllerAxes[i], i-rowCount, rowCount)

        #Add hats and buttons
        self.layout.addLayout(self.buttons)
        self.layout.addLayout(self.axes)
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/1.75, screenSize.height()/1.75)
        self.setLayout(self.layout)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Midi Joy")
        ports = mido.get_output_names()
        print(ports)
        self.port = mido.open_output(ports[3])
        self.controllerWindows = []

        self.layout = QVBoxLayout()
        
        self.joysticks = [game.get_controllers().Joystick(x) for x in range(game.get_controllers().get_count())]
        self.controllerButtons = []
        self.activeController = -1
        colorArray = ['#bb14e0', '#ff0000', '#005100', '#0011fb']
        for i in range(0, game.get_controllers().get_count()):
            controllerName = self.joysticks[i].get_name()
            controllerGUID = self.joysticks[i].get_guid()
            self.controllerButtons.append(mjs.AnimatedButton(controllerName))
            self.controllerButtons[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Preferred,
                QSizePolicy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, name=controllerName, id=i, guid=controllerGUID: self.controllerClicked(name, id, guid))
            self.layout.addWidget(self.controllerButtons[i])
        self.container = QWidget()
        self.container.setLayout(self.layout)

        # Set the central widget of the Window.
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()/3, screenSize.height()/3)
        self.setCentralWidget(self.container)

        self.thread = QThread()
        self.pyGame_thread = pyGame_qthread(self.controllerButtons, self.joysticks, self.port)
        self.pyGame_thread.moveToThread(self.thread)
        self.pyGame_thread.controllerSignal.connect(self.animateButton)
        self.thread.started.connect(self.pyGame_thread.pyGame)
        self.thread.start()

    def controllerClicked(self, controllerName, controllerID, controllerGUID):
        print(controllerName, controllerID, controllerGUID)
        self.controllerWindows.append(AnotherWindow(controllerName=controllerName, controllerID=controllerID, controllerGUID=controllerGUID))
        self.controllerWindows[len(self.controllerWindows)-1].show()
        #print(len(self.controllerWindows))

    def animateButton(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()

        self.controllerButtons[button].fullAnimatedClick.start()
        #self.controllerButtons[button].secondAnimation.start()

        

app = QApplication([])

window = MainWindow()
window.show()

app.exec()