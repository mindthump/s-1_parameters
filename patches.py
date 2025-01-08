"""
Boilerplate script frame, so a tiny command-line script has
basic organization, arguments, etc.
"""

# import os
import sys
import argparse
import logging
from pathlib import Path
from collections import defaultdict
import csv


class App:
    def __init__(self, app_args):
        self.args = app_args
        self.patch_dir = "/Users/ed/Music/s1_patch_analysis"
        self.patch_files = []
        self.patch_file_properties = list()
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(message)s",
            filename="app.log",
            filemode="w",
        )
        # logging.debug('A debug message')

    def execute(self):
        print("Executing.")
        self.prepare()
        self.run()
        self.cleanup()
        return 0

    def prepare(self):
        print(f"Preparing {self.args.app_name}.")
        self.patch_files = [
            patch_file
            for patch_file in Path(self.patch_dir).iterdir()
            if patch_file.is_file() and not patch_file.name.startswith(".")
        ]

    def run(self):
        # PRIMARY CODE GOES HERE
        logging.info(f"Running {self.args.app_name}.")
        property_names = set()
        for patch_file in self.patch_files:
            # set to remove duplicates
            # open the file and suck up the properties
            file_properties = self.get_properties(patch_file)
            file_properties["FILENAME"] = patch_file.name
            for prop_name in file_properties.keys():
                property_names.add(prop_name)
            # We don't know *all* the property names until we've read all the files.
            self.patch_file_properties.append(file_properties)
        with open("props.csv", "w") as csvfile:
            prop_writer = csv.DictWriter(csvfile, fieldnames=property_names)
            prop_writer.writeheader()
            prop_writer.writerows(self.patch_file_properties)

    def cleanup(self):
        print(f"Cleaning up {self.args.app_name}.")

    def get_properties(self, filepath):
        properties = {}
        if filepath != "":
            prop_file = open(filepath, "r")
            lines = prop_file.read().split("\n")

            for ln in (f for f in lines if f):
                if not ln.startswith("STEP_"):
                    eqind = ln.index("=")
                    prop = ln[:eqind]
                    prop = prop.strip()
                    val = ln[eqind + 1 :]
                    val = val.strip()
                    properties[prop] = val
        return properties


def parse_app_args(raw_args):
    parser = argparse.ArgumentParser(raw_args)
    # parser.add_argument("positional")
    # parser.add_argument("--optional_value", "-o")
    # parser.add_argument("--flag", "-f", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_app_args(sys.argv[1:])
    parsed_args.app_name = Path(sys.argv[0]).name
    app = App(parsed_args)
    sys.exit(app.execute())
