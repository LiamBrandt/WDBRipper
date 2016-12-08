"""
This tool is intended to make extraction of data from raw binary files
easier. Any text file contained in ./formats can be used to describe the
format of a binary file, and pointers to each point of data will be
stored in a dictionary. To get the data from a binary file using this
reference dictionary, call get_raw(bin_list, bin_file) where bin_list
is the 2 item list found in the reference dictionary for the piece of
data you want to get. bin_file is the binary file you are extracting the
data from.

Problems:
 * Cannot do nested IF statements
 * Cannot handle nested parentheses in get_dynamic_number()
 * INDEX needs to be made respective to each CHUNK, not just stored in VARS
 * Fix PEMDAS in get_dynamic_number()
"""

import struct
import time
import os
import traceback

#import color_console as cons

SETTINGS = {
    "trace": False,
    "safe_debug": False,
}

INDICES = {}

#flat dictionary of variables previously defined
VARS = {}

MARKERS = {}

ABORT = False

def trace(text):
    """Print the text to the console if SETTINGS["trace"] is True."""
    if SETTINGS["trace"]:
        print(text)

def trace_error():
    """Print the last error to the console."""
    if SETTINGS["trace"]:
        traceback.print_exc()

def shorten_vowels(text, length):
    """Return the shorter text of specified length by removing vowels."""
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
    """Print the text to the console along with the current chunk layer."""
    if SETTINGS["trace"]:
        trace(shorten_vowels(layer, 12) + "   " + text)

def unpack(bin_file, data_type, length_arg=0):
    """
    Use struct.unpack() to load a value from the binary file.

    Keyword arguments:
    length_arg -- the length of the data, used only for strings

    Use data_type to tell what type of data to unpack from bin_file, then return
    the unpacked data.
    """
    if SETTINGS["safe_debug"]:
        global ABORT
        current_offset = bin_file.tell()
        bin_file.seek(0, 2)
        if current_offset == bin_file.tell():
            #trying to read bytes that dont exist, we are at end of file!
            ABORT = True
            return ["EOF"]
        bin_file.seek(current_offset)

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

def get_dynamic_number(var, chunk, bin_file):
    """
    Get and return an integer based on a math expression and or variables.

    If var is just an integer in string form, return the integer. Otherwise
    evaluate var as a mathematical expression, calling get_dynamic_number()
    on both sides of an operand until an integer value is reached. Variable
    names defined in previously in the format file can be used instead of
    integers.
    """
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
                trace("FOUND 'INDEX' of " + str(number))
            elif "INDEX:" in var:
                number = INDICES[var.split(":")[1]]
                trace("FOUND 'INDEX:' of " + str(number))
            else:
                number = get_raw(chunk[var], bin_file)

    return number

def interpret_chunk(format_file, bin_file, layer):
    """
    Interpret binary data from bin_file using the format from format_file.

    Read lines from format_file. For each line, identify what the line is
    telling the interpret_chunk() to do, and do it. This could mean anything
    from carrying out an if statement, to jumping to an offset, to
    creating a new chunk inside of this chunk by calling interpret_chunk()
    recursively.
    """
    global INDICES
    global VARS

    chunk_trace("<<<NEW CHUNK<<<", layer)

    skipping_until_endif = False
    nested_ifs = 0

    chunk = {}
    flags = {
        "return": False,
    }

    try:
        #read lines in this chunk
        while(True):
            if ABORT:
                chunk_trace(">>>END CHUNK by error: ABORT>>>", layer)
                flags["return"] = True
                return chunk, flags

            line = format_file.readline().lstrip()

            line_list = line.split()

            """
            if SETTINGS["trace"]:
                cons.set_text_attr(cons.FOREGROUND_RED | cons.BACKGROUND_BLACK | cons.FOREGROUND_INTENSITY)
                chunk_trace("(STATUS): " + str(skipping_until_endif) + ": " + str(format_file.tell()) + " --> " + str(line_list), layer)
                cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_BLACK)
            """

            #ignore comments and blank lines
            if line.startswith("#") or len(line_list) == 0:
                chunk_trace("COMMENT/BLANK", layer)
                continue

            #IF statement
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
            if line_list[0] == "END":
                chunk_trace("END", layer)
                chunk_trace(">>>END CHUNK>>>", layer)
                return chunk, flags

            if line_list[0] == "RETURN":
                chunk_trace("RETURN", layer)
                chunk_trace(">>>END CHUNK by return>>>", layer)
                flags["return"] = True
                return chunk, flags

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
                    trace_error()
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
                    trace("INDICIES --- " + str(INDICES))
                    VARS["INDEX"] = chunk_index
                    #go back to beggining of chunk format instructions for every chunk we read
                    format_file.seek(format_reference_offset)
                    trace("seeking to: " + str(format_reference_offset))
                    chunk_trace("***" + line_list[1] + "*** INDEX: " + str(INDICES[line_list[1]]) + "/" + str(num_chunks), layer)
                    new_chunk, new_flags = interpret_chunk(format_file, bin_file, line_list[1])
                    #add new child chunks to this parent chunk
                    chunk[line_list[1]].append(new_chunk)

                    if new_flags["return"]:
                        trace("chunk RETURNed, chunk_index: " + str(chunk_index))
                        break

                    trace("chunk ENDed, chunk_index: " + str(chunk_index))
                trace("end of all chunks: ")
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

            #SEEKREL offset
            if line_list[0] == "SEEKREL":
                chunk_trace("SEEKREL", layer)
                bin_file.seek(get_dynamic_number(line_list[1], VARS, bin_file), 1)
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
            data = get_raw(bin_list, bin_file, False)
            if data == "ERROR":
                chunk_trace(">>>END CHUNK by error: data is 'ERROR'>>>", layer)
                flags["return"] = True
                return chunk, flags

            """
            if SETTINGS["trace"]:
                cons.set_text_attr(cons.FOREGROUND_YELLOW | cons.BACKGROUND_BLACK | cons.FOREGROUND_INTENSITY)
                chunk_trace("(DATA): " + str(data) + ", FORM: " + str(bin_list[0]) + ", OFF: " + str(bin_list[1]), layer)
                cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_BLACK)
            """
    except:
        trace_error()
        chunk_trace(">>>END CHUNK by error: exception in interpret_chunk()>>>", layer)
        flags["return"] = True
        return chunk, flags

def get_raw(bin_list, bin_file, return_to_pos=True):
    """
    Unpack and return binary data from bin_file using bin_list.

    Keyword arguments:
    return_to_pos -- whether or not to return to the offset of bin_file before the get_raw() was called

    Use the form from bin_list[0] and offset from bin_list[1] to unpack
    the binary data at the offset with a specific form. This form is a string
    that will be given to unpack() as the data_type for the data to be
    unpacked.
    """

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
        trace("get_raw() returned ERROR!")
        trace_error()
        raw = "ERROR"
        ABORT = True

    #hit end of file
    if type(raw) == type([]):
        if raw[0] == "EOF":
            raw = "ERROR"
            ABORT = True

    if return_to_pos:
        bin_file.seek(old_offset)

    return raw

def get_formatted_data(bin_file, format_name, pattern_name):
    """
    Return a structured dictionary of data about values contained in bin_file.

    Open a format file based on format_name and find a pattern to start from
    based on pattern_name. Return a dictionary with values that are
    tuples that represent what type of data is stored at a certain offset in
    bin_file, and keys that are descriptions of that data.
    """
    global MARKERS
    global ABORT
    ABORT = False

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
        line_list = line.split()

        if line.startswith("@"):
            if line_list[0] == "@"+pattern_name:
                break

    data, flags = interpret_chunk(format_file, bin_file, "GLOBAL")

    return data
