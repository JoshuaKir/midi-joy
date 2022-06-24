import mido
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QGraphicsColorizeEffect
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
    def __init__(self, controllerName):
        self.controller = controllerName
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel(self.controller)
        layout.addWidget(self.label)
        self.setLayout(layout)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Midi Joy")
        ports = mido.get_output_names()
        print(ports)
        self.port = mido.open_output(ports[3])

        self.layout = QVBoxLayout()
        
        self.joysticks = [game.get_controllers().Joystick(x) for x in range(game.get_controllers().get_count())]
        self.controllerButtons = []
        self.activeController = -1
        colorArray = ['#bb14e0', '#ff0000', '#005100', '#0011fb']
        for i in range(0, game.get_controllers().get_count()):
            self.controllerButtons.append(mjs.AnimatedButton(self.joysticks[i].get_name()))
            self.controllerButtons[i].setAnimationColor(colorArray[i%len(colorArray)])
            self.controllerButtons[i].clicked.connect(self.controllerClicked)
            self.layout.addWidget(self.controllerButtons[i])
        self.container = QWidget()
        self.container.setLayout(self.layout)

        # Set the central widget of the Window.
        self.setCentralWidget(self.container)

        self.thread = QThread()
        self.pyGame_thread = pyGame_qthread(self.controllerButtons, self.joysticks, self.port)
        self.pyGame_thread.moveToThread(self.thread)
        self.pyGame_thread.controllerSignal.connect(self.animateButton)
        self.thread.started.connect(self.pyGame_thread.pyGame)
        self.thread.start()

    def controllerClicked(self, controllerName):
        print(controllerName)

    def animateButton(self, button):
        self.controllerButtons[button].fullAnimatedClick.stop()

        self.controllerButtons[button].fullAnimatedClick.start()
        #self.controllerButtons[button].secondAnimation.start()

        

app = QApplication([])

window = MainWindow()
window.show()

app.exec()