
from itertools import zip_longest
import math
import wave
import csv
import os

# https://docs.python.org/3/library/wave.html

def stream(file):
    with wave.open(file, mode='rb') as river:
        river.rewind()

        ch = river.getnchannels()
        assert ch == 1

        w = river.getsampwidth()

        r = river.getframerate() // w

        print('FILE :', file)
        print('CHANNELS :', ch)
        print('SAMPLE WIDTH (bytes) :', w)
        print('FRAMES PER SEC: ', r)
        #print('\n')

        total_frames = river.getnframes() // w

        for frame_id in range(total_frames):
            yield (frame_id / r, normalize(river.readframes(1)))
            river.setpos(river.tell() + 1)
        
        #print('CHANNELS :', ch)
        #print('SAMPLE WIDTH (bytes) :', w)
        #print('FRAMES PER SEC: ', r)
        print('done\n')

        # null terminator
        yield (frame_id / r, normalize(river.readframes(1)))


def normalize(frame):
    val = int.from_bytes(frame, byteorder='little')
    
    # manual conversion of two's compliemnt encoded 16-bit int
    if (0x8000 & val):
        val -= 0x10000

    return val / (2**15)

def extract(stream, update_prop=0.2, ready_thresh=0.02, reset_thresh=0.001):

    diff_mov_avg = 0
    diff = 0

    ready = True

    peaks = 0
    last_peak = 0
    
    sig = 0

    # extract params:
    #  change prop 0.2 
    #  retained ma 0.8 = 1 - 0.2
    #  
    try:
        while True:

            t1, s1 = next(stream)
            t2, s2 = next(stream)

            diff = abs(s2 - s1)
            diff_mov_avg = (1 - update_prop) * diff_mov_avg + update_prop * diff

            #print(t2, diff_mov_avg)

            """ """
            sig = -1 if ready else -2

            if ready and abs(diff_mov_avg) > ready_thresh:
                ready = False
                #print('ready = False at t =', t2)

                peaks += 1
                last_peak = t2
                yield t2

            if not ready and abs(diff_mov_avg) < reset_thresh:
                ready = True
                #print('ready = True at t =', t2)
            """ """

            if t2 - last_peak > 0.20:
                yield sig

    except StopIteration:
        pass

    print("PEAK COUNT :", peaks)
    print("\n")

def run():
    dripFiles = os.listdir('data/')

    headers = []
    cols = []

    for dripFile in dripFiles:

        headers.append(dripFile)
        col = []

        ready_thresh = 0.022
        reset_thresh = 0.00075
        d_ready_thresh = -ready_thresh / 15
        d_reset_thresh =  reset_thresh / 15

        last_peak_time = 0

        while(not col):
            for peak_time in extract(stream('data/' + dripFile), ready_thresh=ready_thresh, reset_thresh=reset_thresh):

                if(peak_time < 0):
                    col = []
                    ready_thresh += d_ready_thresh if peak_time == -1 else 0
                    reset_thresh += d_reset_thresh if peak_time == -2 else 0
                    print('bad data after', last_peak_time, 'SIG :', peak_time)
                    print('updating extract params\n')
                    break
                
                last_peak_time = peak_time
                col.append(peak_time)

        cols.append(col)

    rows = zip_longest(*cols, fillvalue='')

    #print(rows)

    with open('res/out.csv', 'w', newline='') as out:
        writer = csv.writer(out, delimiter=',')

        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)

            



run()

# https://docs.python.org/3/library/csv.html
"""
with open('out1.csv', 'w', newline='') as out:

    writer = csv.writer(out, delimiter=' ')

    for peak_time in extract(stream('3 9 cm -1.wav')):
        writer.writerow([peak_time])
"""
"""
for time, frame in stream('pitterpatter.wav'):

    val = int.from_bytes(frame, byteorder='little')
    
    # manual conversion of two's compliemnt encoded 16-bit int
    if (0x8000 & val):
        val -= 0x10000

    print(time, val / (2**15))
"""