import os
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
import json

def save_raw_output(host, data):
    """
    Saves the raw output to a file in the 'raw_output' directory.
    """
    if not os.path.exists("raw_output"):
        os.makedirs("raw_output")
    
    filename = f"raw_output/{host}.txt"
    
    with open(filename, "w") as file:
        # Write device facts
        file.write("Device Facts:\n")
        for key, value in data["facts"].items():
            file.write(f"{key}: {value}\n")
        file.write("\n")

        # Write interfaces information
        file.write("Interfaces:\n")
        for interface, details in data["interfaces"].items():
            file.write(f"Interface: {interface}\n")
            for key, value in details.items():
                file.write(f"  {key}: {value}\n")
            file.write("\n")
        file.write("\n")

        # Write LLDP neighbors
        file.write("LLDP Neighbors:\n")
        for interface, neighbors in data["lldp_neighbors"].items():
            file.write(f"{interface}:\n")
            for neighbor in neighbors:
                file.write(f"  {neighbor['port']} ({neighbor['hostname']})\n")
            file.write("\n")

        # Write user information
        file.write("Users:\n")
        for user, details in data["users"].items():
            file.write(f"User: {user}\n")
            for key, value in details.items():
                file.write(f"  {key}: {value}\n")
            file.write("\n")

        # Write network instances information
        file.write("Network Instances:\n")
        for instance, details in data["network_instances"].items():
            file.write(f"Network Instance: {instance}\n")
            for key, value in details.items():
                file.write(f"  {key}: {value}\n")
            file.write("\n")

        # Write device configuration
        file.write("Device Configuration:\n")
        if isinstance(data["config"], dict):
            file.write(json.dumps(data["config"], indent=4))  # Convert dictionary to string with indentation
        else:
            file.write(data["config"])


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
        # Open connection and retrieve device facts, interfaces, LLDP neighbors, users, network instances, and configuration
        result = task.run(task=napalm_get, getters=["facts", "interfaces", "lldp_neighbors", "users", "network_instances", "config"])
        return result[0].result  # Return the gathered data
    except Exception as e:
        return {"error": str(e)}

# Execute the function to pull and save data
if __name__ == "__main__":
    pull_and_save_data()
