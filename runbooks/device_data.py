import os
import yaml
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir_scrapli.tasks import send_command

def save_device_data(host, device_data):
    """
    Saves device data to a YAML file.
    """
    folder_name = "device_data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    filename = f"{folder_name}/{host}_data.yaml"
    
    with open(filename, "w") as file:
        yaml.dump(device_data, file, default_flow_style=False)

def get_device_data(host):
    """
    Retrieves device data using Napalm for facts and interfaces, and Scrapli for additional details.
    """
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    nr = nr.filter(name=host)

    try:
        # Initialize device_data as an empty dictionary
        device_data = {}

        # Retrieve facts using Napalm
        result = nr.run(task=napalm_get, getters=["facts"])
        facts = result[host][0].result["facts"]  # Ensure we're working with 'facts'
        
        # Remove unnecessary keys from facts
        facts.pop("interface_list", None)
        facts.pop("model", None)

        # Add facts to device_data
        device_data["facts"] = facts

        # Retrieve interfaces using Napalm
        interfaces_result = nr.run(task=napalm_get, getters=["interfaces"])
        napalm_interfaces = interfaces_result[host][0].result["interfaces"]
        
        # Retrieve additional details using Scrapli
        scrapli_details = {}
        for interface in napalm_interfaces.keys():
            command_result = nr.run(task=send_command, command=f"show interface {interface}")
            raw_output = command_result[host][0].result
            scrapli_details[interface] = parse_scrapli_output(raw_output)
        
        # Combine Napalm and Scrapli interface details
        combined_interfaces = {}
        for interface, napalm_detail in napalm_interfaces.items():
            combined_interfaces[interface] = {
                **napalm_detail,
                **scrapli_details.get(interface, {})
            }
        
        # Remove 'description' from interfaces
        for interface_detail in combined_interfaces.values():
            if "description" in interface_detail:
                del interface_detail["description"]
        
        # Add combined interface details under the 'interfaces' key
        device_data["interfaces"] = combined_interfaces
        
        return device_data
    except Exception as e:
        print(f"Failed to retrieve device data for {host}: {str(e)}")


def parse_scrapli_output(output):
    """
    Parses Scrapli output to extract additional details.
    """
    parsed_details = {}
    lines = output.split("\n")
    for line in lines:
        if "Hardware" in line:
            parsed_details["Hardware"] = line.strip()
    return parsed_details

def main():
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    try:
        for host in nr.inventory.hosts.keys():
            device_data = get_device_data(host)
            if device_data:
                save_device_data(host, device_data)
                print(f"Data for {host} saved successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
