import mido
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup, QFile, QTextStream
import qdarkstyle
from ui_elements import midi_joy_style as mjs
from midi_and_controller import game_inputs as game
import ControllerWindow as cw
import time

start = time.time()
end = time.time()
class pyGame_qthread(QObject):
    controllerSignal = pyqtSignal(int)

    def __init__(self, joysticks):

        self.joysticks = joysticks #not needed
        super(pyGame_qthread, self).__init__()

    def pyGame(self):
        while(1):
            controller = game.get_active_controller()
            if (controller and controller > -1):
                global start
                start = time.time()
                self.controllerSignal.emit(controller)
                #print(self.joysticks[controller].get_id())


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Midi Joy")
        ports = mido.get_output_names()
        print(ports)
        self.port = mido.open_output(ports[0])
        self.controllerWindows = []

        self.layout = QVBoxLayout()
        
        self.joysticks = [game.get_controllers().Joystick(x) for x in range(game.get_controllers().get_count())]
        self.controllerButtons = []
        self.activeController = -1
        colorArray = mjs.colorArray
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
        self.pyGame_thread = pyGame_qthread(self.joysticks)
        self.pyGame_thread.moveToThread(self.thread)
        self.pyGame_thread.controllerSignal.connect(self.animateButton)
        self.thread.started.connect(self.pyGame_thread.pyGame)
        self.thread.start()

    def controllerClicked(self, controllerName, controllerID, controllerGUID):
        print(controllerName, controllerID, controllerGUID)
        self.controllerWindows.append(cw.controllerWindow(controllerName=controllerName, controllerID=controllerID, controllerGUID=controllerGUID))
        self.controllerWindows[len(self.controllerWindows)-1].show()

    def animateButton(self, button):
        end = time.time()
        #print(end - start)
        self.controllerButtons[button].fullAnimatedClick.stop()

        self.controllerButtons[button].fullAnimatedClick.start()

app = QApplication([])
app.setStyleSheet(qdarkstyle.load_stylesheet()) #https://github.com/ColinDuquesnoy/QDarkStyleSheet
window = MainWindow()
window.show()

app.exec()