#!/usr/bin/env python3
"""
Fix Flask routes indentation
"""


def fix_flask_routes():
    """Fix the indentation of Flask routes"""

    with open("corporate_headquarters.py", "r") as f:
        content = f.read()

    # Find the Flask app creation
    flask_start = content.find("app = Flask(__name__)")
    if flask_start == -1:
        print("Could not find Flask app creation")
        return False

    # Find the indentation level
    line_start = content.rfind("\n", 0, flask_start) + 1
    indent = " " * (flask_start - line_start - len("app = Flask(__name__)".split()[0]))

    print(f"Found Flask app with indent level: {len(indent)} spaces")

    # Find the metrics routes
    metrics_route_start = content.find("@app.route('/api/metrics')")
    if metrics_route_start != -1:
        # Find where the routes end
        route_end = content.find("\n@app.route('/')", metrics_route_start)
        if route_end == -1:
            route_end = content.find("\nif __name__", metrics_route_start)

        if route_end != -1:
            # Extract the routes
            routes_text = content[metrics_route_start:route_end]

            # Fix the indentation
            fixed_routes = []
            for line in routes_text.split("\n"):
                if line.strip():  # Skip empty lines
                    fixed_routes.append(indent + line.lstrip())
                else:
                    fixed_routes.append("")

            fixed_routes_text = "\n".join(fixed_routes)

            # Replace in content
            content = (
                content[:metrics_route_start] + fixed_routes_text + content[route_end:]
            )

            print("✓ Fixed routes indentation")

    # Save the file
    with open("corporate_headquarters.py", "w") as f:
        f.write(content)

    return True


if __name__ == "__main__":
    if fix_flask_routes():
        print("✅ Successfully fixed Flask routes indentation")
    else:
        print("❌ Failed to fix routes")
