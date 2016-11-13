import sys
import traceback

from formatter import get_formatted_data
from formatter import get_raw

SETTINGS = {
    "bin_path": "./bin/",
    "gif_path": "./gif/",
    "model_path": "./models/",
}

# MATERIALS stores all the materials for the bin file being extracted. This
# is reset to an empty dictionary every time a new bin file is extracted.
MATERIALS = {}

log = open("lastlog.txt", "w")
log.truncate()
log.close()
def trace(text):
    print(text)
    log = open("lastlog.txt", "a")
    log.write(text + "\n")
    log.close()

# Creates a folder and returns the path to it.
def create_dir(path):
    import os
    if not os.path.exists(path):
        os.makedirs(path)
    return path

# Create an object file based on the data provided in dictionary data, whose
# structure is based on the format described in the wdb format file.
def export_obj(data, model, bin_file, filename):
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
            trace("888888888888888888888888888888888888 woW Weird error")
            sys.exit(0)

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

# Create an mtl file with all of the materials stored in MATERIALS for this
# particular bin file. These will be used by all LOD models in the bin file.
def export_mtl(data, path, bin_file):
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

# Create a gif image based on image, a dictionary whose structure is given
# by the wdb format file. The image is saved to path.
def export_gif(image, path, bin_file):
    import pygame

    gif_name = get_raw(image["gif_name"], bin_file)
    width = get_raw(image["width"], bin_file)
    height = get_raw(image["height"], bin_file)
    num_colors = get_raw(image["num_colors"], bin_file)

    #trace("Exporting GIF. W: " + str(width) + ", H: " + str(height) + ", NAME: " + str(gif_name) + ", COLORS: " + str(num_colors))

    colors = []
    for color in image["colors"]:
        r = get_raw(color["r"], bin_file)
        g = get_raw(color["g"], bin_file)
        b = get_raw(color["b"], bin_file)
        colors.append((r, g, b))

    draw_image = pygame.surface.Surface([width, height])
    y = 0
    for row in image["rows"]:
        x = 0
        for pixel in row["pixels"]:
            color_index = get_raw(pixel["color_index"], bin_file)
            new_color = colors[color_index]
            draw_image.set_at([x, y], new_color)
            x += 1
        y += 1

    #trace("GIF SAVED TO: " + path + gif_name[:-4] + ".png")
    pygame.image.save(draw_image, path + gif_name[:-4] + ".png")

# Open WORLD.WDB using format wdb and pattern wdb. Then write all of the bin
# files based on the tables in the header of the wdb.
def extract_wdb():
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
                #for each_byte in range(size_of_item):
                #    write_file.write(bin_file.read(1))
                write_file.close()

    #write gif chunk to be extracted by extract_gif_chunk()
    directory = create_dir(SETTINGS["gif_path"])
    write_file = open(directory + "gifchunk.bin", "wb")
    bin_file.seek(data["gif_chunk_size"][1]+4)
    write_file.write(bin_file.read(get_raw(data["gif_chunk_size"], bin_file)))
    write_file.close()

# Extract all of the gif images from the gifchunk.bin, which is just data that
# was extracted from the raw wdb. This is neccesary because the wdb has random
# gifs lying around inside it that aren't specifically assigned to any models,
# they are probably just loaded into memory when the game loads.
def extract_gif_chunk():
    import pygame

    bin_file = open(SETTINGS["gif_path"] + "gifchunk.bin", "rb")

    data = get_formatted_data(bin_file, "wdb", "gifchunk")

    for image in data["images"]:
        export_gif(image, SETTINGS["gif_path"], bin_file)

# Go through all of the bin files in the folder hierarchy that was extracted,
# and call extract_pattern() on each of them. It will try to extract using the
# pattern with no animations, and then with animations.
def extract_models():
    global MATERIALS
    import pygame
    import os

    #find all files in the groups folder that end in .bin
    bin_files = [os.path.join(root, name)
        for root, dirs, files in os.walk(SETTINGS["bin_path"])
        for name in files
        if name.endswith((".bin"))]

    total_file_num = len(bin_files)
    files_extracted = 0

    #overwrite bin_files for testing extraction of one particular file
    #bin_files = ["./bin/ACT1/sub1/ambul.bin"]

    #go through all bin files with extract_pattern() using two different patterns, using whichever one works
    for file_path in bin_files:
        used_pattern = "model-noanims"
        progress = extract_pattern(file_path, used_pattern)
        if "X" in progress:
            used_pattern = "model"
            progress = extract_pattern(file_path, used_pattern)

        #display the name and progress for this file
        trace(file_path.ljust(40) + str(progress) + " " + used_pattern)

        #success, increment files_extracted
        if "X" not in progress:
            files_extracted += 1

    #final stat printed
    trace(str(files_extracted) + " out of " + str(total_file_num) + " extracted!")

# Grab data from a specific bin file using the specified pattern in the wdb
# format file. The data will then be used to create wavefront object files
# from vertex, normal and coordinate data, gif images from textures, and a
# mdl file to connect the textures with the models.
def extract_pattern(file_path, pattern):
    bin_file = open(file_path, "rb")

    #reset materials to empty
    MATERIALS = {}

    progress = ["X", "X", "X", "X", "X"]

    #INTERPRET FORMAT FROM FILE
    try:
        data = get_formatted_data(bin_file, "wdb", pattern)
        progress[0] = "_"
    except:
        traceback.print_exc()
        return progress

    #EXPORT OBJ
    try:
        file_name = get_raw(data["file_name"], bin_file)

        #trace(data)
        for component in data["components"]:
            component_name = get_raw(component["component_name"], bin_file)
            model_index = len(component["models"])
            for model in component["models"]:
                model_index -= 1
                file_path = file_path.replace("\\", "/")
                obj_path = create_dir("./obj" + file_path[file_path.find("/", 3):file_path.rfind("/")] + "/" + file_name + "/")
                #trace(obj_path)
                export_obj(data, model, bin_file, obj_path + component_name + str(model_index))
        progress[1] = "_"
    except:
        traceback.print_exc()
        return progress


    found_materials = []
    #EXPORT TEXTURES
    try:
        num_images = get_raw(data["num_images"], bin_file)

        #export textures embedded in this bin group as .png
        for image in data["images"]:
            export_gif(image, obj_path, bin_file)
            #special hidden textures, only seen on isle_hi
            #if file_name[-1:] == "X":
            #	hide_image, file_name2 = read_gif(bin_file, False)
            #	pygame.image.save(hide_image, newpath + "hide_" + file_name + ".png")
            found_materials.append(get_raw(image["gif_name"], bin_file)[:-4])
        progress[2] = "_"
    except:
        traceback.print_exc()
        return progress

    #EXPORT MATERIALS
    try:
        #export materials without textures as .png, just their rgb on a 4x4 texture
        for material in MATERIALS:
            if material not in found_materials:
                new_image = pygame.surface.Surface([4, 4])
                new_image.fill(MATERIALS[material])
                pygame.image.save(new_image, obj_path + material + ".png")
                #trace("MATERIAL SAVED TO: " + obj_path + material + ".png")
        progress[3] = "_"
    except:
        traceback.print_exc()
        return progress

    #EXPORT MTL FILE
    try:
        export_mtl(data, obj_path, bin_file)
        progress[4] = "_"
    except:
        traceback.print_exc()
        return progress

    return progress

def main():
    #extract_wdb()
    #extract_gif_chunk()
    extract_models()

main()
