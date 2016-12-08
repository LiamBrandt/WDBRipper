"""
This is a tool to extract data from the Lego Island WORLD.WDB. This data
is used to export OBJ, MTL and PNG files based on the model data found in
WORLD.WDB.
"""

import traceback
import cProfile
import os
import png

from formatter import get_formatted_data
from formatter import get_raw

SETTINGS = {}

with open("config.txt","r") as inf:
    SETTINGS = eval(inf.read())

# MATERIALS stores all the materials for the bin file being extracted. This
# is reset to an empty dictionary every time a new bin file is extracted.
MATERIALS = {}

STATS = {
    "csv": {
        "materials": [["Material", "Flat", "TimesUsed"]],
    },
}

if SETTINGS["write_log"]:
    log = open("lastlog.txt", "w")
    log.truncate()
    log.close()
def trace(text):
    """Print text to the console."""
    if SETTINGS["verbose"]:
        print(text)
        if SETTINGS["write_log"]:
            log = open("lastlog.txt", "a")
            log.write(text + "\n")
            log.close()

def trace_error():
    """Print the most recent error to the console."""
    if SETTINGS["verbose"]:
        traceback.print_exc()

def create_dir(path):
    zero_stripped_path = path.strip("\0")
    """Create a folder and return the path to it."""
    if not os.path.exists(zero_stripped_path):
        os.makedirs(zero_stripped_path)
    return zero_stripped_path

def export_obj(data, model, bin_file, filename):
    """
    Create a wavefront object file based on the data and model dictionaries.

    The dictionaries data and model are based on the wdb format taken from
    get_formatted_data() in formatter.py. The object file is exported to
    the path specified by filename.
    """

    global MATERIALS
    obj_file = open(filename + ".obj", "w")
    obj_file.truncate()

    obj_file.write("mtllib " + get_raw(data["file_name"], bin_file) + ".mtl\n")

    scale = 1.0
    #WRITE OBJ VERTS, NORMALS, COORDINATES
    for vertex in model["vertices"]:
        obj_file.write("v " + str(get_raw(vertex["x"], bin_file)*scale) + " " + str(-get_raw(vertex["y"], bin_file)*scale) + " " + str(get_raw(vertex["z"], bin_file)*scale) + "\n")

    for text_coord in model["coordinates"]:
        obj_file.write("vt " + str(((get_raw(text_coord["u"], bin_file)*scale)-scale)/scale) + " " + str(((-get_raw(text_coord["v"], bin_file)*scale)-scale)/scale) + "\n")

    for normal in model["normals"]:
        obj_file.write("vn " + str(get_raw(normal["x"], bin_file)*scale) + " " + str(-get_raw(normal["y"], bin_file)*scale) + " " + str(get_raw(normal["z"], bin_file)*scale) + "\n")


    #INTERPRET AND WRITE INDICES
    part_index = 0
    for part in model["parts"]:
        tri_normal = None
        triangles = []

        vert_definitions = []
        text_definitions = []

        if len(part["coordinate_indices"]) > 0 and len(part["coordinate_indices"]) != len(part["indices"]):
            trace("This shouldn't happen!!!!!")

        for index in range(len(part["indices"])):
            vert_indices = []
            text_indices = []
            for axis in range(len(part["indices"][index]["axis"])):
                first = get_raw(part["indices"][index]["axis"][axis]["first"], bin_file)
                second = get_raw(part["indices"][index]["axis"][axis]["second"], bin_file)
                if len(part["coordinate_indices"]) > 0:
                    coordinate_index = get_raw(part["coordinate_indices"][index]["axis"][axis]["coordinate_index"], bin_file)
                else:
                    coordinate_index = 1

                #index definition
                if second >= 32768:
                    vert_definitions.append(first)
                    text_definitions.append(coordinate_index)

                    vert_indices.append(first)
                    text_indices.append(coordinate_index)

                    tri_normal = second - 32768
                #index to a definition, not a definition
                else:
                    vert_indices.append(vert_definitions[first])
                    if len(part["coordinate_indices"]) > 0:
                        text_indices.append(text_definitions[first])
                    else:
                        text_indices.append(1)

            #Triangle format: (verts, normal, coords)
            triangles.append([vert_indices, tri_normal, text_indices])

        red = get_raw(part["part_color_red"], bin_file)
        green = get_raw(part["part_color_green"], bin_file)
        blue = get_raw(part["part_color_blue"], bin_file)

        color = (red, green, blue)

        texture_name = get_raw(part["texture_name"], bin_file)[:-4].replace(" ", "")
        material_name = get_raw(part["material_name"], bin_file).replace(" ", "")

        if texture_name == "":
            name_to_use = material_name
        else:
            name_to_use = texture_name

        dont_add = False
        for each_material in MATERIALS:
            if each_material == name_to_use:
                dont_add = True
        if dont_add == False:
            MATERIALS[name_to_use] = color


        #WRITE INDICES TO OBJ
        obj_file.write("o " + str(part_index) + "\n")

        #try to use texture_name, otherwise material_name
        if texture_name == "":
            obj_file.write("usemtl " + str(material_name) + "\n")
        else:
            obj_file.write("usemtl " + str(texture_name) + "\n")

        for each_triangle in triangles:
            obj_file.write("f ")
            #three iterations for 3 points in a triangle, NOT 3 dimensions (x,y,z)!
            for i in range(3):
                #make sure there are texture coordinates
                if len(each_triangle[2]) > 0:
                    #index/coordinate/normal
                    obj_file.write(str(each_triangle[0][i]+1) + "/" + str(each_triangle[2][i]+1) + "/" + str(each_triangle[1]+1))
                else:
                    #index/1/normal
                    obj_file.write(str(each_triangle[0][i]+1) + "//" + str(each_triangle[1]+1))
                obj_file.write(" ")

            obj_file.write("\n")

        part_index += 1

    obj_file.close()

def export_mtl(data, path, bin_file):
    """
    Create a material file to be used by wavefront object files.

    Creates a mtl file using some default values plus the paths to the
    materials used by the object files.
    """
    global MATERIALS
    file = open(path + get_raw(data["file_name"], bin_file) + ".mtl", "w")
    file.truncate()

    for material in MATERIALS:
        file.write("newmtl " + str(material) + "\n")
        file.write("Ns 0\n")
        file.write("Ka 0.000000 0.000000 0.000000\n")
        file.write("Kd 0.8 0.8 0.8\n")
        file.write("Ks 0.8 0.8 0.8\n")
        file.write("d 1\n")
        file.write("illum 2\n")

        file.write("map_Ka " + str(material) + ".png\n")
        file.write("map_Kd " + str(material) + ".png\n")
        file.write("map_Ks " + str(material) + ".png\n")

    file.close()

def export_gif(image, path, bin_file):
    """
    Create a PNG image based on a GIF image.

    The GIF data is specified in the dictionary image and contains formatted
    data based on the wdb structure. The PNG image is saved to path.
    """
    gif_name = get_raw(image["gif_name"], bin_file)
    width = get_raw(image["width"], bin_file)
    height = get_raw(image["height"], bin_file)
    num_colors = get_raw(image["num_colors"], bin_file)

    colors = []
    for color in image["colors"]:
        r = get_raw(color["r"], bin_file)
        g = get_raw(color["g"], bin_file)
        b = get_raw(color["b"], bin_file)
        colors.append((r, g, b))

    rows = []
    y = 0
    for row in image["rows"]:
        x = 0
        rows.append([])
        for pixel in row["pixels"]:
            color_index = get_raw(pixel["color_index"], bin_file)
            c = colors[color_index]
            for i in range(3):
                rows[y].append(c[i])

            x += 1
        y += 1

    #write png
    f = open(path + gif_name[:-4] + ".png", "wb")
    f.truncate()
    w = png.Writer(width, height)
    w.write(f, rows)
    f.close()

def extract_wdb():
    """
    Open WORLD.WDB and write all the sections as *.bin files.

    Open WORLD.WDB as specified by the structure found in the wdb format
    file. Export each section of the wdb as a bin file in the folder
    hiearchy found in the header of the wdb file.
    """
    bin_file = open("./WORLD.WDB", "rb")

    data = get_formatted_data(bin_file, "wdb", "wdb")

    for each_group in data["groups"]:
        group_title = get_raw(each_group["group_title"], bin_file)
        i = -1
        for each_subgroup in each_group["subgroups"]:
            i += 1
            subgroup_title = "sub" + str(i)
            for each_sub_item in each_subgroup["sub_items"]:
                sub_item_title = get_raw(each_sub_item["sub_item_title"], bin_file)
                item_offset = get_raw(each_sub_item["item_offset"], bin_file)
                size_of_item = get_raw(each_sub_item["size_of_item"], bin_file)

                directory = create_dir(SETTINGS["bin_path"] + group_title[:-1] + "/" + subgroup_title + "/")

                write_file = open(directory + sub_item_title[:-1] + ".bin", "wb")
                write_file.truncate()

                bin_file.seek(item_offset)
                write_file.write(bin_file.read(size_of_item))
                write_file.close()

    #write gif chunk to be extracted by extract_gif_chunk()
    directory = create_dir(SETTINGS["gif_path"])
    write_file = open(directory + "gifchunk.bin", "wb")
    bin_file.seek(data["gif_chunk_size"][1]+4)
    write_file.write(bin_file.read(get_raw(data["gif_chunk_size"], bin_file)))
    write_file.close()

    #write model chunk to be extracted by extract_model_chunk()
    print(str(data["model_chunk_size"]))
    directory = create_dir(SETTINGS["gif_path"])
    write_file = open(directory + "modelchunk.bin", "wb")
    bin_file.seek(data["model_chunk_size"][1]+4)
    write_file.write(bin_file.read(get_raw(data["model_chunk_size"], bin_file)))
    write_file.close()

def extract_gif_chunk():
    """
    Extract all of the GIF images from gifchunk.bin as PNGs.

    gifchunk.bin is just raw gifs that were found lying around in the wdb.
    They aren't specifically assigned to any models, and are likely just
    loaded into memory when Lego Island loads.
    """
    bin_file = open(SETTINGS["gif_path"] + "gifchunk.bin", "rb")

    data = get_formatted_data(bin_file, "wdb", "gifchunk")

    for image in data["images"]:
        export_gif(image, SETTINGS["gif_path"], bin_file)

def extract_model_chunk():
    bin_file = open(SETTINGS["gif_path"] + "modelchunk.bin", "rb")

    data = get_formatted_data(bin_file, "wdb", "modelchunk")
    bin_file.seek(0)
    for binn in data["bins"]:
        end_bin_offset = get_raw(binn["end_bin_offset"], bin_file)
        size_of_item = end_bin_offset - bin_file.tell()

        write_file = open(SETTINGS["bin_path"] + "/" + get_raw(binn["bin_name"], bin_file) + ".bin", "wb")
        write_file.truncate()

        write_file.write(bin_file.read(size_of_item))
        write_file.close()

        bin_file.seek(end_bin_offset)

def extract_models():
    """
    Go through all *.bin files and extract the models from them.

    Calls extract_pattern() on all of the bin files, this function's purpose
    is just to keep track of which files extract and which ones don't.
    """
    #find all files in the groups folder that end in .bin
    bin_files = [os.path.join(root, name)
        for root, dirs, files in os.walk(SETTINGS["bin_path"])
        for name in files
        if name.endswith((".bin"))]

    #overwrite bin_files for testing extraction of one particular file
    if SETTINGS["override"]:
        bin_files = [SETTINGS["override_path"]]

    total_file_num = len(bin_files)
    files_extracted = 0

    #go through all bin files with extract_pattern() using two different patterns, using whichever one works
    for file_path in bin_files:
        progress = extract_pattern(file_path, "model")

        #display the name and progress for this file
        trace(file_path.ljust(40) + str(progress))

        #success, increment files_extracted
        if "X" not in progress:
            files_extracted += 1

    #final stat printed
    trace(str(files_extracted) + " out of " + str(total_file_num) + " extracted!")

def extract_pattern(file_path, pattern):
    """
    Attempt to extract data from a .bin file and return the progress made.

    There are five steps to extraction:
     * Interpret data from the wdb using the wdb format file
     * Export the object files using the data
     * Export textures
     * Export materials
     * Export the material file mtl
    These steps are represented by the list of five items returned by the
    function that signify if that step was successful. '_' means success,
    and 'X' means failure.
    """
    global MATERIALS
    global STATS
    bin_file = open(file_path, "rb")

    #reset materials to empty
    MATERIALS = {}

    progress = ["X", "X", "X", "X", "X"]

    #INTERPRET FORMAT FROM FILE
    try:
        data = get_formatted_data(bin_file, "wdb", pattern)
        #trace(str(data))
        progress[0] = "_"
    except:
        trace_error()
        return progress

    #EXPORT OBJ
    try:
        file_name = get_raw(data["file_name"], bin_file)

        file_path = file_path.replace("\\", "/")
        obj_path = create_dir(SETTINGS["obj_path"] + file_path[file_path.find("/", 3):file_path.rfind("/")] + "/" + file_name + "/")

        #trace(data)
        for component in data["components"]:
            component_name = get_raw(component["component_name"], bin_file)
            if "models" in component:
                model_index = len(component["models"])
                for model in component["models"]:
                    model_index -= 1
                    #determine whether or not to export this LOD model based on SETTINGS
                    export = False
                    if SETTINGS["highest_lod_only"]:
                        if model_index == 0:
                            export = True
                    else:
                        export = True

                    if export:
                        if SETTINGS["highest_lod_only"] and not SETTINGS["lod_labels"]:
                            end_string = ""
                        else:
                            end_string = "_lod" + str(model_index)
                        export_obj(data, model, bin_file, obj_path + component_name + end_string)
            else:
                #no models in this component, only the component header
                pass
        progress[1] = "_"
    except:
        trace_error()
        return progress


    found_materials = []
    #EXPORT TEXTURES
    try:
        num_images = get_raw(data["num_images"], bin_file)

        #export textures embedded in this bin group as .png
        for image in data["images"]:
            #normal gif
            export_gif(image, obj_path, bin_file)
            #special hidden gif, only seen on isle and isle_hi gifs
            if "extra_images" in image:
                image["extra_images"][0]["gif_name"] = image["gif_name"]
                export_gif(image["extra_images"][0], obj_path + "/hidden_", bin_file)
            found_materials.append(get_raw(image["gif_name"], bin_file)[:-4])
        progress[2] = "_"
    except:
        trace_error()
        return progress

    #EXPORT MATERIALS
    try:
        #export materials without textures as .png, just their rgb on a 4x4 texture
        for material in MATERIALS:
            if material not in found_materials:
                found_materials.append(material)
                #write 4x4 png of color c
                c = MATERIALS[material]
                rows = []
                for row in range(4):
                    rows.append([])
                    for pixel in range(4):
                        rows[row].append(c[0])
                        rows[row].append(c[1])
                        rows[row].append(c[2])
                f = open(obj_path + material + ".png", "wb")
                f.truncate()
                w = png.Writer(4, 4)
                w.write(f, rows)
                f.close()


        #statistics for materials
        for material in found_materials:
            found_duplicate = False
            for row in STATS["csv"]["materials"]:
                if row[0] == material:
                    found_duplicate = True
                    row[2] += 1
            if not found_duplicate:
                STATS["csv"]["materials"].append([material, "No", 1])


        progress[3] = "_"
    except:
        trace_error()
        return progress

    #EXPORT MTL FILE
    try:
        export_mtl(data, obj_path, bin_file)
        progress[4] = "_"
    except:
        trace_error()
        return progress

    return progress

def export_stats():
    stat_path = create_dir(SETTINGS["stat_path"])
    for csv_key in STATS["csv"]:
        csv_file = open(stat_path + csv_key + ".csv", "w")
        csv_file.truncate()
        for row in STATS["csv"][csv_key]:
            for value in row:
                csv_file.write(str(value) + ", ")
            csv_file.write("\n")
        csv_file.close()

def main():
    if SETTINGS["extract_wdb"]:
        print("Extracting WDB...")
        extract_wdb()
        print("Extracting GIFs...")
        extract_gif_chunk()
        #print("Extracting BINCHUNK...")
        #extract_model_chunk()
    if SETTINGS["extract_obj"]:
        print("Creating OBJs from BINs...")
        extract_models()
    if SETTINGS["statistics"]:
        print("Exporting statistics...")
        export_stats()
    print("Done!")

if SETTINGS["profile"]:
    cProfile.runctx( "main()", globals(), locals(), filename="wdb_ripper.profile" )
else:
    main()
