import struct
import sys
import time
import os

INDICES = {}

#Similar to the chunk structure, but it is flat, so variables of the same name will be overwritten.
#This gives a list of the most recently set variables without having to work back in a nested
# dictionary, assuming variable names are globally unique.
VARS = {}

MARKERS = {}

ABORT = False

open("log.txt", "w").truncate()
def trace(text):
    pass
    #log_file = open("log.txt", "a")
    #log_file.write(text + "\n")
    #print(text)

#makes unpacking binary values easier
def unpack(bin_file, data_type, length_arg=0):
    #integer or unsigned integer
    if data_type == "i" or data_type == "I":
        return int(struct.unpack(data_type, bin_file.read(4))[0])
    #short or unsigned short
    elif data_type == "h" or data_type == "H":
        return int(struct.unpack(data_type, bin_file.read(2))[0])
    #float
    elif data_type == "f":
        return float(struct.unpack(data_type, bin_file.read(4))[0])
    #string
    elif data_type == "s":
        return struct.unpack(str(length_arg) + data_type, bin_file.read(length_arg))[0]
    #char
    elif data_type == "c":
        return struct.unpack(data_type, bin_file.read(1))[0]
    #byte or unsigned byte
    elif data_type == "b" or data_type == "B":
        return int(struct.unpack(data_type, bin_file.read(1))[0])
    else:
        trace("UNKNOWN UNPACK DATA TYPE: " + str(data_type))
        sys.exit(0)

#if var is string, get int from var in current chunk, otherwise return the int
def get_dynamic_number(var, chunk, bin_file):
    try:
        number = int(var)
    except:
        if "/" in var:
            var = var.split("/")
            number = get_dynamic_number(var[0], chunk, bin_file) / get_dynamic_number(var[1], chunk, bin_file)
        elif "*" in var:
            var = var.split("*")
            number = get_dynamic_number(var[0], chunk, bin_file) * get_dynamic_number(var[1], chunk, bin_file)
        elif "+" in var:
            var = var.split("+")
            number = get_dynamic_number(var[0], chunk, bin_file) + get_dynamic_number(var[1], chunk, bin_file)
        elif "-" in var:
            var = var.split("-")
            number = get_dynamic_number(var[0], chunk, bin_file) - get_dynamic_number(var[1], chunk, bin_file)
        else:
            number = get_raw(chunk[var], bin_file, tracer="get_dynamic_number")

    return number

#potentially recursive function to interpret format lines and read data from bin_file
def interpret_chunk(format_file, bin_file):
    global INDICES
    global VARS

    trace("===NEW CHUNK===")

    skipping_until_endif = False
    nested_ifs = 0

    chunk = {}

    try:
        #read lines in this chunk
        while(True):
            if ABORT:
                return chunk

            line = format_file.readline().lstrip()

            line_list = line.split()

            #trace('\033[94m' + str(skipping_until_endif) + ": " + str(bin_file.tell()) + " - " + str(chunk))
            trace('\033[92m' + str(skipping_until_endif) + ": " + str(format_file.tell()) + "--> " + str(line_list))

            #ignore comments and blank lines
            if line.startswith("#") or len(line_list) == 0:
                trace("\033[93mCOMMENT/BLANK")
                continue

            #skip over pattern definitions
            if line.startswith("@"):
                continue

            #exit, the chunk is done being read
            if line_list[0] == "END" or line_list[0] == "RETURN":
                trace("\033[93mEND")
                return chunk

            if line_list[0] == "IF":
                trace("\033[93mIF")
                nested_ifs += 1
                if line_list[1].startswith("INDEX"):
                    boolean = (INDICES[line_list[1].split("/")[1]] == get_dynamic_number(line_list[2], VARS, bin_file))
                else:
                    boolean = (get_dynamic_number(line_list[1], VARS, bin_file) == get_dynamic_number(line_list[2], VARS, bin_file))
                trace("\033[93mIf resolved to " + str(boolean))
                if not boolean:
                    skipping_until_endif = True
                continue

            #Exit IF statement
            if line_list[0] == "ENDIF":
                trace("\033[93mENDIF")
                nested_ifs -= 1
                if nested_ifs < 1:
                    skipping_until_endif = False
                continue

            #stop skipping lines because we have left all if statements
            #bug - will not work if we skip while already inside an if block
            if skipping_until_endif:
                trace("\033[93mWAIT FOR ENDIF, nested_ifs: " + str(nested_ifs))
                continue

            #GOTO a MARKER
            if line_list[0] == "GOTO":
                format_file.seek(MARKERS[line_list[1]])
                continue

            #MARKER to jump to from GOTO
            if line_list[0] == "MARKER":
                continue

            #KILL for debugging
            if line_list[0] == "KILL":
                time.sleep(1000)

            #CHUNK
            if line_list[0] == "CHUNK":
                trace("\033[93mCHUNK")
                chunk[line_list[1]] = []
                #reference offset for the beggining of the chunk format
                format_reference_offset = format_file.tell()
                num_chunks = get_dynamic_number(line_list[2], VARS, bin_file)

                #skip to the end of this format chunk if there are no chunks to be read
                if num_chunks == 0:
                    indent = 0
                    while(True):
                        line = format_file.readline().lstrip()
                        line_list = line.split()
                        if len(line_list) == 0:
                            continue
                        if line_list[0] == "CHUNK":
                            indent += 1
                        if line_list[0] == "END":
                            if indent == 0:
                                break
                            indent -= 1

                for each_chunk in range(num_chunks):
                    #Set the index with this chunk name to be the index we are on in the loop.
                    #This is used for IF statements that need to know what the chunk INDEX is.
                    INDICES[line_list[1]] = each_chunk
                    #go back to beggining of chunk format instructions for every chunk we read
                    format_file.seek(format_reference_offset)
                    trace("\033[91m***" + line_list[1] + "*** INDEX: " + str(INDICES[line_list[1]]) + "/" + str(num_chunks))
                    new_chunk = interpret_chunk(format_file, bin_file)
                    #add new child chunks to this parent chunk
                    chunk[line_list[1]].append(new_chunk)
                continue

            #SKIP bytes
            if line_list[0] == "SKIP":
                trace("\033[93mSKIP")
                bin_file.read(get_dynamic_number(line_list[1], VARS, bin_file))
                continue

            #SEEK offset
            if line_list[0] == "SEEK":
                trace("\033[93mSEEK")
                bin_file.seek(get_dynamic_number(line_list[1], VARS, bin_file))
                continue

            #normal line
            trace("\033[93mUNPACK DATA")
            if len(line_list) > 2:
                bin_list = (line_list[1] + str(get_dynamic_number(line_list[2], VARS, bin_file)), bin_file.tell())
            else:
                bin_list = (line_list[1], bin_file.tell())
            chunk[line_list[0]] = bin_list
            VARS[line_list[0]] = bin_list

            #advance in bin_file for correct offset to be stored in bin_list
            data = get_raw(bin_list, bin_file, False, tracer="interpret_chunk")
            if data == "ERROR":
                return chunk

            trace('\033[94m' + str(data) + ", FORM: " + str(bin_list[0]) + ", OFF: " + str(bin_list[1]))
    except:
        return chunk

def get_raw(bin_list, bin_file, return_to_pos=True, tracer=None):
    if tracer != None:
        pass

    form = bin_list[0]
    offset = bin_list[1]

    old_offset = bin_file.tell()
    bin_file.seek(offset)

    try:
        if len(form) > 1:
            length_arg = int(form[1:])
            raw = unpack(bin_file, form[:1], length_arg)
        else:
            raw = unpack(bin_file, form[:1])
    except:
        #print("get_raw() returned ERROR!")
        raw = "ERROR"
        ABORT = True

    if return_to_pos:
        bin_file.seek(old_offset)

    return raw

def get_formatted_data(bin_file, format_name, pattern_name):
    global MARKERS

    format_file = open("./formats/" + format_name, "r")

    format_file.seek(0, os.SEEK_END)
    format_file_size = format_file.tell()
    format_file.seek(0)

    MARKERS = {}
    while(True):
        line = format_file.readline().lstrip()

        if format_file.tell() == format_file_size:
            break

        split = line.split()
        if split != []:
            if split[0] == "MARKER":
                MARKERS[split[1]] = format_file.tell()

    trace(MARKERS)

    format_file.seek(0)
    while(True):
        line = format_file.readline().lstrip()

        if line.startswith("@"):
            if pattern_name in line:
                break

    data = interpret_chunk(format_file, bin_file)

    return data
