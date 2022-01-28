import mido
import multiprocessing
import pygame as game
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5 import QtCore

def get_wildin_controller(event):
    #function returns which controller is currently inputting
    if(     event.type == game.JOYBUTTONDOWN
            or event.type == game.JOYBUTTONUP
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

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        self.port = mido.open_output('test 3')

        self.layout = QVBoxLayout()
        game.init()
        self.joysticks = [game.joystick.Joystick(x) for x in range(game.joystick.get_count())]
        self.controllerButtons = []
        for i in range(0, game.joystick.get_count()):
            self.controllerButtons.append(QPushButton(self.joysticks[i].get_name()))
            # controllerButtons[i].setCheckable(True)
            self.controllerButtons[i].clicked.connect(self.clicked)
            self.layout.addWidget(self.controllerButtons[i])
        self.container = QWidget()
        self.container.setLayout(self.layout)

        # Set the central widget of the Window.
        self.setCentralWidget(self.container)

        self.my_timer = QtCore.QTimer()
        self.my_timer.timeout.connect(self.pyGame)
        self.my_timer.start(100)  # ms


    def pyGame(self):
        for event in game.event.get():
            controller = get_wildin_controller(event)
            if(controller > -1):
                self.controllerButtons[controller].animateClick()
                print(self.joysticks[controller].get_id())
        self.update()

    def clicked(self):
        print("asdfasfsfsaf")
        msg = mido.Message('note_on', note=60)
        self.port.send(msg)


app = QApplication([])

window = MainWindow()
window.show()

app.exec()