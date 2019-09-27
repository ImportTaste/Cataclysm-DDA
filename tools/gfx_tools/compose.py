#!/bin/python

# decompose.py
# Split a gfx tile_config.json into 1000s of little directories, each with their own config
# file and tile image.

import argparse
import copy
import json
import os
import string
import subprocess

FALLBACK = {
    "file": "fallback.png",
    "tiles": [],
    "ascii": [
    { "offset": 0, "bold": False, "color": "BLACK" },
    { "offset": 256, "bold": True, "color": "WHITE" },
    { "offset": 512, "bold": False, "color": "WHITE" },
    { "offset": 768, "bold": True, "color": "BLACK" },
    { "offset": 1024, "bold": False, "color": "RED" },
    { "offset": 1280, "bold": False, "color": "GREEN" },
    { "offset": 1536, "bold": False, "color": "BLUE" },
    { "offset": 1792, "bold": False, "color": "CYAN" },
    { "offset": 2048, "bold": False, "color": "MAGENTA" },
    { "offset": 2304, "bold": False, "color": "YELLOW" },
    { "offset": 2560, "bold": True, "color": "RED" },
    { "offset": 2816, "bold": True, "color": "GREEN" },
    { "offset": 3072, "bold": True, "color": "BLUE" },
    { "offset": 3328, "bold": True, "color": "CYAN" },
    { "offset": 3584, "bold": True, "color": "MAGENTA" },
    { "offset": 3840, "bold": True, "color": "YELLOW" }
    ]
}

# stupid stinking Python 2 versus Python 3 syntax
def write_to_json(pathname, data):
    with open(pathname, "w") as fp:
        try:
            json.dump(data, fp)
        except ValueError:
            fp.write(json.dumps(data))


def find_or_make_dir(pathname):
    try:
        os.stat(pathname)
    except OSError:
        os.mkdir(pathname)


def convert_pngname_to_pngnum(tile_entry, pngname_to_pngnum):
    bg_id = tile_entry.get("bg")
    if bg_id:
        tile_entry["bg"] = pngname_to_pngnum[bg_id]

    add_tile_entrys = tile_entry.get("additional_tiles", [])
    for add_tile_entry in add_tile_entrys:
        convert_pngname_to_pngnum(add_tile_entry, pngname_to_pngnum)

    new_fg = []
    read_pngnames = tile_entry.get("fg")
        
    if isinstance(read_pngnames, list):
        for pngname in read_pngnames:
            if isinstance(pngname, dict):
                sprite_ids = pngname.get("sprite")
                valid = False
                if isinstance(sprite_ids, list):
                    new_sprites = []
                    for sprite_id in sprite_ids:
                        if sprite_id != "no_entry":
                            new_sprites.append(pngname_to_pngnum[sprite_id])
                            valid = True
                    pngname["sprite"] = new_sprites
                else:
                    if sprite_ids and sprite_ids != "no_entry":
                        pngname["sprite"] = pngname_to_pngnum[sprite_ids]
                        valid = True
                if valid:
                    new_fg.append(pngname)
            elif pngname != "no_entry":
                new_fg.append(pngname_to_pngnum[pngname])
    elif read_pngnames and read_pngnames != "no_entry":
        new_fg.append(pngname_to_pngnum[read_pngnames])
    if new_fg:
        tile_entry["fg"] = new_fg
    return tile_entry


def merge_pngs(ts_path, row_pngs, row_num, pngnum, width, height):
    spacer = 16 - len(row_pngs)
    pngnum += spacer
    offset_x = 0
    offset_y = 0

    cmd = ["montage"]
    for png_pathname in row_pngs:
        if png_pathname == "null_image":
            cmd.append("null:")
        else:
            cmd.append(png_pathname)

    tmp_path = "{}/tmp_{}.png".format(ts_path, row_num)
    cmd += ["-tile", "16x1","-geometry", "{}x{}+{}+{}".format(width, height, offset_x, offset_y)]
    cmd += [tmp_path]
    failure = subprocess.check_output(cmd)
    if failure:
        print("failed: {}".format(failure))

    return pngnum, tmp_path


def finalize_merges(ts_filepath, merge_pngs, width, height):
    cmd = ["montage"] + merge_pngs
    cmd += ["-tile", "1", "-geometry", "{}x{}".format(16 * width, height), ts_filepath]
    failure = subprocess.check_output(cmd)
    if failure:
        print("failed: {}".format(failure))
    for merged_png in merge_pngs:
        os.remove(merged_png)


args = argparse.ArgumentParser(description="Merge all the individal tile_entries and pngs in a tileset's directory into a tile_config.json and 1 or more tilesheet pngs.")
args.add_argument("tileset_dir", action="store",
                  help="local name of the tileset directory under gfx/")
argsDict = vars(args.parse_args())

tileset_dirname = argsDict.get("tileset_dir", "")

tileset_pathname = tileset_dirname
if not tileset_dirname.startswith("gfx/"):
    tileset_pathname = "gfx/" + tileset_dirname

try:
    os.stat(tileset_pathname)
except KeyError:
    print("cannot find a directory {}".format(tileset_pathname))
    exit -1

pngnum = 1
all_ts_data = {}
pngname_to_pngnum = { "null_image": 0 }
pngnum_to_pngname = { 0: "null_image" }
all_subdirs = os.listdir(tileset_pathname)

for subdir in all_subdirs:
    if string.find(subdir, "pngs_") < 0:
        continue
    ts_name = subdir.split("pngs_")[1] + ".png"
    ts_path = tileset_pathname + "/" + ts_name       
    #print("tilesheet {}".format(ts_name))
    subdir_path = tileset_pathname + "/" + subdir
    tile_entries = []
    row_num = 0
    width = -1
    height = -1
    tmp_merged_pngs = []
    row_pngs = ["null_image"]

    for subdir_fpath, dirnames, filenames in os.walk(subdir_path):
        #print("{} has dirs {} and files {}".format(subdir_fpath, dirnames, filenames))
        for filename in filenames:
            filepath = subdir_fpath + "/" + filename
            if filename.endswith(".png"):
                pngname = filename.split(".png")[0]
                if pngname in pngname_to_pngnum or pngname == "no_entry":
                    continue
                row_pngs.append(filepath)
                if width < 0 or height < 0:
                    cmd = ["identify", "-format", "\"%G\"", filepath]
                    geometry_dim = subprocess.check_output(cmd)
                    width = int(geometry_dim.split("x")[0][1:])
                    height = int(geometry_dim.split("x")[1][:-1])

                pngname_to_pngnum[pngname] = pngnum
                pngnum_to_pngname[pngnum] = pngname
                pngnum += 1
                if len(row_pngs) > 15:
                    pngnum, merged = merge_pngs(subdir_path, row_pngs, row_num,
                                                pngnum, width, height)
                    row_num += 1
                    row_pngs = []
                    tmp_merged_pngs.append(merged)
            elif filename.endswith(".json"):
                with open(filepath, "r") as fp:
                    tile_entry = json.load(fp)
                    tile_entries.append(tile_entry)
    pngnum, merged = merge_pngs(subdir_path, row_pngs, row_num, pngnum, width, height)
    tmp_merged_pngs.append(merged)

    finalize_merges(ts_path, tmp_merged_pngs, width, height)

    all_ts_data[ts_name] = {
        "width": width,
        "height": height,
        "tile_entries": tile_entries
    }


#print("pngname to pngnum {}".format(json.dumps(pngname_to_pngnum, indent=2)))
#print("pngnum to pngname {}".format(json.dumps(pngnum_to_pngname, sort_keys=True, indent=2)))

tiles_new = []

for ts_name, ts_data in all_ts_data.items():
    ts_tile_entries = []
    for tile_entry in ts_data["tile_entries"]:
        converted_tile_entry = convert_pngname_to_pngnum(tile_entry, pngname_to_pngnum)
        ts_tile_entries.append(converted_tile_entry)
    ts_conf = {
        "file": ts_name,
        "tiles": ts_tile_entries
    }
    tiles_new.append(ts_conf)

tiles_new.append(FALLBACK)
conf_data = {
    "tiles-new": tiles_new
}
tileset_confpath = tileset_pathname + "/" + "test_tile_config.json"
write_to_json(tileset_confpath, conf_data)
