from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QGridLayout, QWidget, QLabel, QGraphicsColorizeEffect, QSizePolicy, QComboBox, QCheckBox
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QSequentialAnimationGroup
from midi_and_controller import game_inputs as game
from midi_and_controller import InputButton as inputs
import mido

globalButtonActionList = []
globalAxisActionList = []
colorArray = ['#ab76e0', '#f570a5', '#1cc468', '#3cd7f6', '#f7b67d']
class AnimatedButton(QPushButton):

    # from https://stackoverflow.com/questions/52270391/i-want-to-create-a-color-animation-for-a-button-with-pyqt5
    # https://www.pythonguis.com/tutorials/qpropertyanimation/
    def __init__(self, *args, **kwargs):
        super(AnimatedButton, self).__init__(*args, **kwargs)
        self.set_animation_color('#bb14e0')

    def set_animation_color(self, colorHex):
        effect = QGraphicsColorizeEffect(self)
        effect.setColor(QtGui.QColor(0, 0, 0))
        self.setGraphicsEffect(effect)
        
        self.firstAnimation = QtCore.QPropertyAnimation(effect, b"color")
        self.firstAnimation.setStartValue(QtGui.QColor(0, 0, 0))
        self.firstAnimation.setEndValue(QtGui.QColor(colorHex))
        self.firstAnimation.setDuration(50)

        self.secondAnimation = QtCore.QPropertyAnimation(effect, b"color")
        self.secondAnimation.setEndValue(QtGui.QColor(0, 0, 0))
        self.secondAnimation.setDuration(2000)

        self.fullAnimatedClick = QSequentialAnimationGroup()
        self.fullAnimatedClick.addAnimation(self.firstAnimation)
        self.fullAnimatedClick.addAnimation(self.secondAnimation)