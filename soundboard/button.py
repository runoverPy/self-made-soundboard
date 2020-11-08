import time
import keyboard
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import random
import re
import argparse
import tempfile
import queue
import sys
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy
from threading import Thread
from audio import Audio



class Button(Audio):
    def __init__(self, filename, recording_key, trigger_key = ""):
        self.trigger_key = trigger_key
        self.recording_key = recording_key
        Audio.__init__(self, filename, self.recording_key)
        
        if(self.trigger_key == ""):
            self.record_audio()
            time.sleep(0.5)
            print("awaiting button designation")
            
            def return_key():    
                def callback(e):
                    nonlocal return_value
                    return_value = e
                return_value = ""
                keyboard.hook(callback=callback)
                while return_value == "":
                    time.sleep(0.05)
                return re.match(r"(\S+\()(\S)((\s|\S)+)", str(return_value)).group(2)
            self.trigger_key = return_key()
            print("key input (", self.trigger_key, ") recieved. compiling button")
            self.file = open("soundboard/sound_masterfile.txt", "r+")
            self.file.write(str(self.filename + " " + self.trigger_key))
            self.file.close()

    def check_play(self):
        if keyboard.is_pressed(self.trigger_key):
            self.play_audio

def create_filename(length):
    result = ""
    for i in range(length -4):
        result += str(random.randint(0, 9))
    return result + ".wav"

def create_button():
    keyboard.wait("`")    
    print("button creation in progress")
    test = Button(create_filename(9), "`")
