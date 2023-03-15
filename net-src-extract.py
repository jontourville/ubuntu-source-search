#!/usr/bin/env python3

import os
import sys
import signal
import argparse
import collections
import urllib.request
import gzip
import tarfile
import tqdm
import hashlib

def get_args():
    mirror = "http://archive.ubuntu.com/ubuntu"
    parser = argparse.ArgumentParser()
    parser.add_argument("OUT_DIR", help="Directory to save downloaded archives")
    parser.add_argument("RELEASE", help="Ubuntu release codename (ex. jammy)")
    parser.add_argument("REPOSITORY", help="repository name (main, universe, multiverse, or restricted)")
    parser.add_argument("-n", "--no-extract", action="store_true", help="do not extract archives after downloading")
    parser.add_argument("-m", "--mirror", default=mirror, help="URL of mirror (defaults to %s)" % mirror)
    args = parser.parse_args()
    args.mirror = args.mirror.removesuffix("/")
    return args

SourceArchive = collections.namedtuple("SourceArchive", ["url", "filename", "size", "md5", "package"])

def size_to_str(size):
    if size < 1024:
        return "%d" % (size)
    elif size < 1024 * 1024:
        return "%.1fK" % (size / 1024.0)
    elif size < 1024 * 1024 * 1024:
        return "%.1fM" % (size / 1024.0 / 1024.0)
    elif size < 1024 * 1024 * 1024 * 1024:
        return "%.1fG" % (size / 1024.0 / 1024.0 / 1024.0)
    return "%.1fT" % (size / 1024.0 / 1024.0 / 1024.0 / 1024.0)

def get_archive_list(mirror, release, repo):
    sources_url = "%s/dists/%s/%s/source/Sources.gz" % (mirror, release, repo)
    sources = gzip.decompress(urllib.request.urlopen(sources_url).read()).decode().split("\n")

    archives = []
    package = ""
    directory = ""
    is_file_line = False
    for line in sources:
        if line.startswith("Package:"):
            package = line.split()[1]
            directory = ""
            is_file_line = False
            continue

        if line.startswith("Directory:"):
            directory = line.split()[1]

        if line.startswith("Files:"):
            is_file_line = True
            continue

        if not line.startswith(" "):
            is_file_line = False
            continue

        if not is_file_line:
            continue

        md5 = bytes.fromhex(line.split()[0])
        size = int(line.split()[1])
        filename = line.split()[2]
        exts = filename.split(".")

        if len(exts) > 1 and "tar" in exts and (exts[-1] == "tar" or exts[-2] == "tar"):
            url = "%s/%s/%s" % (mirror, directory, filename)
            archives.append(SourceArchive(url, filename, size, md5, package))

    return archives

def mkdir(d):
    try:
        os.mkdir(d)
    except FileExistsError:
        pass

def is_out_of_date(archive_path, md5):
    try:
        with open(archive_path, "rb") as f:
            local_md5 = hashlib.md5(f.read()).digest()
            if local_md5 == md5:
                return False
    except:
        return True

    return True

def get_outdated_archives(archives, out_dir):
    outdated_archives = []
    for archive in archives:
        if is_out_of_date(os.path.join(out_dir, archive.filename), archive.md5):
            outdated_archives.append(archive)

    return outdated_archives

def download_archives(archives, out_dir, no_extract):
    mkdir(out_dir)
    total_size = 0
    for archive in archives:
        total_size += archive.size

    print("Downloading:")
    pbar = tqdm.tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024, dynamic_ncols=True, disable=None)
    for archive in archives:
        filename = archive.url.split("/")[-1]
        archive_path = os.path.join(out_dir, filename)

        tqdm.tqdm.write("     %s..." % (filename))
        with open(archive_path, "wb") as f:
            f.write(urllib.request.urlopen(archive.url).read())

        if not no_extract:
            extract_dir = os.path.join(out_dir, archive.package)
            mkdir(extract_dir)
            with tarfile.open(archive_path, "r") as t:
                t.extractall(extract_dir)

        pbar.update(archive.size)

    pbar.close()

def prompt_to_continue(archives):
    if len(archives) == 0:
        print("All archives are up-to-date")
        return False

    total_size = 0
    for archive in archives:
        total_size += archive.size

    print("%d archives (%s) to download" % (len(archives), size_to_str(total_size)))
    resp = input("Do you want to continue? [y/N] ")
    if resp.lower() in ["y", "yes"]:
        return True

    return False

def cancel(sig=None, frame=None):
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cancel)
    args = get_args()

    archives = get_archive_list(args.mirror, args.RELEASE, args.REPOSITORY)
    outdated_archives = get_outdated_archives(archives, args.OUT_DIR)
    if prompt_to_continue(outdated_archives):
        download_archives(outdated_archives, args.OUT_DIR, args.no_extract)
    else:
        cancel()
