import pygame
import sys
import struct
import math
import pickle

from formatter import get_formatted_data
from formatter import get_raw

pygame.init()

SETTINGS = {
    "screen_x": 700,
    "screen_y": 800,

    "cells_per_row": 16,

    "filename": raw_input("FILE: "),
    "format": raw_input("FORMAT: "),
    "pattern": raw_input("PATTERN: "),

    "ignore_pattern": False,
}
pygame.display.set_caption(SETTINGS["filename"])

SETTINGS["cell_width"] = SETTINGS["screen_x"] / SETTINGS["cells_per_row"]
SETTINGS["cell_height"] = SETTINGS["cell_width"]

#round the screen width to the nearest cell
SETTINGS["screen_x"] = SETTINGS["cell_width"] * SETTINGS["cells_per_row"]

INFO = {
    "x_offset": 0,
    "y_offset": 0,

    "update_display": True,
    "update_overlay": True,
}

ABORT = False

screen = pygame.display.set_mode([SETTINGS["screen_x"], SETTINGS["screen_y"]])

main_font = pygame.font.Font("monaco.ttf", SETTINGS["cell_width"]/2)

class Overlay(object):
    def __init__(self):
        self.icons = {}

    def draw(self):
        for key in self.icons:
            self.icons[key].draw()

class Icon(object):
    def __init__(self, image, pos):
        self.image = image
        self.pos = pos
    def draw(self):
        screen.blit(self.image, self.pos)

class Editor(object):
    def __init__(self, bin_file):
        self.file = bin_file
        self.data = []
        self.groups = []

        #self.load()
        self.populate()
        self.update_rects()

    def update_rects(self):
        for each_data in self.data:
            each_data.update_rect()
        for each_group in self.groups:
            each_group.update_rect()

    def load(self):
        try:
            save_file = open(self.file.name + "_bd.sav", "rb")
            self.groups = pickle.load(save_file)
        except:
            pass

    def save(self):
        save_file = open(self.file.name + "_bd.sav", "wb")
        save_file.truncate()

        pickle.dump(self.groups, save_file)

    def draw(self):
        screen.fill((0, 0, 0))

        for each_data in self.data:
            each_data.draw()

        for each_group in self.groups:
            each_group.draw()

    #load bytes from file, only what is needed to be drawn on the screen
    def populate(self):
        self.data = []

        length_to_read = (SETTINGS["cells_per_row"])* (SETTINGS["screen_y"]/SETTINGS["cell_height"])

        self.file.seek(-INFO["y_offset"]*SETTINGS["cells_per_row"])
        for each_byte in range(length_to_read):
            try:
                new_byte = int(struct.unpack("B", self.file.read(1))[0])
            except:
                break

            new_data = Data(new_byte, self.file.tell()-1)

            self.data.append(new_data)

class Data(object):
    def __init__(self, value, offset):
        self.value = value
        self.offset = offset

        self.update_rect()

    def update_rect(self):
        rect = calculate_rect(self.offset, 1)
        self.pos = [rect[0], rect[1]]
        self.width = rect[2]
        self.height = rect[3]

    def is_in(self, pos):
        if pos[0] > self.pos[0] and pos[0] < self.pos[0]+self.width:
            if pos[1] > self.pos[1] and pos[1] < self.pos[1]+self.height:
                return True

        return False

    def draw(self, selected=False):
        draw_x = self.pos[0]
        draw_y = self.pos[1]

        if draw_y > SETTINGS["screen_y"] or draw_y < 0 or draw_x > SETTINGS["screen_x"] or draw_x < 0:
            return

        if selected:
            pygame.draw.rect(screen, (200, 200, 0), (draw_x, draw_y, self.width, self.height), 0)
        else:
            pygame.draw.rect(screen, (20, 20, 20), (draw_x, draw_y, self.width, self.height), 1)

        text = main_font.render(hex(self.value)[2:].zfill(2).upper(), True, (255, 255, 255))
        screen.blit(text, [draw_x+(self.width/2)-text.get_width()/2, draw_y+(self.height/2)-text.get_height()/2])

class Group(object):
    def __init__(self, name, data_string, offset, bin_file):
        self.name = name
        self.data_string = data_string
        self.offset = offset

        self.value = str(get_raw((data_string, offset), bin_file))

        self.update_rect()

    def update_rect(self):
        rect = calculate_rect(self.offset, self.get_length())
        self.pos = [rect[0], rect[1]]
        self.width = rect[2]
        self.height = rect[3]

    def is_in(self, pos, force_pos=None):
        if force_pos == None:
            draw_x = self.pos[0]
            draw_y = self.pos[1]
        else:
            draw_x = force_pos[0]
            draw_y = force_pos[1]

        #check if pos is in the firstmost rectangle
        if pos[0] > draw_x and pos[0] < draw_x+self.width:
            if pos[1] > draw_y and pos[1] < draw_y+self.height:
                return True

        #otherwise check if group goes off edge of screen to check if pos is in the next line
        """if draw_x+self.width > SETTINGS["screen_x"]:
            screen_edge = SETTINGS["cell_width"]*SETTINGS["cells_per_row"]
            new_draw_pos = [-(screen_edge-(draw_x)), draw_y+SETTINGS["cell_height"]]
            return self.is_in(pos, new_draw_pos)"""

        #otherwise return false
        return False

    def get_color(self):
        colors = {
            "i": (0, 200, 0),
            "h": (0, 100, 0),
            "b": (0, 0, 150),
            "f": (170, 0, 130),
            "s": (150, 0, 0),
        }
        if self.data_string[0].lower() in colors:
            return colors[self.data_string[0].lower()]
        else:
            return (255, 255, 255)

    def get_length(self):
        lengths = {
            "i": 4,
            "h": 2,
            "b": 1,
            "f": 4,
        }
        first_char = self.data_string[0].lower()
        if first_char == "s":
            # If the length happens to have been loaded as an error in the form,
            # make sure that something useable is returned for length.
            try:
                return int(self.data_string[1:])
            except:
                return 0

        # Make sure the form is in the dictionary before getting the length
        elif first_char in lengths:
            return int(lengths[first_char])
        else:
            return 0

    def draw(self, force_pos=None):
        try:
            if force_pos == None:
                draw_x = self.pos[0]
                draw_y = self.pos[1]
            else:
                draw_x = force_pos[0]
                draw_y = force_pos[1]

            if draw_y > SETTINGS["screen_y"] or draw_y < 0 or draw_x > SETTINGS["screen_x"] or draw_x < 0:
                if force_pos == None:
                    return

            #draw rect
            pygame.draw.rect(screen, self.get_color(), (draw_x, draw_y, self.width, self.height), 0)
            pygame.draw.rect(screen, (0, 0, 0), (draw_x, draw_y, self.width, self.height), 1)

            #if group goes off edge of screen, redraw it on the next line
            if draw_x+self.width > SETTINGS["screen_x"]:
                screen_edge = SETTINGS["cell_width"]*SETTINGS["cells_per_row"]
                new_draw_pos = [-(screen_edge-(draw_x)), draw_y+SETTINGS["cell_height"]]
                self.draw(new_draw_pos)

            #draw text
            text = main_font.render(self.value, True, (255, 255, 255))

            #if the text is wider than the group box, convert to rounded scientific notation
            if text.get_width() > self.width and self.data_string == "f":
                self.value = "%.2E" % float(self.value)
                text = main_font.render(self.value, True, (255, 255, 255))
            if text.get_width() > self.width:
                text = pygame.transform.scale(text, (self.width, int(text.get_height() * (float(self.width)/float(text.get_width())))))

            screen.blit(text, [draw_x+(self.width/2)-text.get_width()/2, draw_y+(self.height/2)-text.get_height()/2])
        except:
            print("Could not draw " + str(self.name) + " of " + str(self.data_string) + " at " + str(self.offset))


def calculate_rect(offset, length):
    new_width = SETTINGS["cell_width"]
    new_height = SETTINGS["cell_height"]

    pixels_down = INFO["y_offset"]*new_height
    new_y = (offset/SETTINGS["cells_per_row"]) * new_height
    new_x = (offset%SETTINGS["cells_per_row"]) * new_width
    new_y += pixels_down

    return (new_x, new_y, new_width*length, new_height)

def get_num():
    got_num = ""
    while(True):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_0:
                    got_num += "0"
                if event.key == pygame.K_1:
                    got_num += "1"
                if event.key == pygame.K_2:
                    got_num += "2"
                if event.key == pygame.K_3:
                    got_num += "3"
                if event.key == pygame.K_4:
                    got_num += "4"
                if event.key == pygame.K_5:
                    got_num += "5"
                if event.key == pygame.K_6:
                    got_num += "6"
                if event.key == pygame.K_7:
                    got_num += "7"
                if event.key == pygame.K_8:
                    got_num += "8"
                if event.key == pygame.K_9:
                    got_num += "9"

                if event.key == pygame.K_RETURN:
                    if got_num != "":
                        return int(got_num)

#Call get_nested_values recursively if value is a dict or list, otherwise just
# append value to values.
def branch_nested_values(values, value, key=None):
    if isinstance(value, dict) or isinstance(value, list):
        values += get_nested_values(value)
    else:
        if key != None:
            values.append((key, value))

def get_nested_values(structure):
    values = []
    if isinstance(structure, dict):
        for key in structure:
            value = structure[key]
            branch_nested_values(values, value, key)
    else:
        for value in structure:
            branch_nested_values(values, value)
    return values


def main():
    bin_file = open(SETTINGS["filename"], "rb")

    editor = Editor(bin_file)
    overlay = Overlay()

    bin_file.seek(0)
    if SETTINGS["ignore_pattern"] == False:
        data = get_formatted_data(bin_file, SETTINGS["format"], SETTINGS["pattern"])

        #tuple_data is (key, (data_string, offset))
        nested_values = sorted(get_nested_values(data), key=lambda x: x[1][1])
        nested_index = 0

        for tuple_data in nested_values:
            key = tuple_data[0]
            data_string = tuple_data[1][0]
            offset = tuple_data[1][1]

            new_group = Group(key, data_string, offset, bin_file)
            editor.groups.append(new_group)

    selected_data = None
    while(True):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                #editor.save()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                INFO["update_display"] = True
                if event.key == pygame.K_i:
                    editor.groups.append(Group("UNDEFINED", "i", selected_data.offset, bin_file))
                if event.key == pygame.K_h:
                    editor.groups.append(Group("UNDEFINED", "h", selected_data.offset, bin_file))
                if event.key == pygame.K_b:
                    editor.groups.append(Group("UNDEFINED", "B", selected_data.offset, bin_file))
                if event.key == pygame.K_f:
                    editor.groups.append(Group("UNDEFINED", "f", selected_data.offset, bin_file))
                if event.key == pygame.K_s:
                    length = get_num()
                    editor.groups.append(Group("UNDEFINED", "s"+str(length), selected_data.offset, bin_file))

                if event.key == pygame.K_BACKSPACE:
                    for each_group in editor.groups:
                        if each_group.offset == selected_data.offset:
                            editor.groups.remove(each_group)

                if event.key == pygame.K_g:
                    offset = get_num()
                    INFO["y_offset"] = -int(offset/SETTINGS["cells_per_row"])
                    editor.update_rects()
                    editor.populate()

                if event.key == pygame.K_SPACE:
                    if nested_index < len(nested_values)-1:
                        tuple_data = nested_values[nested_index]
                        key = tuple_data[0]
                        data_string = tuple_data[1][0]
                        offset = tuple_data[1][1]

                        if not data_string.startswith("s"):
                            new_group = Group(key, data_string, offset, bin_file)
                            editor.groups.append(new_group)

                        nested_index += 1
                    else:
                        print("NO MORE NESTED VALUES")

            if event.type == pygame.MOUSEBUTTONDOWN:
                INFO["update_display"] = True
                if event.button == 4:
                    if INFO["y_offset"] < 0:
                        INFO["y_offset"] += 1
                        editor.update_rects()
                        editor.populate()
                        selected_data = None
                elif event.button == 5:
                    INFO["y_offset"] -= 1
                    editor.update_rects()
                    editor.populate()
                    selected_data = None

        #select data with the mouse
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            for each_data in editor.data:
                if each_data.is_in(mouse_pos):
                    INFO["update_display"] = True
                    selected_data = each_data

        #hover over groups with the mouse
        try:
            del(overlay.icons["mouse_icon"])
        except:
            pass
        for each_group in editor.groups:
            if each_group.is_in(mouse_pos):
                INFO["update_overlay"] = True
                name_text = main_font.render(each_group.name, True, (50, 50, 50))
                name_rect = pygame.surface.Surface((name_text.get_width(), name_text.get_height()))
                name_rect.fill((255, 255, 255))
                name_rect.blit(name_text, (0, 0))
                name_pos = [mouse_pos[0], mouse_pos[1]+10]
                if name_pos[0]+name_rect.get_width() > SETTINGS["screen_x"]:
                    name_pos[0] = SETTINGS["screen_x"]-name_rect.get_width()
                overlay.icons["mouse_icon"] = Icon(name_rect, name_pos)

        #only redraw editor if required
        if INFO["update_display"]:
            INFO["update_display"] = False

            #draw editor and selected_data
            editor.draw()
            if selected_data != None:
                selected_data.draw(True)
            #save a bg_image so that it does not have to be redrawn with every overlay update
            INFO["bg_image"] = pygame.surface.Surface((screen.get_width(), screen.get_height()))
            INFO["bg_image"].blit(screen, (0, 0))

        if INFO["update_overlay"]:
            screen.blit(INFO["bg_image"], (0, 0))
            overlay.draw()


        pygame.display.flip()

main()
