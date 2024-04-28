import os
from flask import Flask, render_template, jsonify, request
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get

app = Flask(__name__)

@app.route("/")
def index():
    try:
        # Initialize Nornir and run task
        nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
        result = nr.run(task=connection_test)
        
        # Extract device data from the MultiResult object
        device_data = {}
        for host, task_result in result.items():
            if not task_result.failed:
                device_data[host] = task_result.result

        # Render template with collected data
        return render_template("dashboard.html", data=device_data)

    except Exception as e:
        return f"An error occurred: {e}"

@app.route("/lldp_neighbors")
def get_lldp_neighbors():
    try:
        # Get the host from the request
        host = request.args.get("host")

        # Initialize Nornir and run task to get LLDP neighbors
        nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
        result = nr.run(task=query_lldp_neighbors, host=host)

        # Extract LLDP neighbors data
        lldp_neighbors = result[host].result

        # Return LLDP neighbors data as JSON
        return jsonify(lldp_neighbors)

    except Exception as e:
        return jsonify({"error": str(e)})

def query_lldp_neighbors(task):
    try:
        # Query LLDP neighbors
        result = task.run(task=napalm_get, getters=["lldp_neighbors"])

        # Extract LLDP neighbors data
        lldp_neighbors = result[0].result.get("lldp_neighbors", {})

        return lldp_neighbors

    except Exception as e:
        return {"error": str(e)}

def connection_test(task):
    try:
        # Open connection and retrieve device facts and interface information
        result = task.run(task=napalm_get, getters=["facts", "interfaces"])

        # Extract data from the result object
        facts = result[0].result.get("facts", {})
        interfaces = result[0].result.get("interfaces", {})

        # Calculate the counts of up and down interfaces
        up_count = sum(1 for interface in interfaces.values() if interface.get("is_up"))
        down_count = len(interfaces) - up_count

        # Calculate average interface speed
        total_speed = sum(interface.get("speed", 0) for interface in interfaces.values())
        average_speed = total_speed / len(interfaces) if interfaces else 0

        # Combine all collected data
        collected_data = {
            "hostname": facts.get("hostname", ""),
            "vendor": facts.get("vendor", ""),
            "model": facts.get("model", ""),
            "up_count": up_count,
            "down_count": down_count,
            "uptime": facts.get("uptime", ""),
            "os_version": facts.get("os_version", ""),
            "serial_number": facts.get("serial_number", ""),
            "fqdn": facts.get("fqdn", ""),
            "average_speed": average_speed  # Add average interface speed to collected data
        }

        return collected_data

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
