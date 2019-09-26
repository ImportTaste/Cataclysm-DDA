#!/bin/python

# decompose.py
# Split a gfx tile_config.json into 1000s of little directories, each with their own config
# file and tile image.

import argparse
import copy
import json
import os
import subprocess


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


def check_for_expansion(tile_entry, expansions):
    if tile_entry.get("fg", -10) == 0:
        expansions.append(tile_entry)
        return True
    return False


def parse_id(tile_entry):
    all_tile_ids = []
    read_tile_ids = tile_entry.get("id")
    if isinstance(read_tile_ids, list):
        for tile_id in read_tile_ids:
            if tile_id and tile_id not in all_tile_ids:
                all_tile_ids.append(tile_id)
    elif read_tile_ids and read_tile_ids not in all_tile_ids:
        all_tile_ids.append(read_tile_ids)
    # print("tile {}".format(all_tile_ids[0]))
    if not all_tile_ids:
        return None, None
    return all_tile_ids[0], all_tile_ids


def parse_png(tile_entry, background_pngnums):
    all_pngnums = []
    read_pngnums = tile_entry.get("fg", -10)
    if isinstance(read_pngnums, list):
        for pngnum in read_pngnums:
            if isinstance(pngnum, dict):
                sprite_ids = pngnum.get("sprite", -10)
                if isinstance(sprite_ids, list):
                    for sprite_id in sprite_ids:
                        if sprite_id >= 0 and sprite_id not in all_pngnums:
                            all_pngnums.append(sprite_id)
                else:
                    if sprite_ids >= 0 and sprite_ids not in all_pngnums:
                        all_pngnums.append(sprite_ids)
            else:
                if pngnum >= 0 and pngnum not in all_pngnums:
                    all_pngnums.append(pngnum)
    elif read_pngnums >= 0 and read_pngnums not in all_pngnums:
        all_pngnums.append(read_pngnums)
    bg_id = tile_entry.get("bg", -10)
    if bg_id >= 0 and bg_id not in all_pngnums:
        all_pngnums.append(bg_id)
    if bg_id >= 0 and bg_id not in background_pngnums:
        background_pngnums.append(bg_id)

    add_tile_entrys = tile_entry.get("additional_tiles", [])
    for add_tile_entry in add_tile_entrys:
        add_pngnums = parse_png(add_tile_entry, background_pngnums)
        for add_pngnum in add_pngnums:
            if add_pngnum not in all_pngnums:
                all_pngnums.append(add_pngnum)
    # print("\tpngs: {}".format(all_pngnums))
    return all_pngnums


def convert_pngnum_to_pngname(tile_entry, pngnum_to_pngname):
    new_fg = []
    new_id = ""
    read_pngnums = tile_entry.get("fg", -10)
    if isinstance(read_pngnums, list):
        for pngnum in read_pngnums:
            if isinstance(pngnum, dict):
                sprite_ids = pngnum.get("sprite", -10)
                if isinstance(sprite_ids, list):
                    new_sprites = []
                    for sprite_id in sprite_ids:
                        if sprite_id >= 0:
                            if not new_id:
                                new_id = pngnum_to_pngname[sprite_id]
                            new_sprites.append(pngnum_to_pngname[sprite_id])
                    pngnum["sprite"] = new_sprites
                else:
                    if sprite_ids >= 0:
                        if not new_id:
                            new_id = pngnum_to_pngname[sprite_ids]
                        pngnum["sprite"] = pngnum_to_pngname[sprite_ids]
                new_fg.append(pngnum)
            else:
                if not new_id:
                    new_id = pngnum_to_pngname[pngnum]
                new_fg.append(pngnum_to_pngname[pngnum])
    elif read_pngnums >= 0:
        if not new_id:
            new_id = pngnum_to_pngname[read_pngnums]
        new_fg.append(pngnum_to_pngname[read_pngnums])
    bg_id = tile_entry.get("bg", -10)
    if bg_id >= 0:
        tile_entry["bg"] = pngnum_to_pngname[bg_id]
    add_tile_entrys = tile_entry.get("additional_tiles", [])
    for add_tile_entry in add_tile_entrys:
        convert_pngnum_to_pngname(add_tile_entry, pngnum_to_pngname)
    if not new_fg:
        new_fg.append("no_entry")
        new_id = "no_entry"
    tile_entry["fg"] = new_fg
    return new_id, tile_entry


def extract_image(pngname, first_file_index, geometry_dim, offset_x, offset_y, subdir_pathname,
                  extracted_pngnums):
    png_index = pngname_to_pngnum[pngname]
    if not png_index or extracted_pngnums.get(png_index):
        return
    file_index = png_index - first_file_index
    y_index = file_index / 16
    x_index = file_index - y_index * 16
    file_off_x = png_width * x_index + offset_x
    file_off_y = png_height * y_index + offset_y
    geometry_offset = "+{}+{}".format(file_off_x, file_off_y)
    tile_png_pathname = subdir_pathname + "/" + pngname + ".png"
    cmd = ["convert", tilesheet_pathname, "-crop", geometry_dim + geometry_offset,
           tile_png_pathname]
    #debug statement for convert call
    #print("for {}, trying {}".format(png_index, cmd))
    failure = subprocess.check_output(cmd)
    if failure:
       print("failed to extract tile_entry_name {}".format(failure))
    else:
       extracted_pngnums[png_index] = True


class Dir_Info(object):
    def __init__(self, ts_dir_pathname):
        self.tilenum_in_dir = 256
        self.dir_count = 0
        self.subdir_pathname = ""
        self.ts_dir_pathname = ts_dir_pathname

    def increment(self):
        if self.tilenum_in_dir > 255:
            self.subdir_pathname = self.ts_dir_pathname + "/" + "images{}".format(self.dir_count)
            find_or_make_dir(self.subdir_pathname)
            self.tilenum_in_dir = 0
            self.dir_count += 1
        else:
            self.tilenum_in_dir += 1
        return self.subdir_pathname


args = argparse.ArgumentParser(description="Split a tileset's tile_config.json into a directory per tile containing the tile data and png.")
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

tileset_confname = tileset_pathname + "/" + "tile_config.json"

try:
    os.stat(tileset_confname)
except KeyError:
    print("cannot find a directory {}".format(tileset_confname))
    exit -1

with open(tileset_confname) as conf_file:
    all_tiles = json.load(conf_file)


# dict of png absolute numbers to png names
pngnum_to_pngname = {}
# dict of pngnames to png numbers; used to control uniqueness
pngname_to_pngnum = {}
# dict of tilesheet png filenames to tilesheet data
tilesheet_to_data = {}
# dict of tilesheet filenames to arbitrary tile_ids to tile_entries
file_tile_id_to_tile_entrys = {}
# dict of background png_nums
background_pngnums = []

all_tilesheet_data = all_tiles.get("tiles-new", [])
default_height = 0
default_width = 0
tile_info = all_tiles.get("tile_info", {})
if tile_info:
    default_height = tile_info[0].get("height")
    default_width = tile_info[0].get("width")

for tilesheet_data in all_tilesheet_data:
    ts_filename = tilesheet_data.get("file", "")
    tile_id_to_tile_entrys = {}
    pngnum_min = 10000000
    pngnum_max = 0
    file_height = tilesheet_data.get("sprite_height", default_height)
    file_width = tilesheet_data.get("sprite_width", default_width)
    file_offset_x = tilesheet_data.get("sprite_offset_x", 0)
    file_offset_y = tilesheet_data.get("sprite_offset_y", 0)
    expansions = []

    all_tile_entry = tilesheet_data.get("tiles", [])
    for tile_entry in all_tile_entry:
        if check_for_expansion(tile_entry, expansions):
            continue
        tile_id, all_tile_ids = parse_id(tile_entry)
        if not tile_id:
            continue
        all_pngnums = parse_png(tile_entry, background_pngnums)
        offset = 0
        for i in range(0, len(all_pngnums)):
            pngnum = all_pngnums[i]
            pngname = "{}_{}".format(tile_id, i + offset)
            while pngname in pngname_to_pngnum:
                offset += 1
                pngname = "{}_{}".format(tile_id, i + offset)
            pngnum_to_pngname.setdefault(pngnum, pngname)
            if pngnum_to_pngname[pngnum] == pngname:
                pngname_to_pngnum.setdefault(pngname, pngnum)
            if pngnum > 0 and pngnum not in background_pngnums:
                pngnum_max = max(pngnum_max, pngnum)
                pngnum_min = min(pngnum_min, pngnum)
        tile_id_to_tile_entrys.setdefault(tile_id, [])
        tile_id_to_tile_entrys[tile_id].append(tile_entry) 
    #debug statement to verify pngnum_min and pngnum_max
    #print("{} from {} to {}".format(ts_filename, pngnum_min, pngnum_max))
    if pngnum_max > 0:
        pngnum_min = 16 * (pngnum_min / 16)
        tilesheet_to_data[ts_filename] = {
            "min": pngnum_min,
            "max": pngnum_max,
            "height": file_height,
            "width": file_width,
            "off_x": file_offset_x,
            "off_y": file_offset_y,
            "expansions": expansions
        }
        #debug statement to verify final tilesheet data
        #print("{}: {}".format(ts_filename, json.dumps(tilesheet_to_data[ts_filename], indent=2)))
    file_tile_id_to_tile_entrys[ts_filename] = tile_id_to_tile_entrys

#debug statements to verify pngnum_to_pngname and pngname_to_pngnum
#print("pngnum_to_pngname: {}".format(json.dumps(pngnum_to_pngname, sort_keys=True, indent=2)))
#print("pngname_to_pngnum: {}".format(json.dumps(pngname_to_pngnum, sort_keys=True, indent=2)))

extracted_pngnums = {}

for ts_filename, tile_id_to_tile_entrys in file_tile_id_to_tile_entrys.items():
    tilenum_in_dir = 256
    dir_count = 0
    tilesheet_data = tilesheet_to_data.get(ts_filename,{})
    png_height = tilesheet_data.get("height")
    png_width = tilesheet_data.get("width")
    geometry_dim = "{}x{}".format(png_width, png_height) 
    first_file_index = tilesheet_data.get("min", 0)
    final_file_index = tilesheet_data.get("max", 0)
    index_range = final_file_index - first_file_index
    offset_x = tilesheet_data.get("offset_x", 0)
    offset_y = tilesheet_data.get("offset_y", 0)
    expansions = tilesheet_data.get("expansions", [])

    if not png_height or not png_width:
        continue

    ts_base = ts_filename.split(".png")[0]
    tilesheet_pathname = tileset_pathname + "/" + ts_filename
    tilesheet_dir_pathname = tileset_pathname + "/pngs_" +  ts_base + "_{}".format(geometry_dim) 
    find_or_make_dir(tilesheet_dir_pathname)
    dir_info = Dir_Info(tilesheet_dir_pathname)

    for expand_entry in expansions:
        expand_entry_filename = "/" + expand_entry.get("id","expansion") + ".json"
        expand_entry_pathname = tilesheet_dir_pathname + "/" + expand_entry_filename
        write_to_json(expand_entry_pathname, expand_entry)

    for tile_id, tile_entrys in tile_id_to_tile_entrys.items():
        subdir_pathname = dir_info.increment()

        for tile_entry in tile_entrys:
            tile_entry_name, tile_entry = convert_pngnum_to_pngname(tile_entry, pngnum_to_pngname)
            if tile_entry_name and tile_entry_name != "no_entry":
                extract_image(tile_entry_name, first_file_index, geometry_dim, offset_x, offset_y, subdir_pathname, extracted_pngnums)
                tile_entry_pathname = subdir_pathname + "/" + tile_entry_name + ".json"
                write_to_json(tile_entry_pathname, tile_entry)
    for pngnum in range(first_file_index, final_file_index):
        if pngnum in pngnum_to_pngname and not extracted_pngnums.get(pngnum):
            subdir_pathname = dir_info.increment()
            extract_image(pngnum_to_pngname[pngnum], first_file_index, geometry_dim, offset_x, offset_y, subdir_pathname, extracted_pngnums)

for pngnum in pngnum_to_pngname:
    if not extracted_pngnums.get(pngnum):
        print("missing index {}, {}".format(pngnum, pngnum_to_pngname[pngnum]))
