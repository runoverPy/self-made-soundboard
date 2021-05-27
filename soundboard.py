import sys
import json
import queue
from datetime import datetime

import keyboard
import sounddevice as sd
import soundfile as sf
from playsound import playsound

def create_filename():
    time = datetime.now()
    name = f"{str(time.year)[2:]}-{time.month}-{time.day}:{time.hour}-{time.minute}-{time.second}"
    return "soundboard/" + str(hex(hash(name)))[2:] + ".wav"

class Button:
    def __init__(self, filename, trigger_key):
        self.trigger_key = trigger_key
        self.soundfile = filename
        keyboard.add_hotkey(self.trigger_key, callback=playsound, args=(self.soundfile))


    @classmethod
    def record(cls, newfile):
        print("starting new recording")
        device_info = sd.query_devices(kind='input')
        samplerate = int(device_info['default_samplerate'])

        savingqueue = queue.Queue()
        def callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            savingqueue.put(indata.copy())

        # Make sure the file is opened before recording anything:
        with sf.SoundFile(newfile, mode='x', samplerate=samplerate, channels=2) as file: 
            with sd.InputStream(samplerate=samplerate, channels=2, callback=callback):
                while keyboard.is_pressed("`"):
                    file.write(savingqueue.get())
        
        print("recording finished", "awaiting button designation", sep="\n")
        trigger_key = keyboard.read_key()
        print(f"key input ({trigger_key}) recieved.")

        return cls(newfile, trigger_key)


    def identity(self):
        return {"file": self.soundfile, "key": self.trigger_key}


class Soundboard():
    def __init__(self):
        self.all_buttons = []


    def main(self):
        try:
            self.restore_buttons()
            while not keyboard.is_pressed("esc"):
                if keyboard.is_pressed("`"):
                    self.create_button()
        finally:
            self.save_buttons()


    def restore_buttons(self):
        print("Restoring previous buttons")
        with open("soundboard/keyfile.json", "r") as keys:
            for soundbyte in json.load(keys):
                self.all_buttons.append(Button(soundbyte["file"], soundbyte["key"]))
        print(f"{len(self.all_buttons)} buttons were restored")


    def create_button(self):
        print("Button creation in progress")
        self.all_buttons.append(Button.record(create_filename()))


    def save_buttons(self):
        print("Saving state")
        with open("soundboard/keyfile.json", "w") as keys:
            json.dump(list(button.identity() for button in self.all_buttons), keys, indent=4)


if __name__ == "__main__":
    Soundboard().main()