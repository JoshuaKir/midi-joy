import mido
import hid
import time
import pygame as game

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


game.init()
#game.joystick.init()
joysticks = [game.joystick.Joystick(x) for x in range(game.joystick.get_count())]
print(game.joystick.get_count())
while 1:
    for event in game.event.get():
        controller = get_wildin_controller(event)
        print(controller)



