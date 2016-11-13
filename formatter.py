# This tool is intended to make extraction of data from raw binary files
# easier. Any text file contained in ./formats can be used to describe the
# format of a binary file, and pointers to each point of data will be
# stored in a dictionary. To get the data from a binary file using this
# reference dictionary, call get_raw(bin_list, bin_file) where bin_list
# is the 2 item list found in the reference dictionary for the piece of
# data you want to get. bin_file is the binary file you are extracting the
# data from.

# PROBLEMS
# * Cannot do nested IF statements
# * Cannot handle nested parentheses in get_dynamic_number()
# * INDEX needs to be made respective to each CHUNK, not just stored in VARS
# * Fix PEMDAS in get_dynamic_number()

import struct
import sys
import time
import os
import traceback

import color_console as cons

INDICES = {}

#Similar to the chunk structure, but it is flat, so variables of the same name will be overwritten.
#This gives a list of the most recently set variables without having to work back in a nested
# dictionary, assuming variable names are globally unique.
VARS = {}

MARKERS = {}

ABORT = False

def trace(text):
    #pass
    print(text)

def shorten_text(text, length):
    if len(text) <= length:
        split = text.ljust(length)
    else:
        split = text[:length]
    final = "[" + split + "]"
    return final

def shorten_vowels(text, length):
    text = text.lower()
    vowels = ["y", "u", "o", "i", "e", "a"]
    for v in vowels:
        if len(text) <= length:
            break
        text = text.replace(v, "")

    if len(text) <= length:
        split = text.ljust(length)
    else:
        split = text[:length]
    final = "[" + split + "]"
    return final

def chunk_trace(text, layer):
    trace(shorten_vowels(layer, 12) + "   " + text)

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
# In every case chunk is VARS, a dictionary of all variables ever loaded
# from the file format structure.
def get_dynamic_number(var, chunk, bin_file):
    #trace("step: " + str(var))
    try:
        number = int(var)
    except:
        #evaluate parentheses first
        #only works for single parentheses, no nested parentheses
        while(True):
            if "(" in var:
                start = var.find("(")
                end = var.find(")", start)
                evaluated = get_dynamic_number(var[start+1:end], chunk, bin_file)
                var = var[:start] + str(evaluated) + var[end+1:]
            else:
                break

        if "*" in var:
            var = var.split("*")
            number = get_dynamic_number(var[0], chunk, bin_file) * get_dynamic_number(var[1], chunk, bin_file)
        elif "/" in var:
            var = var.split("/")
            number = get_dynamic_number(var[0], chunk, bin_file) / get_dynamic_number(var[1], chunk, bin_file)
        elif "+" in var:
            var = var.split("+")
            number = get_dynamic_number(var[0], chunk, bin_file) + get_dynamic_number(var[1], chunk, bin_file)
        elif "-" in var:
            var = var.split("-")
            number = get_dynamic_number(var[0], chunk, bin_file) - get_dynamic_number(var[1], chunk, bin_file)
        else:
            #all math symbols have been evaluated, now evaluate variable values
            if var == "INDEX":
                number = chunk[var]
                print("FOUND 'INDEX' of " + str(number))
            elif "INDEX:" in var:
                number = INDICES[var.split(":")[1]]
                print("FOUND 'INDEX:' of " + str(number))
            else:
                number = get_raw(chunk[var], bin_file, tracer="get_dynamic_number")

    return number

#potentially recursive function to interpret format lines and read data from bin_file
def interpret_chunk(format_file, bin_file, layer):
    global INDICES
    global VARS

    chunk_trace("<<<NEW CHUNK<<<", layer)

    skipping_until_endif = False
    nested_ifs = 0

    chunk = {}

    try:
        #read lines in this chunk
        while(True):
            if ABORT:
                chunk_trace(">>>END CHUNK by error: ABORT>>>", layer)
                return chunk

            line = format_file.readline().lstrip()

            line_list = line.split()

            #trace('\033[94m' + str(skipping_until_endif) + ": " + str(bin_file.tell()) + " - " + str(chunk))
            cons.set_text_attr(cons.FOREGROUND_RED | cons.BACKGROUND_BLACK | cons.FOREGROUND_INTENSITY)
            chunk_trace("(STATUS): " + str(skipping_until_endif) + ": " + str(format_file.tell()) + " --> " + str(line_list), layer)
            cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_BLACK)

            #ignore comments and blank lines
            if line.startswith("#") or len(line_list) == 0:
                chunk_trace("COMMENT/BLANK", layer)
                continue

            if line_list[0] == "IF":
                chunk_trace("IF", layer)
                nested_ifs += 1
                if line_list[1].startswith("INDEX"):
                    boolean = (INDICES[line_list[1].split("/")[1]] == get_dynamic_number(line_list[2], VARS, bin_file))
                else:
                    boolean = (get_dynamic_number(line_list[1], VARS, bin_file) == get_dynamic_number(line_list[2], VARS, bin_file))
                chunk_trace("If resolved to " + str(boolean), layer)
                if not boolean:
                    skipping_until_endif = True
                continue

            #Exit IF statement
            if line_list[0] == "ENDIF":
                chunk_trace("ENDIF", layer)
                nested_ifs -= 1
                if nested_ifs < 1:
                    skipping_until_endif = False
                continue

            #stop skipping lines because we have left all if statements
            #bug - will not work if we skip while already inside an if block
            if skipping_until_endif:
                chunk_trace("WAIT FOR ENDIF, nested_ifs: " + str(nested_ifs), layer)
                continue

            #skip over pattern definitions
            if line.startswith("@"):
                chunk_trace("PATTERN DEFINITION", layer)
                continue

            #exit, the chunk is done being read
            if line_list[0] == "END" or line_list[0] == "RETURN":
                chunk_trace("END", layer)
                chunk_trace(">>>END CHUNK>>>", layer)
                return chunk

            #GOTO a MARKER
            if line_list[0] == "GOTO":
                chunk_trace("GOTO", layer)
                format_file.seek(MARKERS[line_list[1]])
                continue

            #MARKER to jump to from GOTO
            if line_list[0] == "MARKER":
                chunk_trace("MARKER", layer)
                continue

            #KILL for debugging
            if line_list[0] == "KILL":
                chunk_trace("KILL", layer)
                time.sleep(1000)

            #CHUNK
            if line_list[0] == "CHUNK":
                chunk_trace("CHUNK", layer)
                chunk[line_list[1]] = []
                #reference offset for the beggining of the chunk format
                format_reference_offset = format_file.tell()
                try:
                    num_chunks = get_dynamic_number(line_list[2], VARS, bin_file)
                except:
                    traceback.print_exc()
                trace("num_chunks: " + str(num_chunks))

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

                for chunk_index in range(num_chunks):
                    #Set the index with this chunk name to be the index we are on in the loop.
                    #This is used for IF statements that need to know what the chunk INDEX is.
                    INDICES[line_list[1]] = chunk_index
                    print("INDICIES --- " + str(INDICES))
                    VARS["INDEX"] = chunk_index
                    #go back to beggining of chunk format instructions for every chunk we read
                    format_file.seek(format_reference_offset)
                    print("seeking to: " + str(format_reference_offset))
                    chunk_trace("***" + line_list[1] + "*** INDEX: " + str(INDICES[line_list[1]]) + "/" + str(num_chunks), layer)
                    new_chunk = interpret_chunk(format_file, bin_file, line_list[1])
                    #add new child chunks to this parent chunk
                    chunk[line_list[1]].append(new_chunk)
                    print("chunk returned, chunk_index: " + str(chunk_index))
                print("end of all chunks: ")
                continue

            #SKIP bytes
            if line_list[0] == "SKIP":
                chunk_trace("SKIP", layer)
                bin_file.read(get_dynamic_number(line_list[1], VARS, bin_file))
                continue

            #SEEK offset
            if line_list[0] == "SEEK":
                chunk_trace("SEEK", layer)
                bin_file.seek(get_dynamic_number(line_list[1], VARS, bin_file))
                continue

            #normal line
            chunk_trace("UNPACK DATA", layer)
            if len(line_list) > 2:
                bin_list = (line_list[1] + str(get_dynamic_number(line_list[2], VARS, bin_file)), bin_file.tell())
            else:
                bin_list = (line_list[1], bin_file.tell())
            chunk[line_list[0]] = bin_list
            VARS[line_list[0]] = bin_list

            #advance in bin_file for correct offset to be stored in bin_list
            data = get_raw(bin_list, bin_file, False, tracer="interpret_chunk")
            if data == "ERROR":
                chunk_trace(">>>END CHUNK by error: data is 'ERROR'>>>", layer)
                return chunk

            cons.set_text_attr(cons.FOREGROUND_YELLOW | cons.BACKGROUND_BLACK | cons.FOREGROUND_INTENSITY)
            chunk_trace("(DATA): " + str(data) + ", FORM: " + str(bin_list[0]) + ", OFF: " + str(bin_list[1]), layer)
            cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_BLACK)
    except:
        traceback.print_exc()
        print("ERR line_list: " + str(line_list))
        chunk_trace(">>>END CHUNK by error: exception in interpret_chunk()>>>", layer)
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
        traceback.print_exc()
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

    #Find all of the MARKER statements in the format file, so they can be
    # jumped to later.
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

    #jump to the specific pattern given
    format_file.seek(0)
    while(True):
        line = format_file.readline().lstrip()

        if line.startswith("@"):
            if pattern_name in line:
                break

    data = interpret_chunk(format_file, bin_file, "GLOBAL")

    return data
