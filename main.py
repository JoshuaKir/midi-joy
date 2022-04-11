import mido
import threading
import pygame as game
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QGraphicsColorizeEffect
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup

game.init()


def get_active_controller(event):
    # function returns which controller is currently inputting
    # This is a qthread so it can run in background
    # guided by https://realpython.com/python-pyqt-qthread/

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


class AnimatedButton(QPushButton):

    # from https://stackoverflow.com/questions/52270391/i-want-to-create-a-color-animation-for-a-button-with-pyqt5
    # https://www.pythonguis.com/tutorials/qpropertyanimation/
    def __init__(self, *args, **kwargs):
        super(AnimatedButton, self).__init__(*args, **kwargs)
        effect = QGraphicsColorizeEffect(self)
        effect.setColor(QtGui.QColor(0, 0, 0))
        self.setGraphicsEffect(effect)

        self.firstAnimation = QtCore.QPropertyAnimation(effect, b"color")

        self.firstAnimation.setStartValue(QtGui.QColor(0, 0, 0))
        self.firstAnimation.setEndValue(QtGui.QColor('#bb14e0'))
        self.firstAnimation.setDuration(50)

        self.secondAnimation = QtCore.QPropertyAnimation(effect, b"color")
        self.secondAnimation.setEndValue(QtGui.QColor(0, 0, 0))
        self.secondAnimation.setDuration(2000)

        self.fullAnimatedClick = QSequentialAnimationGroup()
        self.fullAnimatedClick.addAnimation(self.firstAnimation)
        self.fullAnimatedClick.addAnimation(self.secondAnimation)


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
        
        self.joysticks = [game.joystick.Joystick(x) for x in range(game.joystick.get_count())]
        self.controllerButtons = []
        self.activeController = -1
        for i in range(0, game.joystick.get_count()):
            self.controllerButtons.append(AnimatedButton(self.joysticks[i].get_name()))
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