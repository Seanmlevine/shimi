import os, sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from PyInquirer import prompt
from webapp.webapp_controller import SingingProcessWrapper
from motion.jam import Jam
from shimi import Shimi
from librosa.core import load
from librosa.beat import tempo as estimate_tempo
from spotify.login import get_authorized_spotipy
import sqlite3
import multiprocessing
import os.path as op
import time
import pickle

AUDIO_PATH = op.join(os.getcwd(), "audio_files")
CNN_PATH = op.join(os.getcwd(), "cnn_outputs")

available_ids = ['TRKIZWL128EF342C5A', 'TRCLINP12903CB007B', 'TRCTVZG128E078ED8D', 'TRCPTQP128F423A80E',
                 'TRCDWQJ128F146DCD1', 'TRFZNJO128F42759D9', 'TRBSDJW128F92D6E19', 'TRFLBTX128F4257817',
                 'TRFUVKB12903CB0FE3', 'TRALLSG128F425A685', 'TRAIFLV12903CCFECD', 'TRAIQCB12903CEB776',
                 'TRADCVS128F932D857', 'TRAGHOR128F9333E26', 'TRZVDJK128F932562D', 'TRZMWZX128F930BECD',
                 'TRZUDGY128F14609BF', 'TRZSYMA12903CB261F', 'TRXCWZL128E0793240', 'TRXZXTP12903CB667B',
                 'TRXXGYO128F4277EA3', 'TRXIEJH128C7196C1D', 'TRXQNRF128F4297E94', 'TRXVFTR128F931DED3',
                 'TRXHJAV128F934C918', 'TRLFCUS128F933B4A9', 'TRLLWIN128F92CB71D', 'TRLTLJC128F9345529',
                 'TRRXXYN128F9317B93', 'TRRIIEN128F92E0443', 'TRRNARX128F4264AEB', 'TRRYJPZ128F930C2BE',
                 'TRRUDYP128F426013C', 'TRTPGLA128F9314F30', 'TRTVDWN128F42678A4', 'TRTEIGY12903CFCC9E',
                 'TRTGHUP128F4260A65', 'TRTGSAR128F42A53DA', 'TROUHQM128F92C5777', 'TRIAYPJ128F4288F8F',
                 'TRIRCFN128F4280243', 'TRIDAFI128F4255BD9', 'TRIHFTE128F930944E', 'TRISOVE12903CB8135',
                 'TRGJMGK12903CAFC9D', 'TRQRTXN128EF356AE3', 'TRQDNCX128F9314FD0', 'TRQMSCD128F426A3F5',
                 'TRQMGQY128EF3406A7', 'TRQJYKE128F42ADAEB', 'TRPIKAH128F426372C', 'TRPPLIU128F4260C6E',
                 'TRPULWH128E0788797', 'TRPEAEG128F1458AAB', 'TRNNZCB128E0782BC7', 'TRNVNJD12903CE58BB',
                 'TRYNGJR128F92CC677', 'TRYVBMA128E0789D39', 'TRYDLPB12903CB0328', 'TRVLECC12903D0D4E9',
                 'TRVBBAX128F92F91B0', 'TRDZKYG128F92E3640', 'TRDXSQX128F930BCB9', 'TRDLKTB128F9340580',
                 'TRDPYFO128F425581C', 'TRDEGGZ128F1498BDA', 'TRDBEXV128F42A4ABC', 'TRHKSZF128F14AD56D',
                 'TRHLVSZ12903CF5496', 'TRHRCXK128F4263C4C', 'TRHOIJR128F93370DA', 'TRHVEET12903CCE9EF',
                 'TRHHKMC128F931E0AB', 'TRHJVLH12903D04F44', 'TRHEOII12903CB23D6', 'TRMKYUC12903D0F58F',
                 'TRMRHAD12903CC0130', 'TRMTRWB128F42A0436', 'TRMJSWT12903CA8AE1', 'TRMGBWD128F930F948',
                 'TRUAGKW128F9311E03', 'TRUGTVW128F92E83BC', 'TRJDNQD128F931C103', 'TRJUIAR128F424169C',
                 'TRSFNHG128F427DF40', 'TRSAMWU128F42636B8', 'TRSPCUZ128F92E8CD5', 'TRSNCXP128F1470E53',
                 'TREISPC128F932E2DC', 'TREVDFX128E07859E0', 'TRESNUQ128F42ACF91', 'TREGGML12903CC0740',
                 'TRWFAIW128F4269A6F', 'TRWOLRE128F427D710', 'TRWQAFX128F428DBB0', 'TRWYDVA128F92FDD86',
                 'TRWDHRF12903CB0249', 'TRWMHMP128EF34293F', 'TRWJIBT128F425F109', 'TRWBTPB128EF34A8A1',
                 'TRWGVPP128F42970A9', 'TRBKFPM12903CE39C7', 'TRBOEFO128F92FC62E', 'TRBPBFY128F426DE70',
                 'TRBMITH128F4282301']

choices = []

song_info = {}


def make_song_options():
    conn = sqlite3.connect('/media/nvidia/disk2/shimi_library.db')
    c = conn.cursor()
    for msd_id in available_ids:
        c.execute("select title, artist_name, release from songs where msd_id=?", [msd_id])
        song = c.fetchone()
        song_info[msd_id] = {}
        song_info[msd_id]['title'] = song[0]
        song_info[msd_id]['artist_name'] = song[1]
        song_info[msd_id]['release'] = song[2]

        choices.append({
            'name': '"%s" by %s (on %s)' % (song[0], song[1], song[2]),
            'value': msd_id
        })


def get_song_info():
    global song_info, choices
    if op.exists("song_info.p"):
        song_info = pickle.load(open("song_info.p", 'rb'))
        choices = song_info['choices']
    else:
        make_song_options()
        song_info['choices'] = choices
        spotify_client = get_authorized_spotipy('rytrose')

        for msd_id in available_ids:
            song_filename = op.join(AUDIO_PATH, "%s.wav" % msd_id)
            y, sr = load(song_filename)
            song_info[msd_id]['length'] = y.shape[0] / sr
            song_info[msd_id]['librosa_tempo'] = 60 / float(estimate_tempo(y, sr))

            if not 'danceability' in song_info[msd_id].keys():
                search = spotify_client.search(song_info[msd_id]['title'])
                uri = ""
                for item in search['tracks']['items']:
                    print("Title: %s" % item['name'])
                    artists = "Artists:"
                    for artist in item['artists']:
                        artists += " %s" % artist['name']
                    print(artists)
                    print("Album: %s" % item['album']['name'])
                    correct = input("Does this match: %s by %s on %s? " % (
                    song_info[msd_id]['title'], song_info[msd_id]['artist_name'], song_info[msd_id]['release']))
                    if correct == "y":
                        uri = item['uri']
                        break
                if uri != "":
                    features = spotify_client.audio_features(uri)[0]
                    song_info[msd_id]['danceability'] = features['danceability']
                    song_info[msd_id]['energy'] = features['energy']
                    song_info[msd_id]['loudness'] = features['loudness']
                    song_info[msd_id]['speechiness'] = features['speechiness']
                    song_info[msd_id]['acousticness'] = features['acousticness']
                    song_info[msd_id]['instrumentalness'] = features['instrumentalness']
                    song_info[msd_id]['liveness'] = features['liveness']
                    song_info[msd_id]['valence'] = features['valence']

            pickle.dump(song_info, open("song_info.p", 'wb'))

        pickle.dump(song_info, open("song_info.p", 'wb'))


if __name__ == '__main__':
    shimi = Shimi()
    get_song_info()

    (client_pipe, server_pipe) = multiprocessing.Pipe()
    singing_process = SingingProcessWrapper(server_pipe)
    singing_process.start()
    time.sleep(2)

    while True:
        try:
            os.system('clear')
            chosen = prompt([{
                'type': 'list',
                'name': 'msd_id',
                'message': 'Choose a song for Shimi to sing!',
                'choices': choices
            }])

            msd_id = chosen['msd_id']
            song_filename = op.join(AUDIO_PATH, "%s.wav" % msd_id)
            cnn_filename = op.join(CNN_PATH, "cnn_%s.txt" % msd_id)

            singing_opts = {
                "audio_file": song_filename,
                "extraction_type": "cnn",
                "analysis_file": cnn_filename
            }

            length = song_info[msd_id]['length']
            tempo = song_info[msd_id]['librosa_tempo']

            move = Jam(shimi, tempo, length)

            client_pipe.send(singing_opts)
            res = client_pipe.recv()

            move.start()
            move.join()
            shimi.initial_position()

        except KeyboardInterrupt:
            print("Exiting...")
            break
