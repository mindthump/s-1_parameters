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
from patch_parameters import PatchParameters


class App:
    def __init__(self, app_args):
        self.args = app_args
        self.patch_dir = "/Users/ed/Music/s1_patch_analysis"
        self.patch_files: list[Path] = []
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
        # Suck up all the properties from all the file
        for patch_file in self.patch_files:
            file_parameters = PatchParameters(patch_file)
            patch_file_properties[patch_file.name] = pd.Series(file_parameters.properties)
        # Put it all in a DF for processing
        self.df = pd.DataFrame(patch_file_properties)
        # Sort the columns by file name, including the "default"
        self.df.sort_index(axis=1, inplace=True)
        self.df.sort_index(axis=0, inplace=True)
        self.dump_changed()
        # Dump to CSV
        csv_params = {}
        for k, v in self.df.items():
            display = {}
            for pv in v:
                if pv["CHANGED"]:
                    display[pv["DISPLAY_NAME"]] = pv["DISPLAY_VALUE"]
            csv_params[k] = pd.Series(display, name=k)
        display_df = pd.DataFrame(csv_params)
        display_df.sort_index(axis=0, inplace=True)
        display_df.sort_index(axis=1, inplace=True)
        display_df.to_csv("display.csv")
        # self.df.to_csv("props.csv")
        pass

    def dump(self):
        for name, parameters in self.df.items():
            print(f"\n----------------- {name} ---------------")
            for p, v in parameters.items():
                print(p, v["DISPLAY_VALUE"])

    def dump_changed(self):
        for name, parameters in self.df.items():
            print(f"\n----------------- {name} ---------------")
            for p, v in parameters.items():
                if v["CHANGED"]:
                 print(f"{v['DISPLAY_NAME']}: {v['DISPLAY_VALUE']}")

    def cleanup(self):
        print(f"Cleaning up {self.args.app_name}.")


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
