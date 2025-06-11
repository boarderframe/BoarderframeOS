#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, '/Users/cosburn/BoarderframeOS/boarderframeos')

import asyncio

# Now import and run Solomon
from agents.solomon.solomon import main

if __name__ == "__main__":
    asyncio.run(main())
