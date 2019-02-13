import os, sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from audio.audio_analysis import Sample
import numpy as np
import os.path as op
from subprocess import Popen, PIPE
import soundfile as sf
import pickle
from pyo import *
from librosa.beat import tempo as estimate_tempo
import time
import random


class MelodyExtraction:
    def __init__(self, path):
        self.path = path
        self.sound_data, self.sr = sf.read(self.path, always_2d=True)
        self.tempo = estimate_tempo(self.sound_data[:, 1], self.sr)[0] / 60
        self.length_samples = self.sound_data.shape[0]
        self.length_seconds = self.length_samples * (1 / self.sr)
        self.abs_path = op.abspath(self.path)
        self.name = "_".join(self.abs_path.split('/')[-1].split('.')[:-1])

        self.deep_learning_path = "/media/nvidia/disk1/Vocal-Melody-Extraction"
        self.deep_learning_model_path = op.join(self.deep_learning_path, "pretrained_models", "Seg")
        self.deep_learning_data = None
        self.deep_learning_timestamps = None

        self.run_melodia_path = "/home/nvidia/shimi/audio"
        self.melodia_data = None
        self.melodia_timestamps = None

    def deep_learning_extraction(self):
        if not op.exists("deep_learning_" + self.name + ".txt"):
            command_string = "python3.5 " + op.join(self.deep_learning_path,
                                                    "VocalMelodyExtraction.py") + " --input_file " + self.abs_path + \
                             " -m " + self.deep_learning_model_path + " --output_file " + "deep_learning_" + self.name

            process = Popen(command_string.split(' '), stdout=PIPE, bufsize=1, universal_newlines=True)

            # Wait until the process is finished  to continue
            for line in process.stdout.readline():
                if line == "FINISHED":
                    print("Deep learning melody extraction complete.")
                    break

        deep_learning_data = np.loadtxt("deep_learning_" + self.name + ".txt")
        self.deep_learning_data = deep_learning_data[:, 1]
        np.place(self.deep_learning_data, self.deep_learning_data <= 0, 0)
        num_points = self.deep_learning_data.shape[0]
        self.deep_learning_timestamps = [(i / num_points) * self.length_seconds for i in range(num_points)]
        self.deep_learning_data, self.deep_learning_timestamps = self.process_data(self.deep_learning_data,
                                                                                   self.deep_learning_timestamps)

    def melodia_extraction(self):
        if not op.exists("melodia_" + self.name + ".p"):
            command_string = "exagear -- " + op.join(self.run_melodia_path,
                                                     "run_melodia.sh") + " " + self.abs_path + " " + self.name

            input("Please run the following in a new shell, and press enter when it is done:\n%s\n" % command_string)

        melodia_data = pickle.load(open("melodia_" + self.name + ".p", "rb"))
        self.melodia_data = melodia_data["frequencies"]
        self.melodia_timestamps = melodia_data["timestamps"]
        self.melodia_data, self.melodia_timestamps = self.process_data(self.melodia_data, self.melodia_timestamps)

    def process_data(self, melody_data, timestamps):
        np.place(melody_data, melody_data <= 0, 0)
        data_without_zeros = []
        timestamps_without_zeros = []

        for freq, timestamp in zip(melody_data, timestamps):
            if freq > 0:
                data_without_zeros.append(freq)
                timestamps_without_zeros.append(timestamp)

        data_len = len(melody_data)
        delta = self.tempo / 10

        timestamps_to_interpolate = []
        i = 0
        j = 0
        while melody_data[i] < 0:  # Move to first vocalization
            i += 1
            j += 1

        while i < data_len:
            while i < data_len and melody_data[i] > 0:
                i += 1
                j += 1
            # current frequency is 0
            while j < data_len and melody_data[j] <= 0:
                j += 1
            # current frequency is not 0
            if j < data_len:
                if timestamps[j] - timestamps[i] < delta:
                    for t in range(i, j):
                        timestamps_to_interpolate.append(timestamps[t])
            i = j

        print("Interpolating %d points." % len(timestamps_to_interpolate))

        interpolated_values = np.interp(timestamps_to_interpolate, timestamps_without_zeros, data_without_zeros)
        for i, val in enumerate(interpolated_values):
            melody_data[np.where(timestamps == timestamps_to_interpolate[i])[0]] = val

        return melody_data, timestamps


class Singing:
    def __init__(self, path, extraction_type, duplex=False):
        self.path = path
        self.duplex = duplex
        self.server = Server()
        pa_list_devices()

        # Mac testing
        self.server.setInputDevice(1)
        self.server.setOutputDevice(0)
        # if self.duplex:
        #     self.server = Server(sr=16000, ichnls=4)
        #     self.server.setInOutDevice(2)
        # else:
        #     self.server = Server(sr=16000, duplex=0)
        #     self.server.setOutputDevice(2)
        self.server.deactivateMidi()
        self.server.boot().start()

        self.melody_extraction = MelodyExtraction(self.path)
        if extraction_type == "melodia":
            self.melody_extraction.melodia_extraction()
            self.melody_data = self.melody_extraction.melodia_data
            self.melody_timestamps = self.melody_extraction.melodia_timestamps
        else:
            self.melody_extraction.deep_learning_extraction()
            self.melody_data = self.melody_extraction.deep_learning_data
            self.melody_timestamps = self.melody_extraction.deep_learning_timestamps

        self.length_seconds = self.melody_extraction.length_seconds

        self.shimi_samples = []

        self.vocal_paths = ["shimi_vocalization.wav", "shimi_vocalization2.wav", "shimi_vocalization3.wav",
                            "shimi_vocalization4.wav"]

        for path in self.vocal_paths:
            shimi_sample = Sample(path)
            self.shimi_samples.append(shimi_sample)

        self.shimi_sample = random.choice(self.shimi_samples)

        self.speed_index = 0

        self.song_sample = SfPlayer(self.path, mul=0.2)

        self.speeds = []
        current_start = -1
        current_end = -1
        for freq, timestamp in zip(self.melody_data, self.melody_timestamps):
            if freq > 0 and current_start < 0:
                current_start = timestamp
            if freq <= 0 and current_start > 0:
                current_end = timestamp
                speed = self.shimi_sample.LENGTH / (current_end - current_start)
                self.speeds.append(speed)
                current_start = -1
                current_end = -1
        if current_start > 0 and current_end < 0:  # catch melody that doesn't end with silence
            current_end = self.melody_timestamps[-1]
            speed = self.shimi_sample.LENGTH / (current_end - current_start)
            self.speeds.append(speed)

        self.frequency_timestep = self.melody_timestamps[1] - self.melody_timestamps[0]
        self.frequency_setter = Pattern(self.set_freq, time=float(self.frequency_timestep))
        self.frequency_index = 1
        self.prev_freq = self.melody_data[0]

        print("Waiting for PV Analysis to be done...")
        wait_time = 3
        for i in range(wait_time):
            print("%d..." % (wait_time - i))
            time.sleep(1.0)

    def set_freq(self):
        new_freq = self.melody_data[self.frequency_index]
        new_transposition = float(new_freq / 440)
        self.shimi_sample.set_transposition(new_transposition)

        if self.prev_freq <= 0 and new_freq > 0:
            self.start_vocal()
        elif self.prev_freq > 0 and new_freq <= 0:
            self.end_vocal()

        self.prev_freq = new_freq

        if self.frequency_index == len(self.melody_data) - 1:  # Stop it because otherwise it will loop forever
            self.frequency_setter.stop()
            for s in self.shimi_samples:
                s.stop()
            self.song_sample.stop()

        self.frequency_index = (self.frequency_index + 1) % len(self.melody_data)

    def start_vocal(self):
        self.shimi_sample.set_speed(self.speeds[self.speed_index])
        self.shimi_sample.play()
        self.speed_index = (self.speed_index + 1) % len(self.speeds)

    def end_vocal(self):
        self.shimi_sample.stop()
        self.shimi_sample = random.choice(self.shimi_samples)

    def sing(self):
        self.frequency_setter.play()
        self.song_sample.out()


if __name__ == '__main__':
    s = Singing("skinny_love.wav", "melodia")
    s.sing()