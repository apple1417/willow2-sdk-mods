#!/usr/bin/env python

# This file is just a helper to let you run the BLIMP tag test suite against the file parser
# It should be run in a regular interpreter, it (obviously) won't do anything from inside the game
# https://github.com/apple1417/blcmm-parsing/tree/master/blimp#tests
if __name__ == "__main__":
    import json
    import sys

    import file_parser

    parse_result = file_parser.parse_string(sys.stdin.read())

    sys.stdout.write(json.dumps(parse_result.blimp_tags))
    sys.exit(0)
