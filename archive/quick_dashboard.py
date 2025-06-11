#!/usr/bin/env python3
import os

os.system("pkill -f 'python.*8888' 2>/dev/null")
import time

time.sleep(2)
import sys

sys.path.insert(0, "/Users/cosburn/BoarderframeOS")
from enhanced_dashboard import main

main()
