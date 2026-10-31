"""Capture container artifacts through exec, including files on tmpfs.

Docker cp does not reliably read tmpfs on this Docker Desktop setup. Keep raw
binary transport out of PowerShell's text pipeline and validate extraction paths.
"""
import argparse
import subprocess
import tarfile
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument("container");p.add_argument("remote");p.add_argument("destination");a=p.parse_args()
    workspace=Path(__file__).resolve().parents[1]
    destination=Path(a.destination).resolve()
    if workspace not in destination.parents:raise ValueError("Capture must stay in this workspace")
    destination.mkdir(parents=True,exist_ok=True)
    remote=a.remote.rstrip("/")
    parent,leaf=remote.rsplit("/",1)
    archive=destination/"capture.tar"
    with archive.open("wb") as stream:
        subprocess.run(["docker","exec",a.container,"tar","cf","-","-C",parent or "/",leaf],stdout=stream,check=True)
    with tarfile.open(archive,"r:") as stream:
        for member in stream.getmembers():
            target=(destination/member.name).resolve()
            if destination not in target.parents or not (member.isfile() or member.isdir()):raise ValueError("Unsafe archive member")
        stream.extractall(destination)
    print(destination/leaf)


if __name__=="__main__":main()
