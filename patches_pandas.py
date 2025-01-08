"""
Boilerplate script frame, so a tiny command-line script has
basic organization, arguments, etc.
"""

# import os
import sys
import argparse
import logging
from pathlib import Path
import pandas as pd


class App:
    def __init__(self, app_args):
        self.args = app_args
        self.patch_dir = "/Users/ed/Music/s1_patch_analysis"
        self.patch_files = []
        self.df = None  # Will be our DataFrame
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
        logging.info(f"Running {self.args.app_name}.")
        patch_file_properties = {}
        # Suck up all the properties from all the files
        for patch_file in self.patch_files:
            file_properties = self.get_properties(patch_file)
            patch_file_properties[patch_file.name] = pd.Series(file_properties)
        # Put it all in a DF for processing
        self.df = pd.DataFrame(patch_file_properties)
        # Sort the columns by file name, including the "default"
        self.df.sort_index(axis=1, inplace=True)
        # Dump to CSV
        self.df.to_csv("props.csv")
        pass

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


class Parameters:
    def __init__(self, app_args):
        self.df = None  # Will be our DataFrame

    def definition(self):
        pass


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
