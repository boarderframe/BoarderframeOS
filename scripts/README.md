# BoarderframeOS Scripts

This directory contains utility scripts organized by purpose.

## Directory Structure

- **`database/`** - Database management scripts (registration, population, migration)
- **`enhance/`** - Enhancement scripts for existing features
- **`integrate/`** - Integration scripts for connecting components
- **`launch/`** - Scripts to launch various system components
- **`publish/`** - Scripts for publishing and deployment
- **`run/`** - Scripts to run specific components or tests
- **`updates/`** - Scripts to update existing data or configurations
- **`utils/`** - General utility scripts (cleanup, restore, etc.)
- **`verify/`** - Verification and validation scripts

## Usage

Most scripts can be run directly:
```bash
python scripts/launch/launch_corporate_headquarters.py
```

Or made executable:
```bash
chmod +x scripts/launch/launch_browser.sh
./scripts/launch/launch_browser.sh
```

## Adding New Scripts

When adding new scripts:
1. Place them in the appropriate subdirectory
2. Add clear docstrings explaining purpose
3. Use descriptive names
4. Consider if it's a one-off script (archive/) or utility (scripts/)

## Script Categories

### Database Scripts (`database/`)
- Component registration
- Data population
- Schema updates

### Launch Scripts (`launch/`)
- Start UI components
- Launch specific agents
- Initialize systems

### Utility Scripts (`utils/`)
- Process management
- Backup/restore
- General maintenance

### Verification Scripts (`verify/`)
- System validation
- Integration testing
- Health checks