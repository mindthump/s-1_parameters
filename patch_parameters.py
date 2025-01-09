import logging
import math
from pathlib import Path
import pandas
import re


class PatchParameters:
    def __init__(self, patch_file: Path):
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(message)s",
            filename="app.log",
            filemode="w",
        )
        self.properties = self.get_properties_from_file(patch_file)

    def get_properties_from_file(self, filepath):
        properties = {}
        prop: str = ""
        val: str = ""
        changed: bool = False
        display_value: str = ""
        display_name: str = ""
        prop_file = open(filepath, "r")
        lines = prop_file.read().split("\n")
        for ln in (f for f in lines if f):
            # TODO: step sequence
            if not ln.startswith("STEP_"):
                eqind = ln.index("=")
                prop = ln[:eqind]
                prop = prop.strip()
                val = ln[eqind + 1 :]
                val = val.strip()
                changed, display_value, display_name = self.parse_parameters(prop, val)
            properties[prop] = {
                "VALUE": val,
                "CHANGED": changed,
                "DISPLAY_VALUE": display_value,
                "DISPLAY_NAME": display_name
            }
        return properties

    def parse_parameters(self, prop_key, prop_value):
        # Depends on the property values all being integers. This is true for now, but subject to change.
        prop_def = self.param_definitions[prop_key]
        display_value = ""
        changed = int(prop_value) != int(prop_def["DEFAULT"])
        display_name = prop_def["NAME"]
        match prop_def["TYPE"]:
            case "INT":
                display_value = prop_value
            case "DICT":
                try:
                    display_value = prop_def["VALUES"][
                        prop_value
                    ]
                except:
                    display_value = prop_value
            case "DIV100":
                display_value = int(prop_value) / 100
            case "SPLIT_TC":
                display_value = self.integer_to_twos_complement(int(prop_value))
            case "CHOP":
                display_value = self.chop_pattern(int(prop_value))
            case "COMB":
                display_value = math.ceil((int(prop_value) / 8) * 10) / 10
            case _:
                display_value = f"Type: {prop_def["TYPE"]} Value: {prop_value}"
        return changed, display_value, display_name

    def chop_pattern(self, pattern):
        binary_str = format(pattern, "b")
        padded_binary_str = binary_str.zfill(16)
        reversed = padded_binary_str[::-1]
        diagram = re.sub("1", "◼", re.sub("0", "◻︎︎", reversed))
        return diagram

    def integer_to_twos_complement(self, integer):
        # Convert the integer to a binary string and remove the '0b' prefix
        binary_str = format(integer, "b")

        # Pad the binary string with leading zeros to ensure it's at least 16 characters long
        padded_binary_str = binary_str.zfill(16)

        # Split the padded binary string into two 8-character substrings
        first_half = padded_binary_str[:8]
        second_half = padded_binary_str[8:]

        # Define a helper function to convert an 8-bit binary to two's complement decimal
        def binary_to_twos_complement(bin_str):
            # Consider the binary to be negative if it starts with '1'
            if bin_str[0] == "1":
                # Convert into a decimal integer by inverting bits and adding 1 (two's complement)
                return -((int(bin_str, 2) ^ 0xFF) + 1)
            else:
                # Simply convert to a decimal integer
                return int(bin_str, 2)

        # Convert both halves to their two's complement decimal form
        # The two values are switched in the S-1 e.g., (button2, button1), (button 4, button3)
        first_decimal = binary_to_twos_complement(second_half)
        second_decimal = binary_to_twos_complement(first_half)

        return first_decimal, second_decimal

    # The two values are switched in the S-1 e.g., (button2, button1), (button 4, button3)
    def twos_complement_to_integer(second_decimal, first_decimal):
        # Define a helper function to convert a signed decimal to an 8-bit binary string
        def twos_complement_to_binary_string(value):
            if value < 0:
                # Calculate the two's complement 8-bit representation of the negative number
                value = (abs(value) ^ 0xFF) + 1
            # Convert to binary and extract the last 8 bits (8 characters)
            return format(value & 0xFF, "08b")

        # Convert both integers to 8-bit binary strings
        first_half = twos_complement_to_binary_string(first_decimal)
        second_half = twos_complement_to_binary_string(second_decimal)

        # Concatenate the two binary strings to form a 16-bit binary string
        combined_binary = first_half + second_half

        # Convert the 16-bit binary string to an integer
        result_integer = int(combined_binary, 2)

        return result_integer

    param_definitions = {
        "LENG": {
            "NAME": "Pattern Length/Last",
            "TYPE": "INT",
            "RANGE": (1, 64),
            "DEFAULT": 16,
        },
        "SCALE": {
            "NAME": "Pattern Scale (Step Length)",
            "TYPE": "DICT",
            "VALUES": {
                "0": "1_8",
                "1": "1_16",
                "2": "1_32",
                "3": "8t",
                "4": "16t",
                "5": "32t",
            },
            "DEFAULT": "1",
        },
        "TRANSPOSE": {
            "NAME": "Key Transpose",
            "TYPE": "INT",
            "RANGE": (-60, 60),
            "DEFAULT": 0,
        },
        "LEVEL": {
            "NAME": "Overall Volume",
            "TYPE": "INT",
            "RANGE": (0, 127),
            "DEFAULT": 70,
        },
        # Tempo is multiplied by 100
        "TEMPO": {
            "NAME": "Tempo",
            "TYPE": "DIV100",
            "RANGE": (400, 30000),
            "DEFAULT": 10000,
        },
        "SHUFFLE": {"NAME": "Shuffle", "TYPE": "INT", "RANGE": (-90, 90), "DEFAULT": 0},
        "ARP_TYPE": {
            "NAME": "Arp Type",
            "TYPE": "DICT",
            "VALUES": {
                "0": "OFF",
                "1": "Up",
                "2": "Down",
                "3": "Up/Down",
                "4": "Up 2",
                "5": "Down 2",
                "6": "Up/Down 2",
                "7": "Random",
                "8": "Random 2",
            },
            "DEFAULT": "0",
        },
        "ARP_RATE": {
            "NAME": "Arp Rate",
            "TYPE": "DICT",
            "VALUES": {
                "0": "1_4",
                "1": "1_8",
                "2": "1_16",
                "3": "1_32",
                "4": "8t",
                "5": "16t",
                "6": "32t",
            },
            "DEFAULT": "2",
        },
        "MOTION_CC1": {"NAME": "Motion Control 1", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC2": {"NAME": "Motion Control 2", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC3": {"NAME": "Motion Control 3", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC4": {"NAME": "Motion Control 4", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC5": {"NAME": "Motion Control 5", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC6": {"NAME": "Motion Control 6", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC7": {"NAME": "Motion Control 7", "TYPE": "UNK", "DEFAULT": "-1"},
        "MOTION_CC8": {"NAME": "Motion Control 8", "TYPE": "UNK", "DEFAULT": "-1"},
        # This depends on LFO_SYNC. How do we represent a RANGE vs a DICT?
        "LFO_RATE": {
            "NAME": "LFO Rate",
            "TYPE": "DICT",
            "VALUES": {
                "0": "8_1",
                "1": "6_1",
                "2": "8_1t",
                "3": "4_1",
                "4": "3_1",
                "5": "4_1t",
                "6": "2_1",
                "7": "1d",
                "8": "2_1t",
                "9": "1_1",
                "10": "2d",
                "11": "1t",
                "12": "1_2",
                "13": "4d",
                "14": "2t",
                "15": "1_4",
                "16": "8d",
                "17": "4t",
                "18": "1_8",
                "19": "16d",
                "20": "8t",
                "21": "1_16",
                "22": "32d",
                "23": "16t",
                "24": "1_32",
                "25": "64d",
                "26": "32t",
                "27": "1_64",
                "28": "128d",
                "29": "64t",
                "30": "128",
            },
            "DEFAULT": 120,
        },
        "LFO_WAVE_FORM": {
            "NAME": "LFO Waveform",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Rising Saw",
                "1": "Descending Saw",
                "2": "Triangle",
                "3": "Square",
                "4": "Random ",
                "5": "Noise",
            },
            "DEFAULT": "2",
        },
        "VCO_MOD_DEPTH": {
            "NAME": "Oscillator LFO",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },  # Depends on PWM Source
        "VCO_RANGE": {
            "NAME": "Oscillator Octave",
            "TYPE": "DICT",
            "VALUES": {
                "0": "64'",
                "1": "32'",
                "2": "16'",
                "3": "8'",
                "4": "4'",
                "5": "2'",
            },
            "DEFAULT": "2",
        },
        "VCO_PULSE_WIDTH": {
            "NAME": "Oscillator Pulse Width",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },
        "VCO_PWM_SOURCE": {
            "NAME": "Oscillator PWM Source",
            "TYPE": "DICT",
            "VALUES": {"0": "Envelope", "1": "Manual", "2": "LFO"},
            "DEFAULT": "2",
        },
        "VCO_PWM_LEVEL": {
            "NAME": "Oscillator PWM Level",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 255,
        },
        "VCO_SAW_LEVEL": {
            "NAME": "Oscillator Saw Level",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCO_SUB_LEVEL": {
            "NAME": "Oscillator Sub Level",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCO_SUB_TYPE": {
            "NAME": "Oscillator Sub Octave",
            "TYPE": "DICT",
            "VALUES": {"0": "-2(A)", "1": "-2(S)", "2": "-1"},
            "DEFAULT": "2",
        },
        "VCO_NOISE_LEVEL": {
            "NAME": "Oscillator Noise Level",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCF_CUTOFF": {
            "NAME": "Filter Cutoff",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "255",
        },
        "VCF_RESONANCE": {
            "NAME": "Filter Resonance",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCF_ENV_DEPTH": {
            "NAME": "Filter Envelope Depth",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCF_MOD_DEPTH": {
            "NAME": "Filter LFO Depth",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCF_KEY_FOLLOW": {
            "NAME": "Filter Keyboard Follow",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 0,
        },
        "VCA_ENV_MODE": {
            "NAME": "Filter Envelope Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "Gate", "1": "Envelope"},
            "DEFAULT": "1",
        },
        "ENV_TRG_MODE": {
            "NAME": "Envelope Trigger Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "LFO", "1": "Gate", "2": "Trigger"},
            "DEFAULT": "2",
        },
        "ENV_ATTACK": {
            "NAME": "Envelope Attack",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },
        "ENV_DECAY": {
            "NAME": "Envelope Decay",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "84",
        },
        "ENV_SUSTAIN": {
            "NAME": "Envelope Sustain",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "51",
        },
        "ENV_RELEASE": {
            "NAME": "Envelope Release",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "42",
        },
        "ASSIGN_MODE": {"NAME": "Assign Mode", "TYPE": "UNK", "DEFAULT": "2"},  # ???
        "CHORD_VOICE2_SW": {
            "NAME": "Chord Voice 2 Switch",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "1",
        },
        "CHORD_VOICE3_SW": {
            "NAME": "Chord Voice 3 Switch",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "1",
        },
        "CHORD_VOICE4_SW": {
            "NAME": "Chord Voice 4 Switch",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "1",
        },
        "CHORD_VOICE2_KEY_SHIFT": {
            "NAME": "Chord Voice 2 Shift",
            "TYPE": "INT",
            "RANGE": (-12, 12),
            "DEFAULT": "12",
        },
        "CHORD_VOICE3_KEY_SHIFT": {
            "NAME": "Chord Voice 3 Shift",
            "TYPE": "INT",
            "RANGE": (-12, 12),
            "DEFAULT": "7",
        },
        "CHORD_VOICE4_KEY_SHIFT": {
            "NAME": "Chord Voice 4 Shift",
            "TYPE": "INT",
            "RANGE": (-12, 12),
            "DEFAULT": "5",
        },
        "VCO_BEND_SENS": {
            "NAME": "Oscillator Bend Sensitivity",
            "TYPE": "INT",
            "RANGE": (0, 240),
            "DEFAULT": "20",
        },
        "VCF_BEND_SENS": {
            "NAME": "Filter Bend Sensitivity",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },
        "LFO_MOD_DEPTH": {
            "NAME": "LFO Modulation Depth",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "30",
        },
        "PORTAMENTO_MODE": {
            "NAME": "Portamento Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On", "2": "Auto"},
            "DEFAULT": "0",
        },
        "PORTAMENTO_TIME": {
            "NAME": "Portamento Time",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "30",
        },
        "NOISE_MODE": {
            "NAME": "Noise Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "Pink", "1": "White"},
            "DEFAULT": "0",
        },
        "LFO_MODE": {
            "NAME": "LFO Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "Normal", "1": "Fast"},
            "DEFAULT": "0",
        },
        # Fine Tune shows as -1.0 to 1.0 in display?
        "FINE_TUNE": {
            "NAME": "Oscillator Range Fine Tune",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "128",
        },
        "TEMPO_SYNC": {
            "NAME": "Delay Sync",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "1",
        },
        "CHORUS": {
            "NAME": "Chorus",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Off",
                "1": "Standard (1)",
                "2": "Faster (2)",
                "3": "Rotary (3)",
                "4": "Relaxed (4)",
            },
            "DEFAULT": "0",
        },
        "DELAY_LEVEL": {
            "NAME": "Delay Volume",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },
        "DELAY_TIME": {
            "NAME": "Delay Time",
            "TYPE": "INT",
            "RANGE": (1, 740),
            "DEFAULT": "174",
        },
        "DELAY_TEMPO": {
            "NAME": "Delay Tempo",
            "TYPE": "DICT",
            "VALUES": {
                "0": "128",
                "1": "64t",
                "2": "128d",
                "3": "1_64",
                "4": "32t",
                "5": "64d",
                "6": "1_32",
                "7": "16t",
                "8": "32d",
                "9": "1_16",
                "10": "8t",
                "11": "16d",
                "12": "1_8",
                "13": "4t",
                "14": "8d",
                "15": "1_4",
            },
            "DEFAULT": "14",
        },
        "DELAY_FEEDBACK": {
            "NAME": "Delay Feedback",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "136",
        },  # What's the value? Not 1:1 ?
        "DELAY_LOW_CUT": {
            "NAME": "Delay Low-Cut Filter",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Flat",
                "1": "20",
                "2": "25",
                "3": "31.5",
                "4": "40",
                "5": "50",
                "6": "63",
                "7": "80",
                "8": "100",
                "9": "125",
                "10": "160",
                "11": "200",
                "12": "250",
                "13": "315",
                "14": "400",
                "15": "500",
                "16": "630",
                "17": "800",
            },
            "DEFAULT": "12",
        },
        "DELAY_HIGH_CUT": {
            "NAME": "Delay High-Cut Filter",
            "TYPE": "DICT",
            "VALUES": {
                "0": "630",
                "1": "800",
                "2": "1k",
                "3": "1.25k",
                "4": "1.6k",
                "5": "2k",
                "6": "2.5k",
                "7": "3.15k",
                "8": "4k",
                "9": "5k",
                "10": "6.3k",
                "11": "8k",
                "12": "10k",
                "13": "12.5k",
                "14": "Flat",
            },
            "DEFAULT": "14",
        },
        "DELAY_SW": {"NAME": "Delay Switch", "TYPE": "UNK", "DEFAULT": "1"},
        "REVERB_TYPE": {
            "NAME": "Reverb Type",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Ambience",
                "1": "Room",
                "2": "Hall 1",
                "3": "Hall 2",
                "4": "Plate",
                "5": "Spring",
                "6": "Modulated",
            },
            "DEFAULT": "5",
        },
        "REVERB_TIME": {
            "NAME": "Reverb Time",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "200",
        },
        "REVERB_LEVEL": {
            "NAME": "Reverb Level",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": "0",
        },
        "REVERB_PRE_DELAY": {
            "NAME": "Reverb Pre-Delay",
            "TYPE": "INT",
            "RANGE": (0, 100),
            "DEFAULT": "20",
        },
        "REVERB_LOW_CUT": {
            "NAME": "Reverb Low-Cut Filter",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Flat",
                "1": "20",
                "2": "25",
                "3": "31.5",
                "4": "40",
                "5": "50",
                "6": "63",
                "7": "80",
                "8": "100",
                "9": "125",
                "10": "160",
                "11": "200",
                "12": "250",
                "13": "315",
                "14": "400",
                "15": "500",
                "16": "630",
                "17": "800",
            },
            "DEFAULT": "12",
        },
        "REVERB_HIGH_CUT": {
            "NAME": "Reverb High-Cut Filter",
            "TYPE": "DICT",
            "VALUES": {
                "0": "630",
                "1": "800",
                "2": "1k",
                "3": "1.25k",
                "4": "1.6k",
                "5": "2k",
                "6": "2.5k",
                "7": "3.15k",
                "8": "4k",
                "9": "5k",
                "10": "6.3k",
                "11": "8k",
                "12": "10k",
                "13": "12.5k",
                "14": "Flat",
            },
            "DEFAULT": "13",
        },
        "REVERB_DENSITY": {
            "NAME": "Reverb Density",
            "TYPE": "INT",
            "RANGE": (0, 10),
            "DEFAULT": "10",
        },
        "OSC_DRAW_SW": {
            "NAME": "Oscillator Draw Switch",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "Step", 2: "Slope"},
            "DEFAULT": "0",
        },
        "OSC_DRAW_MULT": {
            "NAME": "Oscillator Draw Multiplier",
            "TYPE": "INT",
            "RANGE": (0, 255),
            "DEFAULT": 7,
        },  # Encoding?
        # Oscillator Draw Pads SPLIT_TC: Binary representation split in 2 halves,
        # then "Two's Complement" each into an integer (with _higher_ index first)
        "OSC_DRAW_P1": {
            "NAME": "Oscillator Draw 1/2",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 46492,
        },
        "OSC_DRAW_P2": {
            "NAME": "Oscillator Draw 3/4",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 59342,
        },
        "OSC_DRAW_P3": {
            "NAME": "Oscillator Draw 5/6",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 6400,
        },
        "OSC_DRAW_P4": {
            "NAME": "Oscillator Draw 7/8",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 19250,
        },
        "OSC_DRAW_P5": {
            "NAME": "Oscillator Draw 9/10",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 19300,
        },
        "OSC_DRAW_P6": {
            "NAME": "Oscillator Draw 11/12",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 6450,
        },
        "OSC_DRAW_P7": {
            "NAME": "Oscillator Draw 13/14",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 59136,
        },
        "OSC_DRAW_P8": {
            "NAME": "Oscillator Draw 15/16",
            "TYPE": "SPLIT_TC",
            "INT": (0, 65535),
            "DEFAULT": 46542,
        },
        "OSC_CHOP_TYPE": {
            "NAME": "Oscillator Chop Type",
            "TYPE": "UNK",
            "DEFAULT": "0",
        },  # ???
        "OSC_CHOP_OVERTONE": {
            "NAME": "Oscillator Chop Overtone",
            "TYPE": "INT",
            "RANGE": (0, 200),
            "DEFAULT": "100",
        },
        "OSC_CHOP_COMB_TYPE": {
            "NAME": "Oscillator Chop Comb Type",
            "TYPE": "UNK",
            "DEFAULT": "0",
        },
        "OSC_CHOP_COMB": {
            "NAME": "Oscillator Chop Comb",
            "TYPE": "COMB",
            "RANGE": (0, 255),
            "DEFAULT": 7,
        },  # Encoding??
        # The number in binary _reversed_ represents the on/off pattern of the pads
        "OSC_CHOP_PWM": {
            "NAME": "Oscillator Chop Square Pattern",
            "TYPE": "CHOP",
            "RANGE": (0, 65535),
            "DEFAULT": 65535,
        },
        "OSC_CHOP_SAW": {
            "NAME": "Oscillator Chop Saw Pattern",
            "TYPE": "CHOP",
            "RANGE": (0, 65535),
            "DEFAULT": 65535,
        },
        "OSC_CHOP_SUB": {
            "NAME": "Oscillator Chop Sub Pattern",
            "TYPE": "CHOP",
            "RANGE": (0, 65535),
            "DEFAULT": 65535,
        },
        "OSC_CHOP_NOISE": {
            "NAME": "Oscillator Chop Noise Pattern",
            "TYPE": "CHOP",
            "RANGE": (0, 65535),
            "DEFAULT": 65535,
        },
        "RISER_MODE": {
            "NAME": "Riser Mode",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Off",
                "1": "Sync",
                "2": "Quick Interval",
                "3": "Quick Pan",
            },
            "DEFAULT": "0",
        },
        "RISER_SW": {"NAME": "Riser Switch", "TYPE": "UNK", "DEFAULT": "0"},
        "RISER_CTRL": {"NAME": "Riser Control", "TYPE": "UNK", "DEFAULT": "0"},
        "RISER_BEAT": {"NAME": "Riser Beat", "TYPE": "UNK", "DEFAULT": "0"},
        "RISER_RESO": {
            "NAME": "Riser Resonance",
            "TYPE": "INT",
            "RANGE": (0, 100),
            "DEFAULT": "50",
        },
        "RISER_LEVEL": {
            "NAME": "Riser Level",
            "TYPE": "INT",
            "RANGE": (0, 100),
            "DEFAULT": "70",
        },
        "DM_ASSIGN_X": {
            "NAME": "D-Motion Roll",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Off",
                "1": "Modulation",
                "2": "Frequency",
                "3": "Resonance",
                "4": "Pitch Bend",
                "5": "Pan",
                "6": "Expression",
                "7": "Delay Level",
                "8": "Reverb Level",
            },
            "DEFAULT": "5",
        },
        "DM_ASSIGN_Y": {
            "NAME": "D-Motion Pitch",
            "TYPE": "DICT",
            "VALUES": {
                "0": "Off",
                "1": "Modulation",
                "2": "Frequency",
                "3": "Resonance",
                "4": "Pitch Bend",
                "5": "Pan",
                "6": "Expression",
                "7": "Delay Level",
                "8": "Reverb Level",
            },
            "DEFAULT": "6",
        },
        "DM_ASSIGN_TAP": {"NAME": "D-Motion Assign Tap", "TYPE": "UNK", "DEFAULT": "0"},
        "DM_ASSIGN_FF": {"NAME": "D-Motion Assign FF", "TYPE": "UNK", "DEFAULT": "0"},
        "DM_SENS_X": {"NAME": "D-Motion X Sensitivity", "TYPE": "UNK", "DEFAULT": "5"},
        "DM_SENS_Y": {"NAME": "D-Motion Y Sensitivity", "TYPE": "UNK", "DEFAULT": "5"},
        "LFO_KEY_TRIG": {
            "NAME": "LFO Key Trigger",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "0",
        },
        "LFO_SYNC": {
            "NAME": "LFO Sync Mode",
            "TYPE": "DICT",
            "VALUES": {"0": "Off", "1": "On"},
            "DEFAULT": "0",
        },
        "RISER_SHAPE": {
            "NAME": "Riser Shape",
            "TYPE": "INT",
            "RANGE": (0, 100),
            "DEFAULT": "0",
        },
        "PRM1": {"NAME": "PRM 1", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM2": {"NAME": "PRM 2", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM3": {"NAME": "PRM 3", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM4": {"NAME": "PRM 4", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM5": {"NAME": "PRM 5", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM6": {"NAME": "PRM 6", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM7": {"NAME": "PRM 7", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM8": {"NAME": "PRM 8", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM9": {"NAME": "PRM 9", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM10": {"NAME": "PRM 10", "TYPE": "UNK", "DEFAULT": "0"},
        "PRM11": {"NAME": "PRM 11", "TYPE": "UNK", "DEFAULT": "0"},
    }
