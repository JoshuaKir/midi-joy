import pygame as game

class GameManager:
    def __init__(self):
        game.init()
        game.joystick.init()

    def get_active_controllers(self):
        # function returns which controller is currently inputting
        # This is a qthread so it can run in background
        # guided by https://realpython.com/python-pyqt-qthread/
        activeControllers = []
        controllerCount = self.get_controllers().get_count()
        for controllerID in range(controllerCount):
            controller = self.get_controllers().Joystick(controllerID)
            for button in range(controller.get_numbuttons()):
                if(controller.get_button(button)):
                    activeControllers.append(controller.get_id())
                    #print(activeButtons)

        return activeControllers

    def get_active_buttons(self, controllerID):
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
                #print(activeButtons)

        return activeButtons

    def get_active_button(self, controllerID):
        # function returns which controller is currently inputting
        # This is a qthread so it can run in background
        # guided by https://realpython.com/python-pyqt-qthread/
        #need to watch for dropped inputs
        for event in game.event.get():
            #can do case and pass in type of input ie axis, button etc
            if ((event.type == game.JOYBUTTONDOWN or event.type == game.JOYBUTTONUP) and event.joy == controllerID):
                if (event.type == game.JOYBUTTONDOWN):
                    return [event.button, True] #tuple for on/off

                elif(event.type == game.JOYBUTTONUP):
                    return [event.button, False]

                #if no event
        return [-1, False]

    def get_event(self):
        #for running loop when no controllerWindows are opened
        for event in game.event.get():
            return event

        return None

    def get_controller_inputs(self, controllerID):
        print(game.joystick.Joystick(controllerID).get_numballs())
        return[game.joystick.Joystick(controllerID).get_numaxes(), game.joystick.Joystick(controllerID).get_numbuttons()]

    def get_controllers(self):
        return game.joystick

    def get_typing_of_event(self):
        x = game.event.EventType
        return (x)

    def get_joy_down_type(self):
        return game.JOYBUTTONDOWN

    def get_joy_up_type(self):
        return game.JOYBUTTONUP
#kinda funny
#get_power_level