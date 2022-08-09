import pygame as game
game.init()
game.joystick.init()

def get_active_controller():
    # function returns which controller is currently inputting
    # This is a qthread so it can run in background
    # guided by https://realpython.com/python-pyqt-qthread/
    for event in game.event.get():
        #print(event)
        if(event.type == game.JOYBUTTONDOWN or event.type == game.JOYBALLMOTION or event.type == game.JOYHATMOTION):
            return event.joy
    
        elif(event.type == game.JOYAXISMOTION):
            if(abs(event.value) > 0.1):
                return event.joy
        
        #if no event
        return -1

def get_active_buttons(controllerID):
    # function returns which controller is currently inputting
    # This is a qthread so it can run in background
    # guided by https://realpython.com/python-pyqt-qthread/
    #event.get pops items out of the queue so can only be used once
    #however can continue to check state of buttons and compare from there
    controller = game.joystick.Joystick(controllerID)
    activeButtons = []
    for button in range(controller.get_numbuttons()):
        #print("what " + str(controller.get_button(button)))
        if(controller.get_button(button)):
            activeButtons.append(button)
            print(activeButtons)
    
    return activeButtons

def get_controller_inputs(controllerID):
    print(game.joystick.Joystick(controllerID).get_numballs())
    return[game.joystick.Joystick(controllerID).get_numaxes(), game.joystick.Joystick(controllerID).get_numbuttons()]

def get_controllers():
    return game.joystick

#kinda funny
#get_power_level