import os
import yaml
import re
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_scrapli.tasks import send_command

def save_raw_output(host, data):
    """
    Saves the raw output to a file in the 'raw_output' directory.
    """
    if not os.path.exists("raw_output"):
        os.makedirs("raw_output")
    
    filename = f"raw_output/{host}.yaml"
    
    with open(filename, "w") as file:
        formatted_data = {}

        # Device Facts
        formatted_data["Device Facts"] = data["facts"]
        
        # Interfaces
        interfaces_data = {}
        for interface, details in data["interfaces"].items():
            interfaces_data[interface] = details
        formatted_data["Interfaces"] = interfaces_data
        
        # LLDP Neighbor Details
        lldp_neighbors_data = {}
        for interface, neighbors in data["lldp_neighbors"].items():
            neighbor_details = []
            for neighbor in neighbors:
                detailed_info = get_lldp_neighbor_detail(host, interface, neighbor["hostname"])
                neighbor_details.append(detailed_info)
            lldp_neighbors_data[interface] = neighbor_details
        formatted_data["LLDP Neighbor Details"] = lldp_neighbors_data

        # Write formatted data to YAML file
        yaml.dump(formatted_data, file, default_flow_style=False)

def pull_and_save_data():
    # Initialize Nornir
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")

    try:
        # Run task to get device data
        result = nr.run(task=connection_test)

        # Save the data to files
        for host, task_result in result.items():
            if not task_result.failed:
                save_raw_output(host, task_result.result)

        print("Data saved successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

def connection_test(task):
    try:
        # Open connection and retrieve device facts, interface information
        result = task.run(task=napalm_get, getters=["facts", "interfaces"])
        device_data = result[0].result
        # Get LLDP neighbor details
        lldp_neighbors = task.run(task=napalm_get, getters=["lldp_neighbors"])
        device_data["lldp_neighbors"] = lldp_neighbors[0].result["lldp_neighbors"]
        return device_data  # Return the gathered data
    except Exception as e:
        return {"error": str(e)}

def get_lldp_neighbor_detail(host, local_interface, neighbor_host):
    # Initialize Nornir for the specific host
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    nr = nr.filter(name=host)

    try:
        # Send the command to get LLDP neighbor detail
        result = nr.run(task=send_command, command=f"show lldp neighbors {local_interface} detail")

        # Extract and return the relevant information
        raw_detail = result[host][0].result
        
        # Parse the raw detail
        parsed_detail = {
            "Local Intf": local_interface,
            "Chassis id": re.search(r"Chassis id:\s*(\S+)", raw_detail).group(1),
            "Port id": re.search(r"Port id:\s*(\S+)", raw_detail).group(1),
            "Port Description": re.search(r"Port Description:\s*(.+)", raw_detail).group(1),
            "System Name": re.search(r"System Name:\s*(\S+)", raw_detail).group(1),
            "System Description": re.search(r"System Description:\s*(.+)", raw_detail).group(1),
            "Linux Software": re.search(r"Linux Software\s*\(.*?\),\s*Version\s*(\S+)", raw_detail).group(0),
            "Version": re.search(r"Version\s*(\S+)", raw_detail).group(1)
        }

        return parsed_detail
    except Exception as e:
        return {"error": str(e)}

# Execute the function to pull and save data
if __name__ == "__main__":
    pull_and_save_data()
