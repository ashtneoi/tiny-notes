#!/usr/bin/env python3


import os

from bakery import render_path


def regen(tmpl_path):
    html_path = tmpl_path[:tmpl_path.rfind(".")] + ".html"
    print("Regenerating " + html_path)
    s = render_path(tmpl_path)
    with open(html_path, "w") as f:
        f.write(s)


def regen_dir(path):
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            regen_dir(entry.path)
        elif (
                entry.is_file(follow_symlinks=False)
                and entry.name.endswith(".htms")
        ):
            regen(entry.path)


regen_dir(".")
