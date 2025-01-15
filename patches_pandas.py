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
from patch_parameters import PatchParameters as pp


class App:
    def __init__(self, app_args):
        self.args = app_args
        self.patch_dir = "/Users/ed/Music/s1_patch_analysis"
        self.patch_files: list[Path] = []
        self.values_df = pd.DataFrame()  # Raw values
        self.display_df = pd.DataFrame()  # Readable values
        self.param_attributes = (
            pd.DataFrame()
        )  # Full name, location on device, data type, default value
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

        # helper for getting descriptive names and blanking out defaults
        def display_value(value, param):
            default = self.param_attributes["DEFAULT"][param]
            if int(value) == int(default) and not self.args.default:
                return pd.NA
            return pp.get_display_value(param, value)

        # DF: rows = params, cols = files
        self.values_df = pd.DataFrame(
            {
                patch_file.name: pp.get_parameter_values_from_file(patch_file)
                for patch_file in self.patch_files
            }
        )
        # display_value = pp.get_display_value(prop, val)
        self.param_attributes = pd.DataFrame(pp.param_definitions).transpose()
        self.values_df.sort_index(axis=1, inplace=True)
        self.values_df.sort_index(axis=0, inplace=True)

        # Make cell values human-readable
        display_rows = {}
        for row in self.values_df.iterrows():
            display_rows[row[0]] = row[1].apply(display_value, args=(row[0],))
            self.display_df = pd.DataFrame(display_rows)

        # Human-readable defaults for CSV
        display_defaults = {}
        for param, default in self.param_attributes["DEFAULT"].items():
            display_defaults[param] = pp.get_display_value(param, default)
        display_defaults = pd.Series(display_defaults, name="DEFAULT")

        # Add in the parameter attributes
        # self.display_df = self.display_df.T
        self.display_df = pd.concat(
            [
                self.param_attributes["NAME"],
                self.param_attributes["LOCATION"],
                self.param_attributes["TYPE"],
                display_defaults,
                self.display_df.T,
            ],
            axis=1,
        )

        # Exclude unknown data types
        if not self.args.unknown:
            # self.display_df.drop(axis=0, labels=[x for x in param_attributes["TYPE"] if param_attributes["TYPE"][x] == 'UNK'], inplace=True)
            self.display_df.drop(
                self.display_df[self.display_df["TYPE"] == "UNK"].index, inplace=True
            )

        # Output
        self.dump()
        self.dump_to_csv()

    def dump_to_csv(self):
        csv_params = {}
        for patch_name, parameters in self.display_df.T.iterrows():
            display = {}
            for param, value in parameters.items():
                display[param] = value
            csv_params[patch_name] = pd.Series(display, name=param)
        csv_df = pd.DataFrame(csv_params)
        csv_df.drop("TYPE", axis=1, inplace=True)
        csv_df.to_csv(self.args.csvname, index=False)
        pass

    def dump(self):
        # for name, parameters in (i for i in self.df.items() if i[0] not in ["LOCATION", "DEFAULT"]):
        for patch_name, parameters in (
            i
            for i in self.display_df.T.iterrows()
            if i[0] not in ["LOCATION", "DEFAULT", "NAME", "TYPE"]
        ):
            print(f"\n----------------- {patch_name} ---------------")
            for p, v in parameters.items():
                if not pd.isna(v):
                    print(f'{self.param_attributes["NAME"][p]}: {v}')

    def cleanup(self):
        print(f"Cleaning up {self.args.app_name}.")


def parse_app_args(raw_args):
    parser = argparse.ArgumentParser(raw_args)
    parser.add_argument(
        "--unknown",
        "-u",
        help="Include params of unknown type",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--default",
        "-d",
        help="Include values that match default value",
        action="store_true",
        default=False,
    )
    parser.add_argument("--csvname", "-c", default="patches.csv")
    return parser.parse_args()


if __name__ == "__main__":
    parsed_args = parse_app_args(sys.argv[1:])
    parsed_args.app_name = Path(sys.argv[0]).name
    app = App(parsed_args)
    sys.exit(app.execute())
