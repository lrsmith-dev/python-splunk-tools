#!/usr/bin/env python3

import argparse
import dill as pickle
import os
import splunklib.client as client
from slugify import slugify

def download_saved_searches( splunkClient, outputFormat ):
    savedsearches = splunkClient.saved_searches
    for saved_search in savedsearches:
      fileName = "SavedSearches/%s.obj" % slugify(saved_search.name)
      if outputFormat == 'pickle':
        fileName = "SavedSearches/%s.obj" % slugify(saved_search.name)
        f = open(fileName,'wb')
        pickle.dump(saved_search.state,f)
      elif outputFormat == "splunk-conf":
        fileName = "SavedSearches/%s.conf" % slugify(saved_search.name)
        f = open(fileName,'w')
        f.write(f"#savedsearches.conf\n")
        f.write(f"[ {saved_search.name} ]\n")
        defaultSettings = import_savedsearches_defaults()
        for k,v in saved_search.content.items():
            try:
                if defaultSettings[k] == v:
                    continue
                else:
                    if v != None:
                      f.write(f"{ k } = {v}\n")
            except KeyError:            # No default setting so print
                f.write(f"{ k } = {v}\n")
        f.write(f"\n\n")
        f.write(f"# local.meta\n")
        f.write(f"[savedsearches/{ saved_search.name }]\n")
        f.write(f"owner = { saved_search.access['owner'] }\n")
        perms = ', '.join("{!s} : {!r}".format(k,v) for (k,v) in saved_search.access['perms'].items()).replace('\'','')
        f.write(f"access = { perms }\n")
      f.close()

def list_saved_searches( splunkClient, outputFormat ):
    savedsearches = splunkClient.saved_searches
    for saved_search in savedsearches:
       print(f"{ saved_search.access['app'] } : {saved_search.name}")

# Given a savedsearches.conf from a Splunk Server, convert to a dict and return.
def import_savedsearches_defaults():
  d = {}
  with open("Data/default-savedsearches.conf") as f:
    for line in f:
      if line[0].isalnum():
        (k, v) = line.strip().split('=',1)
        d[k.rstrip()] = v.lstrip()
  return d

if __name__ == "__main__":
    
    # List of allowed positional arguments and function to call
    command_map = { 'download' : download_saved_searches,
                    'list': list_saved_searches,
                  }

    # Setup argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('command' , choices=command_map.keys() )
    #parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output.")
    #parser.add_argument("-q", "--quiet", action="store_true", help="Disable output and run in quiet mode.")

    parser.add_argument("--output-format", default="pickle", choices=['pickle','splunk-conf'], help="Format to output SavedSearches to. splunk-conf, pickle")

    parser.add_argument("--splunk-app", default="-", help="Splunk app to look for saved searches in.")
    parser.add_argument("--splunk-port", default="8089", help="Splunk Server port")
    parser.add_argument("--splunk-server", default="localhost", help="Splunk Server to connect to.")
    
    args = parser.parse_args()

    # Connect to specified Splunk Server
    splunkClient = client.connect(
        app  = args.splunk_app,
        host = args.splunk_server,
        port = args.splunk_port,
        splunkToken=os.getenv('BEARER_TOKEN')
        )
    assert isinstance(splunkClient, client.Service)

    # Execute function based on command
    command_map[args.command](splunkClient, args.output_format)
