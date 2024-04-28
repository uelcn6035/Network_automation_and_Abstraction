# app.py

from flask import Flask, render_template
import os
import json

app = Flask(__name__)

@app.route("/")
def index():
    try:
        # Read the saved data from files
        device_data = read_device_data()

        # Render template with collected data
        return render_template("dashboard.html", data=device_data)

    except Exception as e:
        return f"An error occurred: {e}"

def read_device_data():
    device_data = {}
    directory = "/root/cn6000_automation/runbooks/web_gui/raw_output"  # New directory path
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            host = filename.split(".")[0]
            with open(os.path.join(directory, filename), "r") as file:
                device_data[host] = parse_device_data(file.readlines())
    return device_data

def parse_device_data(lines):
    device_data = {}
    section = None
    for line in lines:
        if line.strip().startswith("Device Facts"):
            section = "facts"
            device_data[section] = {}
        elif line.strip().startswith("Interfaces"):
            section = "interfaces"
            device_data[section] = {}
        elif line.strip().startswith("LLDP Neighbors"):
            section = "lldp_neighbors"
            device_data[section] = {}
        elif line.strip().startswith("Device Configuration"):
            section = "config"
            device_data[section] = ""
        else:
            if section == "config":
                device_data[section] += line.strip()
            else:
                key, value = line.strip().split(":")
                device_data[section][key.strip()] = value.strip()
    return device_data

if __name__ == "__main__":
    app.run(debug=True)
