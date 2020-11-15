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
from playsound import playsound 

class Delayer(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        while True:
            time.sleep(0.1)
            if(keyboard.is_pressed("esc")):
                break



def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

class Audio():
    def __init__(self, filename, path, record_key):
        self.filename = filename
        self.fs = 44100  # Sample rate
        self.record_key = record_key
        self.path = path

        
    def play_audio(self):
        playsound(self.path + self.filename)


    def record_audio(self):
        print("starting new recording")

        self.parser = argparse.ArgumentParser(add_help=False)
        self.parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
        self.args, remaining = self.parser.parse_known_args()
        if self.args.list_devices:
            print(sd.query_devices())
            self.parser.exit(0)
        self.parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[self.parser])
        self.parser.add_argument('filename', nargs='?', metavar='FILENAME', help='audio file to store recording to')
        self.parser.add_argument('-d', '--device', type=int_or_str, help='input device (numeric ID or substring)')
        self.parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
        self.parser.add_argument('-c', '--channels', type=int, default=1, help='number of input channels')
        self.parser.add_argument('-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
        self.args = self.parser.parse_args(remaining)

        self.q = queue.Queue()


        def callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            self.q.put(indata.copy())


        if self.args.samplerate is None:
            device_info = sd.query_devices(self.args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            self.args.samplerate = int(device_info['default_samplerate'])
        if self.args.filename is None:
            self.args.filename = self.filename

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(self.args.filename, mode='x', samplerate=self.args.samplerate,
                            channels=self.args.channels, subtype=self.args.subtype) as file:
            with sd.InputStream(samplerate=self.args.samplerate, device=self.args.device,
                                channels=self.args.channels, callback=callback):
                while True:
                    file.write(self.q.get())
                    if(not keyboard.is_pressed("`")):
                        break             
        
        print("recording finished")



class Button(Audio):
    def __init__(self, filename, path, recording_key, trigger_key = ""):
        self.trigger_key = trigger_key
        self.recording_key = recording_key
        self.path = path
        Audio.__init__(self, filename, path, self.recording_key)
        if self.trigger_key == "":
            self.record() 
        self.set_key()

    def check_play(self):
        if keyboard.is_pressed(self.trigger_key):
            self.play_audio

    def record(self):
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

    def set_key(self):
        def callback():
            self.play_audio()
        keyboard.add_hotkey(self.trigger_key, callback)


def create_filename(length):
    result = ""
    for i in range(length -4):
        result += str(random.randint(0, 9))
    return result + ".wav"



class Soundboard():
    def __init__(self):
        self.recording_key = "`"
        self.path = ""
        self.used_filenames = []
        self.filename_length = 9
        self.all_buttons = []
        print("restoring previous buttons")
        self.restore_buttons()

    def clear_file(self):
        self.newfile = open("soundboard/sound_masterfile.txt", "w")
        self.newfile.close()

    def restore_buttons(self):
        try:
            self.savefile = open("soundboard/sound_masterfile.txt", "r+")
            for self.line in self.savefile:
                try:
                    self.recalled_filename = re.match(r"(\S+\.wav)(\s+)(\S+)", self.line) 
                    self.used_filenames.append(self.recalled_filename.group(1))
                    self.all_buttons.append(Button(self.recalled_filename.group(1), self.path, self.recording_key, self.recalled_filename.group(3)))
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
        keyboard.wait("`")    
        print("button creation in progress")
        self.all_buttons.append(Button(create_filename(9), "`", self.recording_key))



soundboard = Soundboard()
while True:
    if keyboard.is_pressed("esc"):
        break
    elif keyboard.is_pressed("`"):
        soundboard.create_button()