###################################
# Smart keycode-ecode mapper by CRImier
# TODO: search for duplicate keycodes
###################################

import sys

#Preparations:
print "This script listens for keycodes and, once detected, lets you choose the appropriate ecode from system-wide ecode collection"
print "Once Ctrl+C-ed, it prints out a Python dictionary of keycode:ecode entries and exits"

from driver import Chatpad

d = {} #Yes, this is THE dictionary.

print "This script uses Python 'evdev' module ecodes.ecodes.keys() list as a ecode base"
from evdev.ecodes import ecodes
ecodes = [key for key in ecodes.keys() if key.startswith("KEY_")] #filtered ecodes 
fsecodes = [key[4:] for key in ecodes] #filtered and stripped ecodes

print "#########################"
print "-How to choose a proper ecode?"
print "-This script takes all KEY_$ ecodes and wait you to either enter the $ or search for an ecode."
print "To enter the $, enter it in uppercase (i.e. 'A' would mean that you chose 'KEY_A')."
print "To search for an ecode, enter part of it in lowercase. Space-separated $ containing your input symbols will be printed out."
print "#########################"

def callback(pressed, *args):
    if not pressed or len(pressed) > 1:
        return None
    print "Keypress detected!"
    keycode = pressed[0]
    try:
        while True:
            if keycode in d.keys():
                print "This key has already been pressed, beware"
            user_input = raw_input("Enter or search:").strip(" ")
            if not user_input: 
                return None
            if not user_input.islower() and not user_input.isupper() and not user_input.isdigit():
                print "Mixed case input detected, ABORT ABORT"
                continue
            elif user_input.isupper() or user_input.isdigit():
                if user_input in fsecodes:
                    if 'KEY_'+user_input in d.values(): print "Value already there, overwriting"
                    d[keycode] = 'KEY_'+user_input
                    print "Key KEY_"+user_input+" saved"
                    return True #Exiting as we've recorded the keycode successfully.
                else:
                    print "Ecode not found, try again"
                    continue
            elif user_input.islower():
                user_input = user_input.upper()
                suggestions = [key for key in fsecodes if user_input in key]
                if suggestions:
                    print " ".join(suggestions)
                else:
                    print "Sorry, nothing found."
    except KeyboardInterrupt:
        return None

def exit():
    print d
    sys.exit(0)    

#Now is the actual key listening
chatpad = Chatpad(port="/dev/ttyUSB1", keycode_callback=callback, name=None) #Not enabling evdev input by passing 'name' as None
print "Starting listening."
print "If you accidentally press more than one key or an unneeded key and don't need to register it, just send an empty response."
try:
    chatpad.listen()
except KeyboardInterrupt:
    exit()
