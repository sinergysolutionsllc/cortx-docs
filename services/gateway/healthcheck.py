#!/usr/bin/env python3
import sys
import urllib.error
import urllib.request

try:
    response = urllib.request.urlopen("http://localhost:8080/health", timeout=5)
    if response.status == 200:
        sys.exit(0)
    else:
        sys.exit(1)
except Exception:
    sys.exit(1)
