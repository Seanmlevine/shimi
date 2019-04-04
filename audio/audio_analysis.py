import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from pyo import *
from audio.singing import Singing
import multiprocessing

LEFT = 0
RIGHT = 1


class AudioAnalysisClient:
    """Client for doing audio analysis using pyo on a separate process for maximal efficiency."""

    def __init__(self):
        """Establishes communication with and initializes audio server."""
        (self.client_pipe, self.server_pipe) = multiprocessing.Pipe()
        self.analysis_server = AudioAnalysisServer(self.server_pipe)
        self.analysis_server.start()

    def _call(self, function_string, *args, **kwargs):
        """Used to pass a function call to the audio server.

        Args:
            function_string: The name of the server function to call.
            *args: A tuple of any arguments to be passed to the server, must be serializable.
            **kwargs: A dict of any keword arguments to be passed to the server, must be serializable.

        Returns:
            A response from the server.
        """
        call_obj = {
            "function": function_string,
            "args": args,
            "kwargs": kwargs
        }

        self.client_pipe.send(call_obj)
        res = self.client_pipe.recv()
        return res

    """
        These functions are used to interact with the audio server. Be sure that the functions implemented in the 
        server process return some value, as the _call function waits for a response to return.
    """

    def get_freq(self):
        return self._call("get_freq")

    def get_freq_midi(self):
        return self._call("get_freq_midi")

    def sing_midi(self, midi_path):
        return self._call("sing_midi", midi_path)

    def sing_audio(self, audio_path, extraction_type):
        return self._call("sing_audio", audio_path, extraction_type)


class AudioAnalysisServer(multiprocessing.Process):
    def __init__(self, connection, duplex=False):
        """Runs audio processing and analysis with pyo in a dedicated process.

        Args:
            connection: A multiprocessing.Pipe used to communicate with the client.
            duplex: A bool specifying whether or not to configure microphone input in addition to audio output.
        """
        super(AudioAnalysisServer, self).__init__()
        self.daemon = False
        self._terminated = False
        self._connection = connection
        self.duplex = duplex
        self.singing_object = None

    def run(self):
        """Initializes the pyo audio server and waits for function calls from the client."""
        self.initialize_server()

        # If input, do some analysis
        if self.duplex:  # WARNING, does not work with singing in parallel, TODO: try input in a new process
            in_0 = Input(chnl=0, mul=1)
            in_1 = Input(chnl=1, mul=1)
            in_mono = in_0 + in_1
            in_analysis = 15 * in_mono

            self.freq_hz = Yin(in_analysis)
            self.freq_midi = FToM(self.freq_hz)

        while not self._terminated:
            to_do = self._connection.recv()  # Blocking read to get function calls from the client
            func = getattr(self, to_do["function"])
            args = to_do["args"]
            kwargs = to_do["kwargs"]
            res = func(self, *args, **kwargs)
            self._connection.send(res)

        self.server.stop()

    def stop(self):
        self._terminated = True

    def initialize_server(self):
        """Starts the pyo audio server."""
        pa_list_devices()

        # Mac testing
        # self.server = Server()
        if self.duplex:
            self.server = Server(sr=16000, ichnls=4)
            self.server.setInOutDevice(2)
        else:
            self.server = Server(sr=16000, duplex=0)
            self.server.setOutputDevice(2)
        self.server.deactivateMidi()
        self.server.boot().start()
        self.singing_object = Singing()

    def get_freq(self, *args, **kwargs):
        return self.freq_hz.get()

    def get_freq_midi(self, *args, **kwargs):
        return self.freq_midi.get()

    def sing_midi(self, *args, **kwargs):
        midi_path = args[1]
        self.singing_object.sing_midi(midi_path)
        return 'ok'

    def sing_audio(self, *args, **kwargs):
        audio_path = args[1]
        extraction_type = args[2]
        self.singing_object.sing_audio(audio_path, extraction_type)
        return 'ok'

if __name__ == '__main__':
    a = AudioAnalysisClient()
