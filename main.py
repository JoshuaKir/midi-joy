import mido
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup, QFile, QTextStream
import qdarkstyle
from ui_elements import midi_joy_style as mjs
from midi_and_controller import game_inputs as game
import ControllerWindow as cw
import time

start = time.time()
end = time.time()
openControllerWindows = 0
gameManager = game.GameManager()

class PyGameEmitter_qthread(QObject):
    eventSignal = pyqtSignal(gameManager.get_typing_of_events())

    def __init__(self, joysticks):
        super(PyGameEmitter_qthread, self).__init__()

    def py_game_emitter(self):
        while(1):
            events = gameManager.get_event()
            if(len(events) > 0):
                self.eventSignal.emit(events)

class PyGameMainMenuAnimation_qthread(QObject):
    controllerSignal = pyqtSignal(int)

    def __init__(self, joysticks):
        super(PyGameMainMenuAnimation_qthread, self).__init__()

    def py_game_controller(self):
        activeControllers = []
        lastFrameActiveControllers = []
        while(1):
            activeControllers = gameManager.get_active_controllers()
            newControllers = set(activeControllers).difference(lastFrameActiveControllers)
            for controller in newControllers:
                self.controllerSignal.emit(controller)

            lastFrameActiveControllers = activeControllers
            time.sleep(0.01)
# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Midi Joy")
        self.controllerWindows = []
        self.layout = QVBoxLayout()
        
        self.joysticks = [gameManager.get_controllers().Joystick(x) for x in range(gameManager.get_controllers().get_count())]
        self.controllerButtons = []
        colorArray = mjs.colorArray
        for i in range(0, gameManager.get_controllers().get_count()):
            controllerName = self.joysticks[i].get_name()
            controllerGUID = self.joysticks[i].get_guid()
            self.controllerButtons.append(mjs.AnimatedButton(controllerName))
            self.controllerButtons[i].set_animation_color(colorArray[i%len(colorArray)])
            self.controllerButtons[i].setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred)
            #https://stackoverflow.com/questions/40705063/pyqt-pushbutton-connect-creation-within-loop
            self.controllerButtons[i].clicked.connect(lambda checked, name=controllerName, id=i, guid=controllerGUID: self.controller_clicked(name, id, guid))
            self.layout.addWidget(self.controllerButtons[i])
        self.container = QWidget()
        self.container.setLayout(self.layout)

        # Set the central widget of the Window.
        screenSize = QApplication.primaryScreen().size()
        self.setMinimumSize(screenSize.width()//3, screenSize.height()//3)
        self.setCentralWidget(self.container)

        self.emitterThread = QThread()
        self.pyGameEmitterThread = PyGameEmitter_qthread(self.joysticks)
        self.pyGameEmitterThread.moveToThread(self.emitterThread)
        self.pyGameEmitterThread.eventSignal.connect(self.send_event_to_controller_windows)
        self.emitterThread.started.connect(self.pyGameEmitterThread.py_game_emitter)
        self.emitterThread.start()

        self.controllerThread = QThread()
        self.py_game_controllerThread = PyGameMainMenuAnimation_qthread(self.joysticks)
        self.py_game_controllerThread.moveToThread(self.controllerThread)
        self.py_game_controllerThread.controllerSignal.connect(self.animate_button)
        self.controllerThread.started.connect(self.py_game_controllerThread.py_game_controller)
        self.controllerThread.start()

    def controller_clicked(self, controllerName, controllerID, controllerGUID):
        print(controllerName, controllerID, controllerGUID)
        global openControllerWindows
        #first remove any closed windows
        for i, window in enumerate(self.controllerWindows):
            if (window.isClosed):
                self.controllerWindows.pop(i)
                openControllerWindows -= 1

        existingWindowIndex = -1
        for i, window in enumerate(self.controllerWindows):
            if (window.controllerID == controllerID):
                existingWindowIndex = i
                
        if (existingWindowIndex == -1):
            self.controllerWindows.append(cw.ControllerWindow(controllerName=controllerName, controllerID=controllerID, controllerGUID=controllerGUID))
            self.controllerWindows[len(self.controllerWindows)-1].show()
            openControllerWindows += 1
        else:
            self.controllerWindows[existingWindowIndex].activateWindow()

    def send_event_to_controller_windows(self, events):
        for i, window in enumerate(self.controllerWindows):
            if (not window.isClosed):
                window.process_game_events(events)
            else:
                self.controllerWindows.pop(i)

    def animate_button(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()
        self.controllerButtons[button].fullAnimatedClick.start()

app = QApplication([])
app.setStyleSheet(qdarkstyle.load_stylesheet()) #https://github.com/ColinDuquesnoy/QDarkStyleSheet
window = MainWindow()
window.show()

app.exec()