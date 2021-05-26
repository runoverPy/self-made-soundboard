from platform import win32_edition
import time
import keyboard
import sounddevice as sd
import soundfile as sf
import random
import re
import argparse
import queue
import sys
from threading import Thread
from playsound import playsound
import json


def create_filename(length):
    result = ""
    for i in range(length -4):
        result += str(random.randint(0, 9))
    return result + ".wav"


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


class Button:
    def __init__(self, filename, recording_key, trigger_key = ""):
        self.trigger_key = trigger_key
        self.recording_key = recording_key
        self.filename = filename
        if self.trigger_key == "":
            self.record() 
        self.set_key()


    def identity(self):
        return {"file": self.filename, "key": self.trigger_key}


    def record(self):
        print("starting new recording")

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-l', '--list-devices', action='store_true', help='show list of audio devices and exit')
        args, remaining = parser.parse_known_args()
        if args.list_devices:
            print(sd.query_devices())
            parser.exit(0)
            sys.exit("Error: no input devices found")
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[parser])
        parser.add_argument('filename', nargs='?', metavar='FILENAME', help='audio file to store recording to')
        parser.add_argument('-d', '--device', type=int_or_str, help='input device (numeric ID or substring)')
        parser.add_argument('-r', '--samplerate', type=int, help='sampling rate')
        parser.add_argument('-c', '--channels', type=int, default=1, help='number of input channels')
        parser.add_argument('-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
        args = parser.parse_args(remaining)

        savingqueue = queue.Queue()


        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            args.samplerate = int(device_info['default_samplerate'])
        if args.filename is None:
            print("filename is none")
            args.filename = self.filename

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(args.filename, mode='x', samplerate=args.samplerate, channels=args.channels, subtype=args.subtype) as file:

            def callback(indata, frames, time, status):
                """This is called (from a separate thread) for each audio block."""
                # nonlocal savingqueue
                if status:
                    print(status, file=sys.stderr)
                savingqueue.put(indata.copy())

            with sd.InputStream(samplerate=args.samplerate, device=args.device, channels=args.channels, callback=callback):
                while keyboard.is_pressed("`"):
                    file.write(savingqueue.get())
         
        print("recording finished")
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
        print(f"key input ({self.trigger_key}) recieved.")

    def set_key(self):
        def callback():
            playsound(self.filename)
        keyboard.add_hotkey(self.trigger_key, callback)


class Soundboard():
    def __init__(self):
        self.recording_key = "`"
        self.used_filenames = []
        self.filename_length = 9
        self.all_buttons = []
        print("restoring previous buttons")
        self.restore_buttons()

    def run(self):
        self.restore_buttons()

    def restore_buttons(self):
        with open("soundboard/keyfile.json", "r") as keys:
            for soundbyte in json.load(keys):
                self.all_buttons.append(Button(soundbyte["file"], self.recording_key, soundbyte["key"]))
                self.used_filenames.append(soundbyte["file"])
        print(f"{len(self.all_buttons)} buttons were restored")


    def save_buttons(self):
        with open("soundboard/keyfile.json", "w") as keys:
            json.dump(list(button.identity() for button in self.all_buttons), keys, indent=4)


    def create_filename(self, length):
        result = ""
        for i in range(length):
            result += str(random.randint(0, 9))
        return result + ".wav"


    def create_button(self):
        keyboard.wait("`")    
        print("button creation in progress")
        self.all_buttons.append(Button(create_filename(9), self.recording_key))

if __name__ == "__main__":
    soundboard = Soundboard()
    while True:
        if keyboard.is_pressed("esc"):
            break
        elif keyboard.is_pressed("`"):
            soundboard.create_button()
    soundboard.save_buttons()