# This script converts the json files of the dash dataset of the bellow url into csv files
# http://media.polito.it/mmsys14-dataset/neubot-dash-dataset-mmsys14.readme.md

import os
import csv
import json
import sys
import argparse

parser = argparse.ArgumentParser(description='Converts the json files of the dash dataset into csv files.')
parser.add_argument('input_path', nargs=1, metavar='input_path', type=str, help='Path with the json files ended by _dash.')
parser.add_argument('output_path', nargs=1, metavar='output_path', type=str, help='Path (or file if -b) where the csv files will be saved.')
parser.add_argument('-v', action='store_true', default=False, help='Turn verbose mode on.')
parser.add_argument('-b', action='store_true', default=False, help='Only one big file as output, otherwise each input file will create one output file.')

args = parser.parse_args()
VERBOSE = args.v
ONE_BIG_FILE = args.b

if not os.path.isdir(args.input_path[0]) or (not ONE_BIG_FILE and not os.path.isdir(args.output_path[0])):
    print "Please enter valid directories"
    sys.exit()

def createOutput(outputFilepath):
    if os.path.isfile(outputFilepath):
        print "Output file ", outputFilepath, " already exists."
        sys.exit()
    f = open(outputFilepath, "wb+")
    fw = csv.writer(f)
    fw.writerow(["srvr_schema_version", 
                "srvr_timestamp", 
                "client_real_address", 
                "client_delta_user_time",
                "client_uuid",
                "client_elapsed_target",
                "client_received",
                "client_timestamp",
                "client_connect_time",
                "client_iteration",
                "client_remote_address",
                "client_elapsed",
                "client_platform",
                "client_rate",
                "client_version",
                "client_delta_sys_time",
                "client_internal_address",
                "client_request_ticks"])
    return (f, fw)

if ONE_BIG_FILE:
    (f,fw) = createOutput(args.output_path[0])
    
for root, dirs, files in os.walk(args.input_path[0]):
    for name in files:
        if name.endswith('_dash'): # Only parse the dash files in the directories
            filepath = os.path.join(root, name)
            if VERBOSE:
                print 'Parsing ', filepath
            
            f = open(filepath)
            jsonContent = json.load(f)
            f.close()

            if not ONE_BIG_FILE:
                (f,fw) = createOutput(os.path.join(args.output_path[0],(name+'.csv')))

            for client in jsonContent["client"]:
                fw.writerow([jsonContent["srvr_schema_version"], 
                            jsonContent["srvr_timestamp"], 
                            client["real_address"], 
                            client["delta_user_time"],
                            client["uuid"],
                            client["elapsed_target"],
                            client["received"],
                            client["timestamp"],
                            client["connect_time"],
                            client["iteration"],
                            client["remote_address"],
                            client["elapsed"],
                            client["platform"],
                            client["rate"],
                            client["version"],
                            client["delta_sys_time"],
                            client["internal_address"],
                            client["request_ticks"]])

            if not ONE_BIG_FILE:
                f.close()



