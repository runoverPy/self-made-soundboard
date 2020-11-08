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
from button import create_button as cb, Button



class Delayer(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            time.sleep(0.1)
            if(keyboard.is_pressed("esc")):
                break

class Soundboard(Button):
    def __init__(self):
        self.recording_key = "`"
        self.used_filenames = []
        self.filename_length = 9
        self.all_buttons = []
        print("restoring previous buttons")
        self.restore_buttons()

    def restore_buttons(self):
        try:
            self.savefile = open("soundboard/sound_masterfile.txt", "r+")
            for self.line in self.savefile:
                try:
                    self.recalled_filename = re.match(r"(\S+\.wav)(\s+)(\S+)", self.line) 
                    self.used_filenames.append(self.recalled_filename.group(1))
                    self.all_buttons.append(Button(self.recalled_filename.group(1), self.recording_key, self.recalled_filename.group(3)))
                except AttributeError:
                    print("error, contents of line improper:", self.line)
        except FileNotFoundError:
            self.newfile = open("soundboard/sound_masterfile.txt", "w")
            self.newfile.close()
        print(len(self.all_buttons), " buttons were restored")

    def create_filename(self, length):
        self.result = ""
        for self.i in range(length -4):
            self.result += str(random.randint(0, 9))
        return self.result + ".wav"

    def create_button(self):
        cb()

    def continuous_parsing(self):
        for button in self.all_buttons:
            button.check_play()

soundboard = Soundboard()
keyboard.add_hotkey(soundboard.recording_key, soundboard.create_button)
while True:
    if keyboard.is_pressed("esc"):
        break