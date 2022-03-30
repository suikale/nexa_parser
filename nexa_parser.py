#!/usr/bin/python3
# takes a Pulseview .sr file, outputs a text file which has 
# digital states (and their durations). Settings are customisable. 
# The .sr file contains states as binary data, printed as long string
# composed of 8 bit chars. The byte tells the 
# state of all 8 channels at given tick
#
# example:
# 7654 3210     channels
# state         char representation 
# 0100 0101 	E
# 0100 0111 	G
# 0101 0101 	U
# 0101 0111 	W
# 
# suikale 140222

from os.path import exists
from os import remove
import argparse
import zipfile
import re

# default settings: "ANT", 2, False, True

# the channel name defined in Pulseview
channel_name = "ANT"

# output mode
# 0: output precise time spent in state
# 1: output rounded time spent in state
# 2: output only the state
output_mode = 2

# True: write on every state change
# False: write only on HIGH to LOW change
write_on_every_state_change = False

# Set if time spent on state decides the state
# time < 300 µs -> state = 0
# time < 1500 µs -> state = 1
# else -> state = -1
# True: state is based on time
# False: state is real state
state_on_time = True


################################################################################
# theres probably no need to change anything below this line
# argparser setup
parser = argparse.ArgumentParser()
parser.add_argument("FILE", help="Path to a Pulseview .sr file or a parsed .txt file")
parser.add_argument("-r", "--remote", help="print remote id from a parsed .txt file", action="store_true")
args = parser.parse_args()

output_file = ""

def get_config(meta):
    # get config values as bytes
    meta_split = meta.split(bytes('\n', 'utf-8'))
    # convert bytes to strings
    meta_split = [x.decode('utf-8') for x in meta_split]
    
    # sample rate is stored in a row like "samplerate=8 MHz"
    # MHz etc are converted to zeroes and sample rate is stored as int
    r = re.compile("samplerate=")
    sr_str = list(filter(r.match, meta_split))[0].split('=')[1].split()

    zeroes = ""
    if sr_str[1] == "KHz":
        zeroes = "000"
    elif sr_str[1] == "MHz":
        zeroes = "000000"
    elif sr_str[1] == "GHz":
        zeroes = "000000000"

    samplerate = int(sr_str[0] + zeroes)

    # channel is stored in a row like "probe5=channel_name"
    # probe numbers are 1-8, so it is converted to 0-7 for channel
    r = re.compile('probe\d*=' + channel_name)
    channel = int(list(filter(str.isdigit, list(filter(r.match, meta_split))[0].split('=')[0]))[0]) - 1
    
    if channel > 7:
        print("only channels 0-7 are supported ATM")
        exit()

    return samplerate, channel

def read_data(zip_file):
    # TODO: are these filenames same every time?
    data_file = "logic-1-1"
    metadata_file = "metadata"
    try:
        with zipfile.ZipFile(zip_file) as z:
            meta = z.read(metadata_file)
            data = z.read(data_file)
            return meta, data
    except:
        print("reading .sr file failed, exiting")
        exit()

def set_state(time, state):
    if state_on_time:
        if time < 300:
            state = 0
        elif time < 1500:
            state = 1
        else:
            state = -1
    return state

def handle_state_change(time_s, state = -1):
    # convert from seconds to microseconds
    time_us = time_s * 1000000
    out_str = ""

    if output_mode == 0:
        # output precise time spent in state
        out_str = f"time: {time_us:>11.6f} µs, state: {set_state(time_us, state)}\n"

    elif output_mode == 1:
        # output rounded time spent in state
        # round the values to 250, 1250, 2550 or 9150 µs
        if time_us < 300:
            rtime = 250
        elif time_us < 1500:
            rtime = 1250
        elif time_us < 3000:
            rtime = 2550
        else:
            rtime = 9150
        out_str = f"time: {rtime:>4} µs, state: {set_state(rtime, state)}\n"
    
    elif output_mode == 2:
        out_str = str(set_state(time_us, state))

    else:
        print("Unknown output mode, exiting")
        exit()

    append_to_file(out_str, output_file)
    return

def get_bit(byte, i):
    return int((byte & ( 1 << i))!=0)

def append_to_file(string, filename):
    with open(filename, "a") as f:
        f.write(string)

def handle_data(data, samplerate, channel):
    # Data consists of 8 channels which make up 1 byte.
    # 8 channels of data is stored to 1 byte per tick. 
    # Each tick lasts 1/samplerate seconds.
    # Varible "channel" tells which byte holds the state we're interested in
    prev_state = get_bit(data[0], channel)
    delta_time = 1/samplerate
    count = 0

    # check if output file exists, delete it if it does
    if exists(output_file):
        remove(output_file)

    # cycle through data
    for c in data:
        current_state = get_bit(c, channel)
        if current_state == prev_state:
            count = count + 1
        else:
            if write_on_every_state_change:
                handle_state_change(count * delta_time, prev_state)
            else:
                if current_state == 1:
                    handle_state_change(count * delta_time)
            
            prev_state = current_state
            count = 1

def parse_sr_file(sr_file):
    # read data to memory
    meta, data = read_data(sr_file)
    print("read", len(meta), "bytes of metadata")
    print("read", len(data), "bytes of data")

    # get values from metadata
    samplerate, channel = get_config(meta)
    print("sample rate: " + str(samplerate) + ", channel: " + str(channel))

    handle_data(data, samplerate, channel)
    print("wrote output to", output_file)

def parse_txt_file(txt_file):
    # parsed file looks something like this:
    # "101-1-11001011001010110010110011001101001010101011010101001011001010101-1-110"
    # the remote id is stored in the first 52 numbers after -1
    # those 13 * 4 numbers can be decoded to 2 bit pieces which form a 26 bit integer 
    #                      0       1       2       3
    supported_bytes = ["0101", "0110", "1001", "1010"]
    lines = []
    with open(txt_file) as f:
        line = f.readline()
    split_line = line.split("-1")

    remote_line = ""
    for l in split_line:
        if len(l) >= 52:
            remote_line = l
    # remote_line:
    # [13 * 4 chars for remote id][3 * 4 chars for device state]
    if len(remote_line) == 0:
        print("reading remote id failed")
        exit()

    # split the long string to 4 char pieces
    remote_split = [remote_line[i:i+4] for i in range(0, len(remote_line), 4)]

    # decode using supported_bytes
    remote_numbers = []
    for i in remote_split:
        remote_numbers.append(supported_bytes.index(i))
    
    # construct the 26-bit integer, for example
    #    [2, 1, 0, 1, 0, 2, 2, 3, 0, 0, 1, 3, 2  |, 1, 0, 0]
    # -> 10 01 00 01 00 10 10 11 00 00 01 11 10
    # -> 38054942
    remote_id = ""
    for i in range(0, 13):
        # adds 2 bits to the end of the string
        remote_id = remote_id + bin(remote_numbers[i])[2:].zfill(2)
    return int(remote_id, 2)

if __name__ == '__main__':
    input_file = args.FILE
    if args.remote:
        print("remote id: ", parse_txt_file(input_file))
        exit()

    # output filename is same as input but with .txt extension
    try:
        output_file = input_file[:input_file.index(".sr")] + ".txt"
    except:
        print("wrong file format, exiting")
        exit()    
    parse_sr_file(input_file)