#!/usr/bin/env python3

import os
import sys
import signal
import argparse
import gzip
import bz2
import lzma
import tarfile
import tqdm

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("ARCHIVE_DIR", help="Directory containing Ubuntu source archives")
    parser.add_argument("OUT_DIR", help="Directory to extract archives to")
    args = parser.parse_args()
    return args

def cancel(sig=None, frame=None):
        sys.exit(0)

def mkdir(d):
    try:
        os.mkdir(d)
    except FileExistsError:
        pass

def is_archive(filename):
    exts = filename.split(".")
    if len(exts) > 1 and "tar" in exts and (exts[-1] == "tar" or exts[-2] == "tar"):
        return True

    return False

def get_archives(archive_dir):
    archives = []
    with os.scandir(archive_dir) as it:
        for entry in it:
            if entry.is_file() and is_archive(entry.name):
                archives.append(os.path.join(archive_dir, entry.name))

    return sorted(archives)

def extract_archives(archives, out_dir):
    mkdir(out_dir)

    pbar = tqdm.tqdm(total=len(archives), unit="", dynamic_ncols=True, disable=None)
    for archive_path in archives:
        filename = os.path.basename(archive_path)
        package = filename.split("_")[0]
        extract_dir = os.path.join(out_dir, package)
        mkdir(extract_dir)
        with tarfile.open(archive_path, "r") as t:
            t.extractall(extract_dir)

        pbar.update(1)

    pbar.close()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cancel)
    args = get_args()

    archives = get_archives(args.ARCHIVE_DIR)
    extract_archives(archives, args.OUT_DIR)
