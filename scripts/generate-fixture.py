"""Script for generating database fixtures for test metadata."""

import json
import sys
from operator import itemgetter

from cloudnetpy_qc.quality import Test

if __name__ == "__main__":
    tests = [
        {
            "testId": cls.__name__,
            "name": cls.name,
            "description": cls.description,
        }
        for cls in Test.__subclasses__()
    ]
    tests = sorted(tests, key=itemgetter("testId"))
    json.dump(tests, sys.stdout, indent=2)
    sys.stdout.write("\n")
