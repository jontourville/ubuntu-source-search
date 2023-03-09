#! /bin/bash

if [ $# -lt 2 -o "$1" == '-h' -o "$1" == '--help' ]; then
    echo "Usage: $(basename "$0") DIR [ GREP_OPTIONS ] PATTERN" > /dev/stderr
    echo > /dev/stderr
    echo "Recursively grep through all files in DIR and print the" > /dev/stderr
    echo "subdirectories that contain any matches" > /dev/stderr
    exit 1
fi

set -e

search_dir="$1"
shift

for package_dir in $search_dir/*; do
    name="$(basename "$package_dir")"
    if grep -rqs "$@" "$package_dir"; then
        echo "$name"
    fi
done
