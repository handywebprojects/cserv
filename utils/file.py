###################################################

import json
import os
import stat
from traceback import print_exc as pe

###################################################

def create_dir(path, verbose = False):
    if not os.path.exists(path):
        os.makedirs(path)
        if verbose:
            print("created directory {}".format(path))
    else:
        if verbose:
            print("{} exists".format(path))

###################################################

def write_string_to_file(path, content):
    try:
        with open(path,"w") as outfile:
            outfile.write(content)
    except:
        print("could not write", path)

def read_string_from_file(path, default):
	try:
		content = open(path).read()
		return content
	except:
		return default

###################################################

def write_json_to_file(path, obj, indent = 2):    
    json.dump(obj, open(path, "w"), indent = indent)
    
def read_json_from_file(path, default):
    try:
        obj = json.load(open(path))
        return obj
    except:
        return default

###################################################

def os_stats_as_dict(stats, name, isdir):
    parts = name.split(".")
    ext = parts[-1]
    basename = name
    if len(parts) > 1:
        basename = ".".join(parts[:-1])
    return {
        "name": name,
        "basename": basename,
        "ext": ext,
        "isdir": isdir,
        "st_mode": stats.st_mode,
        "st_mode_unix_rwx": stat.filemode(stats.st_mode),
        "st_ino": stats.st_ino,
        "st_dev": stats.st_dev,
        "st_nlink": stats.st_nlink,
        "st_uid": stats.st_uid,
        "st_gid": stats.st_gid,
        "st_size": stats.st_size,
        "st_atime": stats.st_atime,
        "st_mtime": stats.st_mtime,
        "st_ctime": stats.st_ctime
    }

def dir_listing_as_list(path):
    try:
        listing = []
        for name in os.listdir(path):            
            currpath = os.path.join(path, name)
            stats = os.stat(currpath)
            isdir = os.path.isdir(currpath)
            listing.append(os_stats_as_dict(stats, name, isdir))
        return listing
    except:
        pe()
        return []

def dir_listing_as_dict(path):
    listing = dir_listing_as_list(path)
    dictionary = {}
    for item in listing:
        dictionary[item["name"]] = item
    return dictionary

def getlastmod(path):
    try:
        stats = os.stat(path)
        mtime = stats.st_mtime
        return mtime
    except:
        return 0

###################################################