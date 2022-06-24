import pygame as game
game.init()

def get_active_controller():
    # function returns which controller is currently inputting
    # This is a qthread so it can run in background
    # guided by https://realpython.com/python-pyqt-qthread/
    for event in game.event.get():
        if( event.type == game.JOYBUTTONDOWN or event.type == game.JOYBALLMOTION or event.type == game.JOYHATMOTION):
            return event.joy
    
        elif(event.type == game.JOYAXISMOTION):
            if(abs(event.value) > 0.1):
                return event.joy
        
        #if no event
        return -1

def get_controllers():
    return game.joystick