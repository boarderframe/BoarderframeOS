#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/Users/cosburn/BoarderframeOS/boarderframeos')

# Now import and run Solomon
from agents.solomon.solomon import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())