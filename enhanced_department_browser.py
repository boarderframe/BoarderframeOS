#!/usr/bin/env python
"""
Enhanced Department Browser - BoarderframeOS

An advanced UI interface for browsing department information from BoarderframeOS
with additional visualizations and interactive features.
"""
import colorsys
import json
import math
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psutil
import streamlit as st
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="BoarderframeOS Department Browser",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .card {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .card-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .card-category {
        font-size: 16px;
        color: #555;
        margin-bottom: 15px;
    }
    .card-description {
        font-size: 18px;
        margin-bottom: 15px;
    }
    .card-purpose {
        font-size: 16px;
        font-style: italic;
        margin-bottom: 15px;
    }
    .section-title {
        font-size: 18px;
        font-weight: bold;
        margin: 15px 0 10px 0;
    }
    .leader-name {
        font-weight: bold;
    }
    .leader-title {
        color: #666;
    }
    .agent-name {
        font-weight: bold;
    }
    .sidebar-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .highlight {
        background-color: #FFD700;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .stButton>button {
        width: 100%;
    }
    .tab-subheader {
        font-size: 20px;
        font-weight: 600;
        margin: 20px 0 10px 0;
    }
    .view-selector {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .stat-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .stat-label {
        font-size: 14px;
        color: #666;
    }
    .department-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        grid-gap: 20px;
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #888;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

def generate_color(category):
    """Generate consistent colors based on category name"""
    # Create a hash of the category name to get consistent colors
    hash_val = sum(ord(c) for c in category)
    hue = (hash_val % 100) / 100.0  # Hue between 0 and 1

    # Predefined saturation and value for pleasant colors
    saturation = 0.4
    value = 0.95

    # Convert HSV to RGB
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)

    # Convert RGB to hex color
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

def load_department_data():
    """Load department data from JSON file"""
    json_path = os.path.join(os.path.dirname(__file__),
                             "departments",
                             "boarderframeos-departments.json")

    with open(json_path, "r") as file:
        data = json.load(file)

    return data

def get_all_departments_from_phases(departments_data):
    """Extract all departments from the phase-based structure"""
    all_departments = {}
    all_phases = []

    for phase_key, phase_data in departments_data.items():
        if phase_key == "metadata":
            continue

        if "departments" in phase_data:
            phase_name = phase_data.get("phase_name", phase_key)
            all_phases.append(phase_name)

            for dept_key, dept_data in phase_data["departments"].items():
                # Add phase information to department
                dept_data["phase"] = phase_name
                dept_data["phase_priority"] = phase_data.get("priority", 999)
                all_departments[dept_key] = dept_data

    return all_departments, all_phases

def get_all_categories_from_phases(all_departments):
    """Get all unique categories from departments"""
    categories = set()
    phases = set()

    for dept in all_departments.values():
        if "category" in dept:
            categories.add(dept["category"])
        if "phase" in dept:
            phases.add(dept["phase"])

    return list(categories), list(phases)

def display_search(all_departments, all_categories, all_phases):
    """Display search functionality"""
    st.sidebar.header("Search & Filter")

    # Search bar
    search_query = st.sidebar.text_input("Search Departments, Leaders, or Agents")

    # Phase filter
    phase_filter = st.sidebar.multiselect(
        "Filter by Phase",
        options=all_phases,
        default=[]
    )

    # Category filter
    category_filter = st.sidebar.multiselect(
        "Filter by Category",
        options=all_categories,
        default=[]
    )

    # Sort option
    sort_option = st.sidebar.selectbox(
        "Sort by",
        ["Phase Priority", "Department Name (A-Z)", "Category", "Number of Leaders", "Number of Agents"]
    )

    return search_query, category_filter, phase_filter, sort_option

def filter_departments(departments_data, search_query, category_filter, phase_filter):
    """Filter departments based on search query, category filter, and phase filter"""
    filtered_departments = {}

    for key, department in departments_data.items():
        # Check if department matches phase filter
        if phase_filter and department.get("phase") not in phase_filter:
            continue

        # Check if department matches category filter
        if category_filter and department["category"] not in category_filter:
            continue

        # Check if department matches search query
        if search_query.lower():
            # Search in department name
            if search_query.lower() in department["department_name"].lower():
                filtered_departments[key] = department
                continue

            # Search in leaders
            leaders_match = any(search_query.lower() in leader["name"].lower() or
                               search_query.lower() in leader["title"].lower() or
                               search_query.lower() in leader["description"].lower()
                               for leader in department["leaders"])
            if leaders_match:
                filtered_departments[key] = department
                continue

            # Search in agents
            agents_match = any(search_query.lower() in agent["name"].lower() or
                              search_query.lower() in agent["description"].lower()
                              for agent in department["native_agents"])
            if agents_match:
                filtered_departments[key] = department
                continue

            # Search in other fields
            if (search_query.lower() in department["description"].lower() or
                search_query.lower() in department["department_purpose"].lower()):
                filtered_departments[key] = department
                continue
        else:
            # If no search query, include this department
            filtered_departments[key] = department

    return filtered_departments

def sort_departments(filtered_departments, sort_option):
    """Sort departments based on selected sort option"""
    if sort_option == "Phase Priority":
        return dict(sorted(filtered_departments.items(),
                           key=lambda item: (item[1].get("phase_priority", 999), item[1]["department_name"])))

    elif sort_option == "Department Name (A-Z)":
        return dict(sorted(filtered_departments.items(),
                           key=lambda item: item[1]["department_name"]))

    elif sort_option == "Category":
        return dict(sorted(filtered_departments.items(),
                           key=lambda item: item[1]["category"]))

    elif sort_option == "Number of Leaders":
        return dict(sorted(filtered_departments.items(),
                           key=lambda item: len(item[1]["leaders"]), reverse=True))

    elif sort_option == "Number of Agents":
        return dict(sorted(filtered_departments.items(),
                           key=lambda item: len(item[1]["native_agents"]), reverse=True))

    return filtered_departments

def display_department_cards(departments, search_query=""):
    """Display department information in cards"""
    # Create columns for displaying cards (3 columns)
    cols = st.columns(3)

    # Display departments in card format
    for i, (key, department) in enumerate(departments.items()):
        col = cols[i % 3]

        # Generate color based on phase
        phase_color = generate_color(department.get("phase", "Unknown"))

        with col:
            with st.container():
                st.markdown(f"""
                <div class="card" style="border-left: 5px solid {phase_color}; background-color: rgba{tuple(int(phase_color[1:][i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}">
                    <div class="card-title">{department["department_name"]}</div>
                    <div class="card-phase" style="color: {phase_color}; font-weight: bold;">{department.get("phase", "Unknown Phase")}</div>
                    <div class="card-category">{department["category"]}</div>
                    <div class="card-description">{department["description"]}</div>
                    <div class="card-purpose">{department["department_purpose"]}</div>

                    <div class="section-title">Leadership:</div>
                    {"".join([f'<div><span class="leader-name">{leader["name"]}</span> - <span class="leader-title">{leader["title"]}</span></div>' for leader in department["leaders"]])}

                    <div class="section-title">Native Agents:</div>
                    {"".join([f'<div><span class="agent-name">{agent["name"]}</span>: {agent["description"]}</div>' for agent in department["native_agents"]])}
                </div>
                """, unsafe_allow_html=True)

                # Highlight search terms if provided
                if search_query:
                    st.markdown(f"""
                    <script>
                        // Simple highlighting script
                        document.querySelectorAll('.card').forEach(card => {{
                            const html = card.innerHTML;
                            card.innerHTML = html.replace(new RegExp('({search_query})', 'gi'),
                                                        '<span class="highlight">$1</span>');
                        }});
                    </script>
                    """, unsafe_allow_html=True)

def display_metadata(metadata):
    """Display metadata in the sidebar"""
    st.sidebar.header("BoarderframeOS Overview")

    st.sidebar.markdown(f"""
    <div class="sidebar-info">
        <strong>Departments:</strong> {metadata["total_departments"]}<br>
        <strong>Leaders:</strong> {metadata["total_leaders"]}<br>
        <strong>Teams:</strong> {metadata["total_teams"]}<br>
        <strong>Last Updated:</strong> {metadata["last_updated"]}<br>
        <strong>Version:</strong> {metadata["version"]}
    </div>
    """, unsafe_allow_html=True)

def create_org_chart(departments_data, metadata):
    """Create an interactive organizational chart"""
    # Create a network graph
    G = nx.Graph()

    # Add departments as nodes
    for key, dept in departments_data.items():
        G.add_node(dept["department_name"],
                  category=dept["category"],
                  description=dept["description"],
                  node_type="department")

    # Add leaders as nodes and connect them to departments
    for key, dept in departments_data.items():
        for leader in dept["leaders"]:
            leader_name = f"{leader['name']} ({leader['title']})"
            G.add_node(leader_name,
                      description=leader["description"],
                      node_type="leader")
            G.add_edge(dept["department_name"], leader_name)

    # Create positions for nodes using a hierarchical layout
    pos = nx.spring_layout(G, k=0.9, iterations=50)

    # Create edge trace
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node traces for departments and leaders
    node_x_dept = []
    node_y_dept = []
    node_text_dept = []
    node_color_dept = []

    node_x_leader = []
    node_y_leader = []
    node_text_leader = []

    for node in G.nodes():
        x, y = pos[node]

        if G.nodes[node]['node_type'] == 'department':
            node_x_dept.append(x)
            node_y_dept.append(y)
            node_color_dept.append(generate_color(G.nodes[node]['category']))
            node_text_dept.append(f"{node}<br>{G.nodes[node]['category']}<br>{G.nodes[node]['description']}")
        else:
            node_x_leader.append(x)
            node_y_leader.append(y)
            node_text_leader.append(f"{node}<br>{G.nodes[node]['description']}")

    # Department nodes
    node_trace_dept = go.Scatter(
        x=node_x_dept, y=node_y_dept,
        mode='markers',
        hoverinfo='text',
        text=node_text_dept,
        marker=dict(
            showscale=False,
            color=node_color_dept,
            size=20,
            line=dict(width=2, color='#333')
        )
    )

    # Leader nodes
    node_trace_leader = go.Scatter(
        x=node_x_leader, y=node_y_leader,
        mode='markers',
        hoverinfo='text',
        text=node_text_leader,
        marker=dict(
            showscale=False,
            color='#2ca02c',
            size=15,
            symbol='diamond',
            line=dict(width=2, color='#333')
        )
    )

    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace_dept, node_trace_leader],
                    layout=go.Layout(
                        title=dict(text='BoarderframeOS Organizational Structure', font=dict(size=16)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        ))

    # Add custom legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=15, color='#1f77b4'),
        name='Department'
    ))

    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=12, color='#2ca02c', symbol='diamond'),
        name='Leader'
    ))

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=800
    )

    return fig

def create_category_chart(departments_data):
    """Create a chart showing departments by category"""
    # Count departments per category
    categories = {}
    for key, dept in departments_data.items():
        cat = dept["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    # Convert to DataFrame
    df = pd.DataFrame({
        'Category': list(categories.keys()),
        'Count': list(categories.values())
    })

    # Sort by count
    df = df.sort_values('Count', ascending=False)

    # Create a bar chart
    fig = px.bar(df,
                x='Category',
                y='Count',
                color='Category',
                labels={'Count': 'Number of Departments'},
                title='Departments by Category')

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Number of Departments",
        height=500
    )

    return fig

def create_phase_chart(departments_data):
    """Create a chart showing departments by phase"""
    # Count departments per phase
    phases = {}
    for key, dept in departments_data.items():
        phase = dept.get("phase", "Unknown")
        if phase not in phases:
            phases[phase] = 0
        phases[phase] += 1

    # Convert to DataFrame
    df = pd.DataFrame({
        'Phase': list(phases.keys()),
        'Count': list(phases.values())
    })

    # Sort by count
    df = df.sort_values('Count', ascending=False)

    # Create a bar chart
    fig = px.bar(df,
                x='Phase',
                y='Count',
                color='Phase',
                labels={'Count': 'Number of Departments'},
                title='Departments by Development Phase')

    fig.update_layout(
        xaxis_title="Development Phase",
        yaxis_title="Number of Departments",
        height=500,
        xaxis={'tickangle': 45}
    )

    return fig

def create_agent_distribution(departments_data):
    """Create a chart showing agent distribution across departments"""
    # Count agents per department
    agent_counts = []
    for key, dept in departments_data.items():
        agent_counts.append({
            'Department': dept['department_name'],
            'Category': dept['category'],
            'Agents': len(dept['native_agents'])
        })

    # Convert to DataFrame and sort
    df = pd.DataFrame(agent_counts)
    df = df.sort_values('Agents', ascending=False)

    # Create a bar chart
    fig = px.bar(df,
                x='Department',
                y='Agents',
                color='Category',
                labels={'Agents': 'Number of Native Agents'},
                title='Native Agents by Department')

    fig.update_layout(
        xaxis_title="Department",
        yaxis_title="Number of Agents",
        xaxis=dict(tickangle=45),
        height=600
    )

    return fig

def create_leader_agent_ratio(departments_data):
    """Create a scatter plot comparing leaders to agents in departments"""
    data = []

    for key, dept in departments_data.items():
        data.append({
            'Department': dept['department_name'],
            'Category': dept['category'],
            'Leaders': len(dept['leaders']),
            'Agents': len(dept['native_agents']),
            'Ratio': len(dept['native_agents']) / max(1, len(dept['leaders']))
        })

    df = pd.DataFrame(data)

    fig = px.scatter(
        df,
        x='Leaders',
        y='Agents',
        size='Ratio',
        color='Category',
        hover_name='Department',
        labels={'Agents': 'Number of Native Agents', 'Leaders': 'Number of Leaders'},
        title='Leaders to Agents Ratio by Department'
    )

    fig.update_layout(height=600)

    return fig

def get_running_agents():
    """Get currently running agents by checking processes"""
    running_agents = {}
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    # Check for agent scripts
                    if any('agents/' in cmd and '.py' in cmd for cmd in cmdline):
                        for cmd in cmdline:
                            if 'agents/' in cmd and '.py' in cmd:
                                agent_path = Path(cmd)
                                agent_name = agent_path.parent.name
                                if agent_name not in running_agents:
                                    running_agents[agent_name] = {
                                        'pid': proc.info['pid'],
                                        'name': agent_name,
                                        'path': cmd,
                                        'status': 'running'
                                    }
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        st.error(f"Error checking running agents: {e}")

    return running_agents

def get_available_agents():
    """Get list of available agents from the agents directory"""
    agents_dir = Path(__file__).parent / "agents"
    available_agents = {}

    if agents_dir.exists():
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name not in ['.', '..', '__pycache__']:
                agent_script = agent_dir / f"{agent_dir.name}.py"
                if agent_script.exists():
                    available_agents[agent_dir.name] = {
                        'name': agent_dir.name,
                        'path': str(agent_script),
                        'status': 'available'
                    }

    return available_agents

def start_agent(agent_name):
    """Start an agent using subprocess"""
    try:
        agents_dir = Path(__file__).parent / "agents"
        agent_script = agents_dir / agent_name / f"{agent_name}.py"

        if agent_script.exists():
            # Start agent in background
            process = subprocess.Popen(
                [sys.executable, str(agent_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(agent_script.parent)
            )
            time.sleep(2)  # Give it time to start

            # Check if process is still running
            if process.poll() is None:
                return True, f"Agent {agent_name} started successfully with PID {process.pid}"
            else:
                stdout, stderr = process.communicate()
                return False, f"Agent {agent_name} failed to start: {stderr.decode()}"
        else:
            return False, f"Agent script not found: {agent_script}"
    except Exception as e:
        return False, f"Error starting agent {agent_name}: {e}"

def stop_agent(agent_name, pid):
    """Stop an agent by PID"""
    try:
        process = psutil.Process(pid)
        process.terminate()

        # Wait for graceful termination
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            # Force kill if it doesn't terminate gracefully
            process.kill()

        return True, f"Agent {agent_name} stopped successfully"
    except psutil.NoSuchProcess:
        return True, f"Agent {agent_name} was already stopped"
    except Exception as e:
        return False, f"Error stopping agent {agent_name}: {e}"

def display_agent_management():
    """Display agent management interface"""
    st.subheader("🤖 Agent Management")

    # Get running and available agents
    running_agents = get_running_agents()
    available_agents = get_available_agents()

    # Create two columns for running and available agents
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 Running Agents")
        if running_agents:
            for agent_name, agent_info in running_agents.items():
                with st.container():
                    st.markdown(f"""
                    <div class="card" style="background-color: #e8f5e8;">
                        <div class="card-title">{agent_name.title()}</div>
                        <div class="card-description">PID: {agent_info['pid']}</div>
                        <div class="card-description">Status: {agent_info['status']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Stop {agent_name}", key=f"stop_{agent_name}"):
                        success, message = stop_agent(agent_name, agent_info['pid'])
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No agents are currently running")

    with col2:
        st.markdown("### ⚪ Available Agents")
        if available_agents:
            for agent_name, agent_info in available_agents.items():
                # Skip if already running
                if agent_name in running_agents:
                    continue

                with st.container():
                    st.markdown(f"""
                    <div class="card" style="background-color: #f5f5f5;">
                        <div class="card-title">{agent_name.title()}</div>
                        <div class="card-description">Path: {agent_info['path']}</div>
                        <div class="card-description">Status: {agent_info['status']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"Start {agent_name}", key=f"start_{agent_name}"):
                        success, message = start_agent(agent_name)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.info("No additional agents available to start")

    # Agent status summary
    st.markdown("---")
    st.markdown("### 📊 Agent Status Summary")

    total_running = len(running_agents)
    total_available = len(available_agents)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Running Agents", total_running)
    with col2:
        st.metric("Available Agents", total_available)
    with col3:
        st.metric("Total Agents", total_running + max(0, total_available - total_running))

    # Refresh button
    if st.button("🔄 Refresh Agent Status", key="refresh_agents"):
        st.rerun()

def get_cost_settings():
    """Load cost management settings"""
    try:
        cost_file = Path(__file__).parent / "core" / "cost_management.py"
        if cost_file.exists():
            # Read and parse the cost settings
            with open(cost_file, 'r') as f:
                content = f.read()

            # Extract API_COST_SETTINGS using simple parsing
            # This is a simplified approach - in production you'd use ast.literal_eval
            settings = {
                "cost_optimization_enabled": True,
                "daily_budget_usd": 50.0,
                "warning_threshold_usd": 40.0,
                "emergency_stop_usd": 55.0,
                "max_calls_per_minute": 30,
                "max_calls_per_hour": 300,
                "max_calls_per_day": 2000,
            }
            return settings
    except Exception as e:
        st.error(f"Error loading cost settings: {e}")

    return {}

def get_mock_cost_data():
    """Generate mock cost data for demonstration"""
    # In a real implementation, this would read from logs/database
    current_date = datetime.now()

    # Mock daily costs for the last 7 days
    daily_costs = []
    for i in range(7):
        date = current_date - timedelta(days=i)
        cost = random.uniform(15, 45)  # Random cost between $15-45
        daily_costs.append({
            'date': date.strftime('%Y-%m-%d'),
            'cost': round(cost, 2),
            'calls': random.randint(800, 1800)
        })

    daily_costs.reverse()  # Order from oldest to newest

    # Mock current usage
    current_usage = {
        'today_cost': round(random.uniform(20, 35), 2),
        'today_calls': random.randint(950, 1200),
        'calls_this_hour': random.randint(15, 25),
        'calls_this_minute': random.randint(0, 3),
    }

    # Mock agent-specific costs
    agent_costs = {
        'solomon': {'cost': round(random.uniform(8, 15), 2), 'calls': random.randint(400, 600)},
        'david': {'cost': round(random.uniform(6, 12), 2), 'calls': random.randint(300, 500)},
        'michael': {'cost': round(random.uniform(3, 8), 2), 'calls': random.randint(150, 300)},
        'adam': {'cost': round(random.uniform(2, 6), 2), 'calls': random.randint(100, 250)},
    }

    return daily_costs, current_usage, agent_costs

def create_cost_trend_chart(daily_costs, budget_limit):
    """Create cost trend chart with budget line"""
    df = pd.DataFrame(daily_costs)

    fig = go.Figure()

    # Add cost line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['cost'],
        mode='lines+markers',
        name='Daily Cost',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))

    # Add budget line
    fig.add_hline(
        y=budget_limit,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Daily Budget: ${budget_limit}",
        annotation_position="top right"
    )

    fig.update_layout(
        title=dict(text='Daily API Cost Trend', font=dict(size=16)),
        xaxis_title='Date',
        yaxis_title='Cost (USD)',
        hovermode='x unified',
        showlegend=True
    )

    return fig

def create_agent_cost_chart(agent_costs):
    """Create agent cost breakdown chart"""
    agents = list(agent_costs.keys())
    costs = [agent_costs[agent]['cost'] for agent in agents]
    calls = [agent_costs[agent]['calls'] for agent in agents]

    fig = go.Figure()

    # Add cost bars
    fig.add_trace(go.Bar(
        x=agents,
        y=costs,
        name='Cost (USD)',
        marker_color='lightcoral',
        yaxis='y'
    ))

    # Add calls line on secondary axis
    fig.add_trace(go.Scatter(
        x=agents,
        y=calls,
        mode='lines+markers',
        name='API Calls',
        line=dict(color='darkblue', width=3),
        marker=dict(size=10),
        yaxis='y2'
    ))

    fig.update_layout(
        title=dict(text='Agent Cost and Usage Breakdown', font=dict(size=16)),
        xaxis_title='Agent',
        yaxis=dict(title='Cost (USD)', side='left'),
        yaxis2=dict(title='API Calls', side='right', overlaying='y'),
        hovermode='x unified',
        showlegend=True
    )

    return fig

def display_cost_monitoring():
    """Display cost monitoring dashboard"""
    st.subheader("💰 Cost Monitoring & Budget Management")

    # Load cost settings
    cost_settings = get_cost_settings()
    daily_budget = cost_settings.get('daily_budget_usd', 50.0)
    warning_threshold = cost_settings.get('warning_threshold_usd', 40.0)

    # Get mock cost data
    daily_costs, current_usage, agent_costs = get_mock_cost_data()

    # Current status metrics
    st.markdown("### 📊 Today's Usage")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        today_cost = current_usage['today_cost']
        delta_color = "normal"
        if today_cost > warning_threshold:
            delta_color = "inverse"
        st.metric(
            "Today's Cost",
            f"${today_cost}",
            f"{(today_cost/daily_budget)*100:.1f}% of budget",
            delta_color=delta_color
        )

    with col2:
        st.metric("Total API Calls", current_usage['today_calls'])

    with col3:
        st.metric("Calls This Hour", current_usage['calls_this_hour'])

    with col4:
        st.metric("Calls This Minute", current_usage['calls_this_minute'])

    # Budget status
    budget_used_pct = (today_cost / daily_budget) * 100

    if budget_used_pct > 80:
        st.error(f"⚠️ Warning: {budget_used_pct:.1f}% of daily budget used!")
    elif budget_used_pct > 60:
        st.warning(f"🔶 Notice: {budget_used_pct:.1f}% of daily budget used")
    else:
        st.success(f"✅ Budget on track: {budget_used_pct:.1f}% used")

    # Progress bar for budget
    st.progress(min(budget_used_pct / 100, 1.0))

    # Cost trend chart
    st.markdown("### 📈 Cost Trends")
    cost_chart = create_cost_trend_chart(daily_costs, daily_budget)
    st.plotly_chart(cost_chart, use_container_width=True)

    # Agent breakdown
    st.markdown("### 🤖 Agent Cost Breakdown")
    agent_chart = create_agent_cost_chart(agent_costs)
    st.plotly_chart(agent_chart, use_container_width=True)

    # Cost settings display
    st.markdown("### ⚙️ Cost Management Settings")

    settings_col1, settings_col2 = st.columns(2)

    with settings_col1:
        st.markdown("**Budget Limits:**")
        st.write(f"Daily Budget: ${cost_settings.get('daily_budget_usd', 'N/A')}")
        st.write(f"Warning Threshold: ${cost_settings.get('warning_threshold_usd', 'N/A')}")
        st.write(f"Emergency Stop: ${cost_settings.get('emergency_stop_usd', 'N/A')}")

    with settings_col2:
        st.markdown("**Rate Limits:**")
        st.write(f"Max calls/minute: {cost_settings.get('max_calls_per_minute', 'N/A')}")
        st.write(f"Max calls/hour: {cost_settings.get('max_calls_per_hour', 'N/A')}")
        st.write(f"Max calls/day: {cost_settings.get('max_calls_per_day', 'N/A')}")

    # Agent cost details table
    st.markdown("### 📋 Detailed Agent Costs")
    agent_df = pd.DataFrame([
        {
            'Agent': agent.title(),
            'Cost Today ($)': data['cost'],
            'API Calls': data['calls'],
            'Avg Cost/Call ($)': round(data['cost'] / data['calls'], 4) if data['calls'] > 0 else 0
        }
        for agent, data in agent_costs.items()
    ])
    st.dataframe(agent_df, use_container_width=True)

def main():
    """Main function to run the app"""
    # Set title
    st.title("BoarderframeOS Department Browser")

    # Load department data
    data = load_department_data()
    raw_departments_data = data["boarderframeos_departments"]
    metadata = data["metadata"]

    # Extract departments from phase structure
    all_departments, all_phases = get_all_departments_from_phases(raw_departments_data)
    all_categories, _ = get_all_categories_from_phases(all_departments)

    # Display metadata in sidebar
    display_metadata(metadata)

    # Display phase overview in sidebar
    st.sidebar.header("Phase Overview")
    for phase_key, phase_data in raw_departments_data.items():
        if phase_key != "metadata" and "phase_name" in phase_data:
            dept_count = len(phase_data.get("departments", {}))
            st.sidebar.markdown(f"**{phase_data['phase_name']}**: {dept_count} departments")

    # Display search and filter functionality
    search_query, category_filter, phase_filter, sort_option = display_search(all_departments, all_categories, all_phases)

    # Filter departments based on search, category, and phase
    filtered_departments = filter_departments(all_departments, search_query, category_filter, phase_filter)

    # Sort departments based on selected option
    sorted_departments = sort_departments(filtered_departments, sort_option)

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Department Cards", "Visualizations", "Overview", "Agent Management"])

    # Tab 1: Department Cards
    with tab1:
        # Display department count
        st.markdown(f"### Displaying {len(sorted_departments)} departments")

        # Show phase breakdown for current filter
        if sorted_departments:
            phase_counts = {}
            for dept in sorted_departments.values():
                phase = dept.get("phase", "Unknown")
                phase_counts[phase] = phase_counts.get(phase, 0) + 1

            st.markdown("**Current filter shows:**")
            for phase, count in sorted(phase_counts.items()):
                st.markdown(f"- {phase}: {count} departments")

        # Display departments in cards
        display_department_cards(sorted_departments, search_query)

    # Tab 2: Visualizations
    with tab2:
        st.subheader("BoarderframeOS Visualizations")

        # Create visualization selector
        visualization = st.selectbox(
            "Select Visualization",
            ["Organization Chart", "Departments by Phase", "Departments by Category", "Agent Distribution", "Leader-Agent Ratio"]
        )

        if visualization == "Organization Chart":
            st.plotly_chart(create_org_chart(all_departments, metadata), use_container_width=True)

        elif visualization == "Departments by Phase":
            st.plotly_chart(create_phase_chart(all_departments), use_container_width=True)

        elif visualization == "Departments by Category":
            st.plotly_chart(create_category_chart(all_departments), use_container_width=True)

        elif visualization == "Agent Distribution":
            st.plotly_chart(create_agent_distribution(all_departments), use_container_width=True)

        elif visualization == "Leader-Agent Ratio":
            st.plotly_chart(create_leader_agent_ratio(all_departments), use_container_width=True)

    # Tab 3: Overview
    with tab3:
        st.subheader("BoarderframeOS Department Overview")

        # Summary statistics
        st.markdown("### Summary Statistics")

        # Create metrics in rows
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Departments", len(all_departments))

        with col2:
            st.metric("Total Leaders", sum(len(dept["leaders"]) for dept in all_departments.values()))

        with col3:
            st.metric("Total Teams", sum(len(dept["native_agents"]) for dept in all_departments.values()))

        with col4:
            # Calculate average agents per department
            avg_agents = sum(len(dept["native_agents"]) for dept in all_departments.values()) / len(all_departments)
            st.metric("Avg Agents per Dept", f"{avg_agents:.1f}")

        # Phase breakdown
        st.markdown("### Phase Breakdown")

        # Group departments by phase
        phases = {}
        for key, dept in all_departments.items():
            phase = dept.get("phase", "Unknown")
            if phase not in phases:
                phases[phase] = []
            phases[phase].append(dept["department_name"])

        # Display phases and departments
        for phase_name, depts in sorted(phases.items()):
            with st.expander(f"{phase_name} ({len(depts)} departments)"):
                for dept in sorted(depts):
                    st.write(f"- {dept}")

        # Category breakdown
        st.markdown("### Category Breakdown")

        # Group departments by category
        categories = {}
        for key, dept in all_departments.items():
            cat = dept["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(dept["department_name"])

        # Display categories and departments
        for cat, depts in sorted(categories.items()):
            with st.expander(f"{cat} ({len(depts)} departments)"):
                for dept in sorted(depts):
                    st.write(f"- {dept}")

    # Tab 4: Agent Management
    with tab4:
        display_agent_management()

    # Add footer
    st.markdown("---")
    st.markdown("<div class='footer'>BoarderframeOS Department Browser © 2025</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
