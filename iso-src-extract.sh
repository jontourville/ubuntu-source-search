#! /bin/bash

if [ $# -lt 2 -o "$1" == '-h' -o "$1" == '--help' ]; then
    echo "Usage: $(basename "$0") OUT_DIR ISO_PATH" > /dev/stderr
    echo > /dev/stderr
    echo "Extract all source archives from an Ubuntu source ISO" > /dev/stderr
    exit 1
fi

set -e

mnt_dir="$(mktemp -dt iso.XXX)"

function cleanup {
    sudo umount "$mnt_dir"
    rmdir $mnt_dir
}

trap cleanup EXIT

out_dir="$1"
iso_path="$2"
uid=$(id -u)
gid=$(id -g)

echo "Mounting \`$iso_path' at \`$mnt_dir'..."
sudo mount -o ro,uid=$uid,gid=$gid "$iso_path" "$mnt_dir"
if [ ! -d "$mnt_dir/pool" ]; then
    echo "Error: \`$iso_path' is not a source ISO" > /dev/stderr
    exit 1
fi

prev_dir="$PWD"
mkdir -p "$out_dir"
cd "$out_dir"

archive_paths="$(find "$mnt_dir/pool" -type f | grep '\.tar\($\|\.[^.]*$\)')"
for p in $archive_paths; do
    name="$(basename "$(dirname "$p")")"
    mkdir -p "$name"
    cd "$name"
    echo "Extracting \`$p'..."
    tar -xaf "$p"
    cd ..
done

cd "$prev_dir"
