##################################
# Python Xbox chatpad driver by CRImier
# Special thanks to Cliff L. Biffle - cliffle.org - for describing the protocol.
# Written using Arduino library - https://github.com/vitormhenrique/xbox_chatpad_library/ - as a reference
###################################


from serial import Serial
from evdev import ecodes, UInput
from time import sleep


class Chatpad():
    
    #Some hard-coded things about the ChatPad protocol
    kInitMessage = bytearray([ 0x87, 0x02, 0x8C, 0x1F, 0xCC ])
    kAwakeMessage = bytearray([ 0x87, 0x02, 0x8C, 0x1B, 0xD0 ])
    kShiftMask = (1 << 0)
    kGreenSquareMask = (1 << 1)
    kOrangeCircleMask = (1 << 2)
    kPeopleMask = (1 << 3)
    #Modifier dictionary
    mod_dict = {kShiftMask:1, kGreenSquareMask: 2, kOrangeCircleMask: 3, kPeopleMask: 4}
    #Key dictionary
    key_dict = {17: 'KEY_7', 18: 'KEY_6', 19: 'KEY_5', 20: 'KEY_4', 21: 'KEY_3', 22: 'KEY_2', 23: 'KEY_1', 33: 'KEY_U', 34: 'KEY_Y', 35: 'KEY_T', 36: 'KEY_R', 37: 'KEY_E', 38: 'KEY_W', 39: 'KEY_Q', 49: 'KEY_J', 50: 'KEY_H', 51: 'KEY_G', 52: 'KEY_F', 53: 'KEY_D', 54: 'KEY_S', 55: 'KEY_A', 65: 'KEY_N', 66: 'KEY_B', 67: 'KEY_V', 68: 'KEY_C', 69: 'KEY_X', 70: 'KEY_Z', 81: 'KEY_RIGHT', 82: 'KEY_M', 83: 'KEY_DOT', 84: 'KEY_SPACE', 85: 'KEY_LEFT', 98: 'KEY_COMMA', 99: 'KEY_ENTER', 100: 'KEY_P', 101: 'KEY_0', 102: 'KEY_9', 103: 'KEY_8', 113: 'KEY_BACKSPACE', 114: 'KEY_L', 117: 'KEY_O', 118: 'KEY_I', 119: 'KEY_K'}
    key_dict.update({1: 'KEY_LEFTSHIFT', 2: 'KEY_LEFTCTRL', 3: 'KEY_RIGHTALT', 4:'KEY_LEFTMETA'}) #Adding modifiers in the dictionary - we'll be injecting their keycodes if modifiers will be found

    def __init__(self, port = "/dev/ttyAMA0", name="xbox_chatpad_input", keycode_callback = None, ecode_callback = None):
        self.keycode_callback = keycode_callback
        self.ecode_callback = ecode_callback
        if ecode_callback == None and name: #If we don't have any external callback provided, we should be using a built-in one that uses uinput
            self.ecode_callback = self.uinput_callback
            self.uinput = UInput(name=name, devnode='/dev/uinput')
        if self.keycode_callback == None: #If keycode_callback is not provided
            self.keycode_callback = lambda *args: None #Setting callback to empty function to avoid exceptions 
        if self.ecode_callback == None: #If ecode_callback is not provided
            self.ecode_callback = lambda *args: None #Setting callback to empty function to avoid exceptions 
        self.name = name
        self.port = port
        self.serial = Serial(port, 19200)
        
    def send_init_message(self):
        #print "Init message sent"
        self.serial.write(self.kInitMessage)

    def send_awake_message(self):
        #print "Awake message sent"
        self.serial.write(self.kAwakeMessage)

    def test_chatpad_on_serial(self):
        # TODO: Add Chatpad detection on a serial port (using 5-byte init response messages starting with A5)
        return NotImplementedError

    def uinput_callback(self, pressed, released):
        for key in pressed: 
            #print "Key pressed: "+self.key_dict[key]
            self.uinput.write(ecodes.EV_KEY, ecodes.ecodes[key], 1)
        for key in released:
            #print "Key released: "+self.key_dict[key]
            self.uinput.write(ecodes.EV_KEY, ecodes.ecodes[key], 0)
        self.uinput.syn()

    def listen(self):
        self.send_init_message()
        self.send_awake_message()
        counter = 0
        counter_treshold = 10
        pressed_keys = []
        previous_keys = []
        pressed_modifiers = []
        previous_modifiers = []
        while True:
            while self.serial.inWaiting() > 8:
                #print self.serial.inWaiting()
                data = self.serial.read(1)
                rdata = bytearray(data[0])[0]
                expected = bytearray([0xB4])[0]
                if rdata != expected:
                    #print "Invalid first byte, shuffling further: "+str(rdata)+", expected: "+str(expected)
                    continue
                #print "First byte OK, checking second byte:"
                data += self.serial.read(1)
                rdata = bytearray(data[1])[0]
                expected = bytearray([0xC5])[0]
                if rdata != expected:
                    #print "Invalid second byte, shuffling further: "+str(rdata)+", expected: "+str(expected)
                    continue
                data += self.serial.read(6)
                #Data package received
                #I won't be checking the checksum, too lazy =)
                #print "Data package received: "+str(data)
                pressed_keys = []
                pressed_modifiers = []
                modifiers = bytearray(data[3])[0]
                key0 = bytearray(data[4])[0]
                key1 = bytearray(data[5])[0]
                if key0:
                    #print "Key 0 is: "+str(key0)
                    pressed_keys.append(key0)                   
                if key1: 
                    #print "Key 1 is: "+str(key1)
                    pressed_keys.append(key1)                   
                if not key0 and not key1: 
                    #print "All keys released"
                    pressed_keys = []
                for modifier in self.mod_dict.keys():
                    if modifier & modifiers == modifier:
                        pressed_modifiers.append(self.mod_dict[modifier])
                if previous_keys == pressed_keys and previous_modifiers == pressed_modifiers:
                    continue #Duplicate message received, no need to worry
                #Next lines would be a perfect example of where to use sets - wonder what is their performance and if that would be premature optimisation
                pressed = [key for key in pressed_keys if key not in previous_keys]
                for mod in pressed_modifiers:
                    if mod not in previous_modifiers:
                        #Append modifier to pressed keys
                        pressed.append(mod)
                released = [key for key in previous_keys if key not in pressed_keys]
                for mod in previous_modifiers:
                    if mod not in pressed_modifiers:
                        #Append modifier to released keys
                        released.append(mod)
                #Keys read, time to process
                self.keycode_callback(pressed, released)
                self.ecode_callback([self.key_dict[keycode] for keycode in pressed], [self.key_dict[keycode] for keycode in released]) 
                #All done, prepare for the next iteration
                previous_keys = pressed_keys
                previous_modifiers = pressed_modifiers
            sleep(1.0/counter_treshold)
            counter += 1
            if counter == counter_treshold:
                self.send_awake_message()
                counter = 0

if __name__ == "__main__":
    chatpad = Chatpad(port="/dev/ttyUSB1")
    chatpad.listen()
