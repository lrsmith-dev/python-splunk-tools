# saved_searches.py

## Overview

This python script provide a CLI for interacting with Splunk Saved Searches, via Splunk's REST API.

## Commands

### `download --output-format pickle`

Download all the saved searches into Pickle formatted files, for future processing.

### `download --output-format splunk-conf`

Download all the saved searches into a "Splunk Formatted file." This will use Splunk's default SavedSearches.conf to remove configs which are set to the defaults, for a fresh Splunk install. 
