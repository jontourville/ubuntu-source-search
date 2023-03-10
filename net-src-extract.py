#!/usr/bin/env python3

import sys
import argparse
import collections
import urllib.request
import gzip

def get_args():
    mirror = "http://archive.ubuntu.com"
    parser = argparse.ArgumentParser()
    parser.add_argument("RELEASE", help='Ubuntu release codename (ex. jammy)')
    parser.add_argument("REPOSITORY", help='repository name (main, universe, multiverse, or restricted)')
    parser.add_argument("-m", "--mirror", default=mirror, help="URL of mirror (defaults to %s)" % mirror)
    return parser.parse_args()

SourceArchive = collections.namedtuple("SourceArchive", ["url", "size", "package"])

def get_archive_list(mirror, release, repo):
    sources_url = "%s/ubuntu/dists/%s/%s/source/Sources.gz" % (mirror, release, repo)
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

        filename = line.split()[2]
        size = int(line.split()[1])
        exts = filename.split(".")

        if len(exts) > 1 and "tar" in exts and (exts[-1] == "tar" or exts[-2] == "tar"):
            url = "%s/ubuntu/%s/%s" % (mirror, directory, filename)
            archives.append(SourceArchive(url, size, package))

    return archives

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

if __name__ == "__main__":
    args = get_args()

    archives = get_archive_list(args.mirror, args.RELEASE, "main")

    total_size = 0
    for archive in archives:
        total_size += archive.size

    print("Number of archives: %d" % (len(archives)))
    print("Compressed size:    %s" % (size_to_str(total_size)))
