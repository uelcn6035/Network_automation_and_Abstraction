import os
from nornir import InitNornir
from nornir_scrapli.tasks import send_configs_from_file
from nornir_utils.plugins.functions import print_result

def send_config(task):
    # Construct the file path using the device name
    file_path = f"/root/cn6000_automation/runbooks/backup_configs/20240407_032749/{task.host.name}.txt"
    
    # Check if the configuration file exists
    if os.path.isfile(file_path):
        # If it exists, print a message
        print(f"Sending configurations to {task.host.name}...")
        
        # Send the configurations from the file
        result = task.run(task=send_configs_from_file, file=file_path)
        
        # Print a message after sending the configurations
        print(f"Finished sending configurations to {task.host.name}.")
        
        return result

# Initialize Nornir and run the task
nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
results = nr.run(task=send_config)

# Print the results from the devices with configurations
for result in results.values():
    if result.result:
        print_result(result)
