#!/usr/bin/env python3

import argparse
import dill as pickle
import os
import splunklib.client as client
from slugify import slugify


def download_saved_searches(splunkClient):

    savedsearches = splunkClient.saved_searches

    isExist = os.path.exists(args.output_dir)
    if not isExist:
        if args.debug:
            print("Creating dir : ", tmpOutputDir)
        os.makedirs(args.output_dir)

    # Iterate through each saved search
    for saved_search in savedsearches:

        # Output in pickle format
        if args.output_format == 'pickle':
            fileName = "%s/%s.obj" % (args.output_dir, slugify(saved_search.name))
            f = open(fileName, 'wb')
            pickle.dump(saved_search.state, f)

        # Output in splunk conf format.
        elif args.output_format == "splunk-conf":

            tmpOutputDir = "/".join([args.output_dir, slugify(saved_search.name)])
            isExist = os.path.exists(tmpOutputDir)
            if not isExist:
                if args.debug:
                    print("Creating dir : ", tmpOutputDir)
                os.makedirs(tmpOutputDir)

            # Given a savedsearches.conf from a Splunk Server, convert to a dict and return.
            defaultSettings = import_savedsearches_defaults()

            # Write savedsearches.conf file
            savedSearchFile = open("%s/savedsearches.conf" % tmpOutputDir, 'w')
            savedSearchFile.write(f"[ {saved_search.name} ]\n")

            for k, v in saved_search.content.items():
                try:
                    if defaultSettings[k] == v:
                        continue
                    else:
                        if v != None:
                            savedSearchFile.write(f"{ k } = {v}\n")
                except KeyError:            # No default setting so print
                    savedSearchFile.write(f"{ k } = {v}\n")
            savedSearchFile.close()

            # Write default.meta file
            defaultMetaFile = open("%s/default.meta" % tmpOutputDir, 'w')
            defaultMetaFile.write(f"[ {saved_search.name} ]\n")

            defaultMetaFile.write(f"[savedsearches/{ saved_search.name }]\n")
            defaultMetaFile.write(
                f"owner = { saved_search.access['owner'] }\n")
            perms = ', '.join("{!s} : {!r}".format(k, v) for (
                k, v) in saved_search.access['perms'].items()).replace('\'', '')
            defaultMetaFile.write(f"access = { perms }\n")
            defaultMetaFile.close()


def list_saved_searches(splunkClient):
    savedsearches = splunkClient.saved_searches
    print(f"name,app,owner")
    for saved_search in savedsearches:
        print(
            f"\"{saved_search.name}\",\"{saved_search.access['app']}\",\"{ saved_search.access['owner'] }\"")


# Given a savedsearches.conf from a Splunk Server, convert to a dict and return.
def import_savedsearches_defaults():
    d = {}
    with open("Data/default-savedsearches.conf") as f:
        for line in f:
            if line[0].isalnum():
                (k, v) = line.strip().split('=', 1)
                d[k.rstrip()] = v.lstrip()
    return d

# Main Function
if __name__ == "__main__":

    # List of allowed positional arguments and function to call
    command_map = {'download': download_saved_searches,
                   'list': list_saved_searches,
                   }

    # Setup argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=command_map.keys())
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output.")
    # parser.add_argument("-q", "--quiet", action="store_true", help="Disable output and run in quiet mode.")

    parser.add_argument("--output-dir", default="./SavedSearches",
                        help="Where to save download objects")
    parser.add_argument("--output-format", default="pickle", choices=[
                        'pickle', 'splunk-conf'], help="Format to output SavedSearches to. splunk-conf, pickle")

    parser.add_argument("--splunk-app", default="-",
                        help="Splunk app to look for saved searches in.")
    parser.add_argument("--splunk-port", default="8089",
                        help="Splunk Server port")
    parser.add_argument("--splunk-server", default="localhost",
                        help="Splunk Server to connect to.")

    args = parser.parse_args()

    # Connect to specified Splunk Server
    splunkClient = client.connect(
        app=args.splunk_app,
        host=args.splunk_server,
        port=args.splunk_port,
        splunkToken=os.getenv('BEARER_TOKEN')
    )
    assert isinstance(splunkClient, client.Service)

    # Execute function based on command
    command_map[args.command]( splunkClient )
