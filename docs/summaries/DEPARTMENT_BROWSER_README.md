# BoarderframeOS Department Browser

A user-friendly interface for browsing the BoarderframeOS department structure in an intuitive card-based UI.

## Overview

This application provides a visual way to explore the BoarderframeOS organizational structure. Available in both basic and enhanced versions:

### Basic Browser Features
- **Card-based department visualization**: Each department displayed as an interactive card
- **Search functionality**: Find departments, leaders, or agents by keyword
- **Category filtering**: Filter departments by their organizational category
- **Sorting options**: Sort departments by name, category, or team size
- **Responsive design**: Works on both desktop and mobile devices

### Enhanced Browser Features (All basic features plus)
- **Interactive organizational chart**: Visual representation of the entire organization
- **Department visualizations**: Charts showing department distribution by category
- **Agent distribution analysis**: Visual breakdown of agent allocation across departments
- **Leader-to-agent ratio analysis**: Compare leadership structure across departments
- **Category breakdown**: Detailed view of departments by category

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Streamlit
- Pillow (PIL Fork)

### Installation

If you haven't already installed the required packages:

```bash
pip install streamlit pillow
```

### Running the Application

From the BoarderframeOS directory, you can use the launcher script:

```bash
./launch_browser.sh
```

This will give you the option to launch either the basic or enhanced version.

Alternatively, you can run either browser directly:

```bash
# For basic browser
streamlit run department_browser.py

# For enhanced browser with visualizations
streamlit run enhanced_department_browser.py
```

This will start the application and automatically open it in your default web browser at `http://localhost:8501`.

## Usage

1. **Browse Departments**: Scroll through the department cards to explore the organization
2. **Search**: Use the search box in the sidebar to find specific departments, leaders, or agents
3. **Filter by Category**: Select one or more categories from the dropdown to filter departments
4. **Sort**: Choose a sorting method to organize the department cards
5. **View Details**: Each card contains comprehensive information about the department, including:
   - Department name and category
   - Description and purpose
   - Leadership team
   - Native agents and their roles

## Data Structure

The application reads data from the `departments/boarderframeos-departments.json` file, which contains the complete organizational structure of BoarderframeOS.

## Customization

You can customize the appearance by modifying the CSS styles in the `department_browser.py` file.

## License

Copyright © 2025 BoarderframeOS
