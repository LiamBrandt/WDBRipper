# WDBRipper
Extracts the 3D models and textures from the Lego Island WORLD.WDB file.

Most of the files in the sub1 folders can be read, the ones in sub0 cannot. This is something that can be worked on for the future.

As of now, 451 out of 592 .bin files can be extracted!

##Requirements:
 * Python 2.7 https://www.python.org/downloads/
 * PyPNG https://pythonhosted.org/pypng/index.html

##Usage:
 * Run the executable:

 ```
 wdb_ripper.exe
 ```

 * Or run the python script:

 ```
 python wdb_ripper.py
 ```

 * You can configure the tool with `config.txt`.

##Understanding:
The wdb file is split into many sections in a folder hierarchy, each section for a different model. The ripper currently extracts each of these sections, and saves each of them as a .bin file in their respective folder. You can find these files in `./bin` once the tool has been run. There are also loose GIF images in the wdb file not attached to any models, which are stored in `./gif`.

Once the ripper has extracted all of the .bin files, the ripper will create 3D wavefront .obj files with .mtl material files plus all the textures as .png for that model. These converted models are stored in `./obj`.

More information on the format of `WORLD.WDB` can be found in `./formats/wdb`, the file used to define what variables are extracted for what purpose.

 * Source Files
   * **`wdb_ripper.py`** is the main program that takes data read from the bin files, and exports it as .obj, .mtl, and .gif.
   * **`formatter.py`** reads the file `./formats/wdb` and uses it to interpret the data found in `WORLD.WDB` and the .bin files. It hands `wdb_ripper.py` a dictionary containing the structure of the files as described in `./formats/wdb`.
   * **`bin_decode3.py`** is a helpful tool to visualize what is going on inside a .bin file in terms of the format of data. It uses `formatter.py` to display the values of each piece of data in the file. You need pygame to run this.
   * **`color_console.py`** does not play a role, it was for debug purposes to help make the console output of `formatter.py` more readable. It was taken from an online example.
