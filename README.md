# WDBRipper
Extracts the 3D models and textures from the Lego Island WORLD.WDB format.

As of now, only about 300 of the 500 total files can be read. The files that cannot be read are ones that have animations, and I am working on figuring out the format for those ones.

##Requirements:
 * Python 2.7 https://www.python.org/downloads/
 * Pygame http://www.pygame.org/download.shtml

##Usage:
 * The wdb file is split into many sections in a folder hierarchy, each section for a different model. The ripper is currently just extracting each of these sections, and saving them as .bin files in their respective folders. You can find these files in the "groups" folder once the tool has been run. There are also loose GIF images that are in the wdb file, not attached to any models, and those are stored in the "images" folder.
 * Once the ripper has extracted all of the .bin files, the ripper will create 3D files in .obj file format with .mtl material files with all the textures for that model, in the "obj" folder.
 * You can change the path to your WORLD.WDB file in config.txt
 * The format of WORLD.WDB is explained more in depth in the format.txt file.