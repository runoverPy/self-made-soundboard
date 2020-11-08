import time
import keyboard
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
import argparse
import queue
import sys
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy



def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

class Audio():
    def __init__(self, filename, record_key):
        self.filename = filename
        self.fs = 44100  # Sample rate
        self.record_key = record_key

        
    def play_audio(self):
        self.data, self.fs = sf.read(self.filename, dtype='float32')
        sd.play(self.data, self.fs)
        self.status = sd.wait()

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