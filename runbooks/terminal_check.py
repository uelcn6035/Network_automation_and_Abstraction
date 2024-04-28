import re
from nornir import InitNornir
from nornir_scrapli.tasks import send_command

def parse_lldp_output(output):
    # Define the regular expression pattern to match each line of the output
    pattern = r"(\S+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)"
    # Initialize an empty list to store the parsed data
    lldp_neighbors = []
    # Iterate over each line of the output
    for line in output.splitlines():
        # Match the line against the pattern
        match = re.match(pattern, line)
        if match:
            # Extract the matched groups and create a dictionary
            neighbor_info = {
                "Device ID": match.group(1),
                "Local Intf": match.group(2),
                "Hold-time": int(match.group(3)),
                "Capability": match.group(4),
                "Port ID": match.group(5)
            }
            # Append the dictionary to the list
            lldp_neighbors.append(neighbor_info)
    return lldp_neighbors

def main():
    # Initialize Nornir
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")

    # Run the task
    result = nr.run(
        task=send_command, command="show lldp neighbor"
    )

    # Process the output
    for host, data in result.items():
        print(f"=== {host} ===")
        # Parse the LLDP output
        lldp_output = data.result
        lldp_neighbors = parse_lldp_output(lldp_output)
        # Print the parsed LLDP neighbors
        for neighbor in lldp_neighbors:
            print(neighbor)

if __name__ == "__main__":
    main()
