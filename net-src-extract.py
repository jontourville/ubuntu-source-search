#!/usr/bin/env python3

import collections
import urllib.request
import gzip

base_url = "http://archive.ubuntu.com"
release = "kinetic"
repo = "restricted"

SourceArchive = collections.namedtuple("SourceArchive", ["url", "size", "package"])

def get_source_urls(base_url, release, repo):
    sources_url = "%s/ubuntu/dists/%s/%s/source/Sources.gz" % (base_url, release, repo)
    sources = gzip.decompress(urllib.request.urlopen(sources_url).read()).decode().split("\n")

    package_urls = {}
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
        exts = filename.split(".")

        if len(exts) > 1 and "tar" in exts and (exts[-1] == "tar" or exts[-2] == "tar"):
            urls = package_urls.get(package, [])
            urls.append("%s/%s/%s" % (base_url, directory, filename))
            package_urls[package] = urls

    return package_urls

package_urls = get_source_urls(base_url, release, repo)
