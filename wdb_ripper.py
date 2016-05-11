#Lego Island WORLD.WDB ripper

import pygame, struct, os, time, math, sys, shutil, datetime

pygame.init()

INFO = {
	"files_read": 0,
	"files_not_read": 0,
}

#load settings
SETTINGS = {}
with open('config.txt','r') as inf:
    SETTINGS = eval(inf.read()) 
	
SETTINGS["screen_x"] = 400
SETTINGS["screen_y"] = 200
SETTINGS["font_size"] = 15
	
	
MATERIALS = []

#load font
big_font = pygame.font.Font("monaco.ttf", SETTINGS["font_size"])
	
#set up display
screen = pygame.display.set_mode([SETTINGS["screen_x"], SETTINGS["screen_y"]])
	
	
	
def get_text():
	last_search_word = "x"
	search_word = ""

	while(True):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit(0)
		
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_a:
					search_word = search_word + "a"
				if event.key == pygame.K_b:
					search_word = search_word + "b"
				if event.key == pygame.K_c:
					search_word = search_word + "c"
				if event.key == pygame.K_d:
					search_word = search_word + "d"
				if event.key == pygame.K_e:
					search_word = search_word + "e"
				if event.key == pygame.K_f:
					search_word = search_word + "f"
				if event.key == pygame.K_g:
					search_word = search_word + "g"
				if event.key == pygame.K_h:
					search_word = search_word + "h"
				if event.key == pygame.K_i:
					search_word = search_word + "i"
				if event.key == pygame.K_j:
					search_word = search_word + "j"
				if event.key == pygame.K_k:
					search_word = search_word + "k"
				if event.key == pygame.K_l:
					search_word = search_word + "l"
				if event.key == pygame.K_m:
					search_word = search_word + "m"
				if event.key == pygame.K_n:
					search_word = search_word + "n"
				if event.key == pygame.K_o:
					search_word = search_word + "o"
				if event.key == pygame.K_p:
					search_word = search_word + "p"
				if event.key == pygame.K_q:
					search_word = search_word + "q"
				if event.key == pygame.K_r:
					search_word = search_word + "r"
				if event.key == pygame.K_s:
					search_word = search_word + "s"
				if event.key == pygame.K_t:
					search_word = search_word + "t"
				if event.key == pygame.K_u:
					search_word = search_word + "u"
				if event.key == pygame.K_v:
					search_word = search_word + "v"
				if event.key == pygame.K_w:
					search_word = search_word + "w"
				if event.key == pygame.K_x:
					search_word = search_word + "x"
				if event.key == pygame.K_y:
					search_word = search_word + "y"
				if event.key == pygame.K_z:
					search_word = search_word + "z"
					
				if event.key == pygame.K_0:
					search_word += "0"
				if event.key == pygame.K_1:
					search_word += "1"
				if event.key == pygame.K_2:
					search_word += "2"
				if event.key == pygame.K_3:
					search_word += "3"
				if event.key == pygame.K_4:
					search_word += "4"
				if event.key == pygame.K_5:
					search_word += "5"
				if event.key == pygame.K_6:
					search_word += "6"
				if event.key == pygame.K_7:
					search_word += "7"
				if event.key == pygame.K_8:
					search_word += "8"
				if event.key == pygame.K_9:
					search_word += "9"
					
				if event.key == pygame.K_PERIOD:
					search_word += "."
				if event.key == pygame.K_SLASH:
					search_word = search_word + "/"
				
				if event.key == pygame.K_SPACE:
					search_word = search_word + " "
					
				if event.key == pygame.K_ESCAPE:
					searching = False
					
				if event.key == pygame.K_BACKSPACE:
					search_word = search_word[:-1]
					
				if event.key == pygame.K_RETURN:
					return search_word
	
		if search_word != last_search_word:
			last_search_word = search_word
			screen.fill([200, 200, 200])
			write_to_screen("Type in the path of the file: " + search_word + "_")
	
def wait_for_input():
	while(True):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit(0)
			if event.type == pygame.KEYDOWN:
				return
	
#makes sure that the screen doesnt freeze, and you can quit the program
def update_pygame_events():
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit(0)
	
#write text to the screen
def write_to_screen(msg, pos=[0, 0]):
	load_text = big_font.render(msg, True, (0, 0, 0))
	screen.blit(load_text, pos)
	
	if load_text.get_width()+pos[0] > SETTINGS["screen_x"]:
		write_to_screen(msg, [pos[0]-SETTINGS["screen_x"], pos[1]+SETTINGS["font_size"]])
	
	pygame.display.flip()
	update_pygame_events()
	
#write to the log
def write_to_log(msg):
	screen.fill([200, 200, 200])
	write_to_screen(msg)
	print(msg)
	"""log_file = open("log.txt", "a")
	log_file.write(msg + "\n")
	log_file.close()"""
	
#debug log, do nothing unless you want lots of text
def write_debug(msg):
	pass
	
class ModelFile(object):
	def __init__(self):
		self.magic_number = 0
		self.bytes_left_in_subgroup = 0
		self.version = 0
		self.num_components = 0
		self.name = ""
		
		#deprecated?
		self.models = []
		
		self.components = []
		self.materials = []

class Material(object):
	def __init__(self, name, color):
		self.name = name
		self.color = color

class Component(object):
	def __init__(self):
		self.name = ""
		self.num_component_parts = 0
		
		self.component_parts = []
		self.models = []
		
class ComponentPart(object):
	def __init__(self):
		self.data = None
		
class Model(object):
	def __init__(self):
		self.num_verts = 0
		self.num_normals = 0
		self.num_texture_coordinates = 0
		
		self.num_parts = 0
	
		self.vertices = []
		self.normals = []
		self.texture_coordinates = []
		
		self.parts = []
		
class Part(object):
	def __init__(self):
		self.triangles = []
		self.color = (255, 255, 255)
		
		self.texture_name = ""
		self.material_name = ""
		
class Point(object):
	def __init__(self, x, y, z, index):
		self.x = x
		self.y = y
		self.z = z
		self.index = index

class TextureCoordinate(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		
class Triangle(object):
	def __init__(self, indexes, normal):
		#vertices
		self.indexes = indexes
		#normal
		self.normal = normal
		
		#texture coordinates
		self.texture_indexes = []
		
	def draw(self, points, angle, scale, color):
		tri_point_list = [points[self.indexes[0].value].get_draw_point(angle, scale), points[self.indexes[1].value].get_draw_point(angle, scale), points[self.indexes[2].value].get_draw_point(angle, scale)]
		pygame.draw.polygon(screen, color, tri_point_list, 1)
		
class Index(object):
	#lego island weird ass format for indices
	def __init__(self, value, is_definition):
		self.value = value
		self.is_definition = is_definition
		
		
		
	
def read_indices(bin_file, model):
	global MATERIALS

	new_part = Part()
	write_debug("creating new PART from offset: " + str(bin_file.tell()))

	#INDICES
	#each indice is 12 bytes, three 4 byte sections, one for each x y z coordinate
	#each 4 byte section is made up of 2 shorts. If the second short has 1 as its most signifigant bit, then this 4 byte section contains an index definition.
	#	otherwise this section is a pointer to an index previously defined.
	#EX: 01 00 01 00 / 05 00 07 80 / 00 00 00 00
	#this 12 byte indice above is an example. The first 4 bytes are a pointer to another index. It is the index of the list of indexes that have been defined
	#	in this section. both of the shorts in the first 4 bytes are duplicates of each other, this is always the same. The second section is a indice definition,
	#	becaues the second short begins with 0x80, which is a 1 as the MSB. The first short is the actual index of the vertice, and this should be appended to the list
	#	of indices we already have, as it may be referenced later by another 4 byte section that is not a definition.
	
	#this number times 12 is the length in bytes of the normal/indice section to follow
	tri_num = int(struct.unpack("h", bin_file.read(2))[0])
	#the number of times that 0x80 appears in the normal/indice section to follow
	num_index_definitions = int(struct.unpack("h", bin_file.read(2))[0])
			
	write_debug("    " + str(tri_num) + " triangles in this part")
	write_debug("    " + str(num_index_definitions) + " index definitions in this part")
	
	indice_list = []
	
	tri_normal = None
	#VERTICE INDEXES
	for each_indice in range(tri_num):
		indexes = []
	
		for each_index in range(3):
			first = struct.unpack("H", bin_file.read(2))[0]
			second = struct.unpack("H", bin_file.read(2))[0]
		
			#index definition
			if second >= 32768:
				indice_list.append(first)
				indexes.append(Index(first, True))
				#normal is second with first bit set to zero
				tri_normal = second - 32768
				#write_to_log("NEW definition with normal: " + str(tri_normal))
			#index to a definition, not a definition
			else:
				indexes.append(Index(indice_list[first], False))
		
		#write_to_log(indexes)
		
		new_part.triangles.append(Triangle(indexes, tri_normal))
	
	indice_list = []
	#TEXTURE COORDINATE INDEXES
	numbers_to_follow = int(struct.unpack("i", bin_file.read(4))[0])
	write_debug("    " + str(numbers_to_follow) + " extra numbers to read")
	write_debug("    reading extra numbers from offset: " + str(bin_file.tell()))
	for tri_index in range(numbers_to_follow/3):
		
		texture_indexes = []
		for point_index in range(3):
			new_index = int(struct.unpack("i", bin_file.read(4))[0])
		
			if new_part.triangles[tri_index].indexes[point_index].is_definition:
				indice_list.append(new_index)
				texture_indexes.append(Index(new_index, True))
			else:
				texture_indexes.append(Index(indice_list[new_index], False))
		
		new_part.triangles[tri_index].texture_indexes = texture_indexes
	
	#COLOR OF INDICES
	red = struct.unpack("B", bin_file.read(1))[0]
	green = struct.unpack("B", bin_file.read(1))[0]
	blue = struct.unpack("B", bin_file.read(1))[0]
		
	new_part.color = (red, green, blue)
		
	zero = int(struct.unpack("i", bin_file.read(4))[0])
	something = int(struct.unpack("i", bin_file.read(4))[0])

	#text of what texture is going to be used
	size_of_texture_name = int(struct.unpack("i", bin_file.read(4))[0])
	texture_name = struct.unpack(str(size_of_texture_name) + "s", bin_file.read(size_of_texture_name))[0][:-4].replace(" ", "")
	new_part.texture_name = texture_name
	write_debug("    texture name: " + texture_name)
		
	#text of material used
	size_of_material_name = int(struct.unpack("i", bin_file.read(4))[0])
	material_name = struct.unpack(str(size_of_material_name) + "s", bin_file.read(size_of_material_name))[0].replace(" ", "")
	new_part.material_name = material_name
	write_debug("    material name: " + material_name)
	
	#add name to MATERIALS for later export and .mtl file
	#use texture name, unless this part is not textured, in which case use material name
	if texture_name == "":
		name_to_use = material_name
	else:
		name_to_use = texture_name
	
	#look for duplicates in MATERIALS list
	dont_add = False
	for each_material in MATERIALS:
		if each_material.name == name_to_use:
			dont_add = True
	if dont_add == False:
		MATERIALS.append(Material(name_to_use, new_part.color))
	
	model.parts.append(new_part)
	
	return model
		
		
def read_gif(bin_file, read_string=True):
	if read_string:
		string_length = int(struct.unpack("i", bin_file.read(4))[0])
		file_name = struct.unpack(str(string_length) + "s", bin_file.read(string_length))[0][:-4]
	else:
		file_name = "HIDDEN"
	
	width = int(struct.unpack("i", bin_file.read(4))[0])
	height = int(struct.unpack("i", bin_file.read(4))[0])
	num_colors = int(struct.unpack("i", bin_file.read(4))[0])
	
	write_debug("NAME: " + file_name)
	write_debug("WIDTH: " + str(width))
	write_debug("HEIGHT: " + str(height))
	write_debug("NUMCOLORS: " + str(num_colors))
	
	colors = []
	for each_color in range(num_colors):
		r = int(struct.unpack("B", bin_file.read(1))[0])
		g = int(struct.unpack("B", bin_file.read(1))[0])
		b = int(struct.unpack("B", bin_file.read(1))[0])
		colors.append((r, g, b))
	
	draw_image = pygame.surface.Surface([width, height])
	
	for y in range(height):
		for x in range(width):
			try:
				index = int(struct.unpack("B", bin_file.read(1))[0])
				new_color = colors[index]
			except:
				new_color = (0, 0, 0)
			draw_image.set_at([x, y], new_color)
		
	return draw_image, file_name
		
		
def export_obj(model_file, model, filename):
	#correct texture coordinates
	#for each_part in each_



	file = open(filename + ".obj", "w")
	file.truncate()

	file.write("mtllib " + str(model_file.name) + ".mtl\n")
	
	for each_vertice in model.vertices:
		file.write("v " + str(each_vertice.x) + " " + str(each_vertice.y) + " " + str(each_vertice.z) + "\n")
		
	for each_text_coor in model.texture_coordinates:
		file.write("vt " + str(each_text_coor.x) + " " + str(each_text_coor.y) + "\n")
		
	for each_normal in model.normals:
		file.write("vn " + str(each_normal.x) + " " + str(each_normal.y) + " " + str(each_normal.z) + "\n")
		
	part_index = -1
	for each_part in model.parts:
		part_index += 1
		file.write("o " + str(part_index) + "\n")
		
		#try to use texture_name, otherwise material_name
		if each_part.texture_name == "":
			file.write("usemtl " + str(each_part.material_name) + "\n")
		else:
			file.write("usemtl " + str(each_part.texture_name) + "\n")
		
		for each_triangle in each_part.triangles:
			file.write("f ")
			for i in range(3):
				if len(each_triangle.texture_indexes) > 0:
					file.write(str(each_triangle.indexes[i].value+1) + "/" + str(each_triangle.texture_indexes[i].value+1) + "/" + str(each_triangle.normal+1))
				else:
					file.write(str(each_triangle.indexes[i].value+1) + "/1/" + str(each_triangle.normal+1))
				file.write(" ")
					
			file.write("\n")
			
	file.close()
	
	
def export_mtl(model_file, filename):
	file = open(filename + ".mtl", "w")
	file.truncate()
		
	for each_material in model_file.materials:
		file.write("newmtl " + str(each_material.name) + "\n")
		file.write("Ns 0\n")
		file.write("Ka 0.000000 0.000000 0.000000\n")
		file.write("Kd 0.8 0.8 0.8\n")
		file.write("Ks 0.8 0.8 0.8\n")
		file.write("d 1\n")
		file.write("illum 2\n")
		
		file.write("map_Ka " + str(each_material.name) + ".png\n")
		file.write("map_Kd " + str(each_material.name) + ".png\n")
		file.write("map_Ks " + str(each_material.name) + ".png\n")
		
	file.close()
	
	
def extract_wdb():
	while(True):
		try:
			bin_file = open(SETTINGS["path_to_wdb"], "rb")
			break
		except:
			write_to_log("Cannot find WDB file at: " + str(SETTINGS["path_to_wdb"]))
			
	#HEADER
	num_groups = int(struct.unpack("i", bin_file.read(4))[0])
	
	for group_num in range(num_groups):
		#size of string
		size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
		#group_title
		group_title = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]
		write_to_log("Reading Folder: " + group_title)
		
		#READ GROUP
		num_sub_groups = 2
		for sub_group_num in range(num_sub_groups):
			#SUBGROUP
			num_sub_items = int(struct.unpack("i", bin_file.read(4))[0])
			write_debug("Number of items in Subgroup #" + str(sub_group_num+1) + ": " + str(num_sub_items))
			for each_sub_item in range(num_sub_items):
				#ITEMS IN SUBGROUPS
			
				#size of string
				size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
				#sub_item_title
				sub_item_title = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]
				write_debug("Subgroup Item Title: " + sub_item_title)
				
				size_of_item = int(struct.unpack("i", bin_file.read(4))[0])
				#write_to_log("Subgroup Item Size: " + str(size_of_item))
				offset_of_item = int(struct.unpack("i", bin_file.read(4))[0])
				#write_to_log("Subgroup Item Offset: " + str(offset_of_item))
				
				#LegoEntityPresenter
				#these only exist inside the second subgroup items of each group
				if sub_group_num == 1:
					#size of string
					size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
					presenter_title = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]
					#write_to_log(presenter_title)
					bin_file.read(37)
					
				previous_offset = bin_file.tell()
				
				#make folders
				newpath = SETTINGS["group_path"] + group_title[:-1] + "/sub" + str(sub_group_num)
				if not os.path.exists(newpath):
					os.makedirs(newpath)
				
				#write subgroup file
				bin_file.seek(offset_of_item)
				write_file = open(SETTINGS["group_path"] + group_title[:-1] + "/sub" + str(sub_group_num) + "/" + sub_item_title[:-1] + ".bin", "wb")
				write_file.truncate()
				for each_byte in range(size_of_item):
					write_file.write(bin_file.read(1))
				write_file.close()
				
				bin_file.seek(previous_offset)
					
			
	write_to_log("Done reading bin files from WORLD.WDB")
	write_to_log("Reading GIF images")
			
	#GIF IMAGES
			
	#make folders
	newpath = SETTINGS["image_path"]
	if not os.path.exists(newpath):
		os.makedirs(newpath)
			
	#read data
	image_section_size = int(struct.unpack("i", bin_file.read(4))[0])
	
	num_images = int(struct.unpack("i", bin_file.read(4))[0])
	
	for each_image in range(num_images):
		data = []

		draw_image, file_name = read_gif(bin_file)
		
		pygame.image.save(draw_image, SETTINGS["image_path"] + file_name + ".png")
	
#return error if it didnt work, None if success
#extracts a .bin file from the specified path bin_file_name
def extract_bin_group(bin_file_name, global_offset=0):
	global MATERIALS

	MATERIALS = []

	while(True):
		try:
			bin_file = open(bin_file_name, "rb")
			break
		except:
			error = "File '" + bin_file_name + "' cannot be found!"
			return error
	
	bin_file.seek(global_offset)
	
	#MODEL FILE
	model_file = ModelFile()
	
	
	#magic number?? always 19 or 0x13
	model_file.magic_number = int(struct.unpack("i", bin_file.read(4))[0])
	#number of bytes after this number to read until end of file
	model_file.bytes_left_in_subgroup = int(struct.unpack("i", bin_file.read(4))[0])
	#version?? seems to be 1 in every file
	model_file.version = int(struct.unpack("i", bin_file.read(4))[0])
	#zero
	unknown = int(struct.unpack("i", bin_file.read(4))[0])
	#zero
	unknown = int(struct.unpack("i", bin_file.read(4))[0])
	
	size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
	model_file.name = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]

	bin_file.read(8)
	
	model_file.num_components = int(struct.unpack("i", bin_file.read(4))[0])
	#COMPONENT HEADER
	for each_component in range(model_file.num_components):
		new_component = Component()
		
		size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
		new_component.name = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]
		new_component.num_component_parts = int(struct.unpack("h", bin_file.read(2))[0])
		#COMPONENT PARTS
		for each_component_part in range(new_component.num_component_parts):
			bin_file.read(16)
		bin_file.read(10)
		#END COMPONENT PARTS
		
		model_file.components.append(new_component)
	#END COMPONENT HEADER
	
	
	
	size_of_string = int(struct.unpack("i", bin_file.read(4))[0])
	string = struct.unpack(str(size_of_string) + "s", bin_file.read(size_of_string))[0]
	bin_file.read(45)
	
	#number of models in this file / the number of LODs for this component
	model_file.num_models = int(struct.unpack("i", bin_file.read(4))[0])
	write_debug(str(model_file.num_models) + " MODELS in this file...")
	
	offset_of_next_component = int(struct.unpack("i", bin_file.read(4))[0])
	
	#MODELS
	for each_model in range(model_file.num_models):
		new_model = Model()
		write_debug("reading new MODEL")
		
		something = int(struct.unpack("i", bin_file.read(4))[0])
		
		#number of parts, as in how many sections of triangles the model is made out of
		new_model.num_parts = int(struct.unpack("i", bin_file.read(4))[0])
		#number of verticies to follow
		new_model.num_verts = int(struct.unpack("h", bin_file.read(2))[0])
		#number of normals after verticies
		new_model.num_normals = int(struct.unpack("h", bin_file.read(2))[0]) 
		#number of texture coordinates after normals
		new_model.num_texture_coordinates = int(struct.unpack("h", bin_file.read(2))[0])
		
		write_debug(str(new_model.num_parts) + " parts in this model")
		
		unknown = int(struct.unpack("h", bin_file.read(2))[0])
		
		#new_model.write_to_log_info()


		#VERTICES
		write_debug("reading VERTICES from offset: " + str(bin_file.tell()))
		for each_point in range(new_model.num_verts):
			#write_to_log("Getting VERT from offset: " + str(bin_file.tell()))
			x = struct.unpack("f", bin_file.read(4))[0] * 200
			y = struct.unpack("f", bin_file.read(4))[0] * 200
			z = struct.unpack("f", bin_file.read(4))[0] * 200
			new_model.vertices.append(Point(x, -y, z, len(new_model.vertices)))
			#write_to_log("X: " + str(x) + ", Y: " + str(y) + ", Z: " + str(z))
				
		write_debug("    read " + str(len(new_model.vertices)) + " VERTICES!")
		#END VERTICES
		
		#NORMALS
		write_debug("reading NORMALS from offset: " + str(bin_file.tell()))
		for each_point in range(new_model.num_normals/2):
			#write_to_log("Getting NORMAL from offset: " + str(bin_file.tell()))
			x = struct.unpack("f", bin_file.read(4))[0] * 200
			y = struct.unpack("f", bin_file.read(4))[0] * 200
			z = struct.unpack("f", bin_file.read(4))[0] * 200
			new_model.normals.append(Point(x, -y, z, len(new_model.normals)))
			#write_to_log("X: " + str(x) + ", Y: " + str(y) + ", Z: " + str(z))
				
		write_debug("    read " + str(len(new_model.normals)) + " NORMALS!")
		#END NORMALS
		
		#TEXTURE COORDINATES
		write_debug("reading TEXTURE COORDINATES from offset: " + str(bin_file.tell()))
		for each_point in range(new_model.num_texture_coordinates):
			#write_to_log("Getting TEXTURE COORDINATES from offset: " + str(bin_file.tell()))
			x = struct.unpack("f", bin_file.read(4))[0] * 200
			y = struct.unpack("f", bin_file.read(4))[0] * 200
			
			x = x - 200
			x = x/200.0
			
			y = y - 200
			y = y/200.0
			
			new_model.texture_coordinates.append(TextureCoordinate(x, -y))
			#write_to_log("X: " + str(x) + ", Y: " + str(y))
		write_debug("    read " + str(len(new_model.texture_coordinates)) + " TEXTURE COORDINATES!")
		#END TEXTURE COORDINATES
				
		#PARTS
		for each_part in range(new_model.num_parts):
			new_model = read_indices(bin_file, new_model)
		
		model_file.models.append(new_model)
		write_debug("  finished reading model at offset: " + str(bin_file.tell()))
		#END PARTS

	write_debug("finishing at offset: " + str(bin_file.tell()))
	write_debug("DONE!!!")
	#END MODELS
	
	
	model_file.materials = MATERIALS
	
	#make path and folders for obj export
	newpath = SETTINGS["obj_path"] + bin_file_name[:bin_file_name.rfind(".")] + "/"
	if not os.path.exists(newpath):
		os.makedirs(newpath)
	
	#export each model LOD as an .obj
	model_index = model_file.num_models
	for each_model in model_file.models:
		export_obj(model_file, each_model, newpath + model_file.name + "_lod" + str(model_index))
		model_index -= 1
	
	
	#GIF IMAGES
	zero = int(struct.unpack("i", bin_file.read(4))[0])
	num_images = int(struct.unpack("i", bin_file.read(4))[0])
	zero = int(struct.unpack("i", bin_file.read(4))[0])
	
	write_debug("reading " + str(num_images) + " GIF files")
	
	found_materials = []
	#export textures embedded in this bin group as .png
	for each_image in range(num_images):
		draw_image, file_name = read_gif(bin_file)
		#special hidden textures, only seen on isle_hi
		if file_name[-1:] == "X":
			hide_image, file_name2 = read_gif(bin_file, False)
			pygame.image.save(hide_image, newpath + "hide_" + file_name + ".png")
		
		pygame.image.save(draw_image, newpath + file_name + ".png")
		
		found_materials.append(file_name)
		write_debug("    finished reading material at offset: " + str(bin_file.tell()))
	
	#export materials without textures as .png, just their rgb on a 4x4 texture
	for each_material in MATERIALS:
		if each_material.name not in found_materials:
			new_image = pygame.surface.Surface([4, 4])
			new_image.fill(each_material.color)
			pygame.image.save(new_image, newpath + each_material.name + ".png")
	
	export_mtl(model_file, newpath + model_file.name)
	
	return None
	
	
#same as extract_bin_group except it will handle errors and delete broken obj outputs
def extract_bin_group_safe(each_name):
	error = "Could not interpret '" + each_name + "' correctly."
	try:
		error = extract_bin_group(each_name)
		write_debug("EXTRACTED: " + str(each_name))
		INFO["files_read"] += 1
	except Exception, ex:
		#import traceback
		#print(traceback.print_exc())
		#time.sleep(30)
	
		top = "./obj" + each_name[1:each_name.rfind(".")]
		top = top.replace("\\", "/")

		write_debug("deleting: " + top)
		try:
			shutil.rmtree(top)
		except:
			write_debug("error deleting: " + top)
		INFO["files_not_read"] += 1
		
	return error
	
#extracts wdb file, and then converts all bin files to obj with materials
def extract_wdb_and_bin():
	write_to_log("=====START OF LOG - (" + datetime.datetime.now().strftime("%A, %B %d %Y %I:%M%p") + ")=====")

	#extract all .bin files from wdb, and images
	extract_wdb()
	
	#find all files in the groups folder that end in .bin
	bin_files = [os.path.join(root, name)
             for root, dirs, files in os.walk(SETTINGS["group_path"])
             for name in files
             if name.endswith((".bin"))]
	
	#extract all .bin files and export as obj with materials
	for each_name in bin_files:
		write_to_log("extracting: " + each_name)
		pygame.display.set_caption("FILES READ: " + str(INFO["files_read"]) + " // FILES UNREADABLE: " + str(INFO["files_not_read"]))
		extract_bin_group_safe(each_name)
	
	
#presents GUI with options for extraction
def main():
	screen.fill((200, 200, 200))
	write_to_screen("Press 'w' for .WDB extract")
	write_to_screen("Press 'b' for .BIN extract", [0, SETTINGS["font_size"]*2])
		
	asking = True
	while(asking):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit(0)
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_w:
					extract_wdb_and_bin()
					write_to_log("DONE extracting WORLD.WDB!")
					wait_for_input()
				if event.key == pygame.K_b:
					extracting = True
					while(extracting):
						path = get_text()
						write_to_log("EXTRACTING BIN FILE FROM PATH: " + str(path))
						error = extract_bin_group_safe(path)
						if error == None:
							extracting = False
							write_to_log("SUCCESSFULLY EXTRACTED " + str(path))
							wait_for_input()
						else:
							write_to_log(error)
							wait_for_input()
							
				screen.fill((200, 200, 200))
				write_to_screen("Press 'w' for .WDB extract")
				write_to_screen("Press 'b' for .BIN extract", [0, SETTINGS["font_size"]*2])
					
		pygame.display.flip()
		
main()