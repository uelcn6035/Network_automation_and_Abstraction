import os
from flask import Flask, render_template, jsonify, request
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
import yaml

app = Flask(__name__)

def is_valid_device(serial_number, vendor, fqdn):
    device_data_dir = '/root/cn6000_automation/runbooks/device_data'  # Directory where the device data files are stored

    # Iterate over all files in the device data directory
    for filename in os.listdir(device_data_dir):
        if filename.endswith('.yaml'):  # Assuming the device data files are YAML
            with open(os.path.join(device_data_dir, filename)) as file:
                device_data = yaml.safe_load(file)

                # Check if the serial number, vendor, and FQDN match this device
                if (device_data.get('facts', {}).get('serial_number') == serial_number and 
                    device_data.get('facts', {}).get('vendor') == vendor and 
                    device_data.get('facts', {}).get('fqdn') == fqdn):
                    return True

    return False

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
    
@app.route('/validate_device', methods=['GET', 'POST'])
def validate_device():
    if request.method == 'POST':
        serial_number = request.form.get('serial_number')
        vendor = request.form.get('vendor')
        fqdn = request.form.get('fqdn')

        if is_valid_device(serial_number, vendor, fqdn):
            validation_result = 'This is a valid device'
            validation_color = 'green'
        else:
            validation_result = 'Unauthorized Device - Port will be err-disabled if connected'
            validation_color = 'red'

        return render_template('validation_result.html', result=validation_result, color=validation_color)

    return render_template('validate_device.html')

@app.route('/active_config', methods=['GET'])
def active_config():
    try:
        # Initialize Nornir
        nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")

        # Run task to get running config on all hosts
        result = nr.run(task=napalm_get, getters=["config"])

        # Extract running config data for each host and convert to YAML
        running_configs = {host: yaml.dump(task_result.result['config']['running']) for host, task_result in result.items() if not task_result.failed}

        # Render template with collected data
        return render_template("active_config.html", data=running_configs)

    except Exception as e:
        return jsonify({"error": str(e)})


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
