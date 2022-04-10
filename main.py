import mido
import threading
import pygame as game
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal

game.init()
def get_active_controller(event):
    #function returns which controller is currently inputting
    #This is a qthread so it can run in background 
    #guided by https://realpython.com/python-pyqt-qthread/

    if(     event.type == game.JOYBUTTONDOWN
            or event.type == game.JOYBALLMOTION
            or event.type == game.JOYHATMOTION):
        return event.joy
    elif(event.type == game.JOYAXISMOTION):
        if(abs(event.value) > 0.1):
            return event.joy
        else:
            return -1
    else:
        return -1

class pyGame_qthread(QObject):
    controllerSignal = pyqtSignal(int)
    def __init__(self, controllerButtons, joysticks, port):

        self.controllerButtons = controllerButtons
        self.joysticks = joysticks
        self.port = port
        super(pyGame_qthread, self).__init__()

    def pyGame(self):
        while(1):
            for event in game.event.get():
                controller = get_active_controller(event)
                if(controller > -1):
                    #self.controllerButtons[controller].animateClick()
                    self.controllerSignal.emit(controller)
                    print(self.joysticks[controller].get_id())
                    
                    if (event.type == game.JOYBUTTONDOWN):
                        msg = mido.Message('note_on', note=60)
                        self.port.send(msg)

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Midi Joy")
        ports = mido.get_output_names()
        print(ports)
        self.port = mido.open_output(ports[3])

        self.layout = QVBoxLayout()
        
        self.joysticks = [game.joystick.Joystick(x) for x in range(game.joystick.get_count())]
        self.controllerButtons = []
        self.activeController = -1
        for i in range(0, game.joystick.get_count()):
            self.controllerButtons.append(QPushButton(self.joysticks[i].get_name()))
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

    def animateButton(self, button):
        self.controllerButtons[button].animateClick()
        


app = QApplication([])

window = MainWindow()
window.show()

app.exec()