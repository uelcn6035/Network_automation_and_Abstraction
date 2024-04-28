# rollback_config.py

import os
import glob
from nornir import InitNornir
from nornir_scrapli.tasks import send_configs_from_file
from nornir_utils.plugins.functions import print_result

def rollback_configs(task):
    # Get the list of backup folders
    backup_folders = glob.glob("/root/cn6000_automation/runbooks/backup_configs/*")
    
    # Check if backup_folders is empty
    if not backup_folders:
        print(f"No backup folders found.")
        return

    # Sort the folders by creation time and get the earliest one
    backup_folder = min(backup_folders, key=os.path.getctime)
    
    # Construct the file path using the device name and backup folder
    file_path = f"{backup_folder}/{task.host.name}.txt"
    
    # Check if the configuration file exists
    if os.path.isfile(file_path):
        # If it exists, print a message
        print(f"Rolling back configurations on {task.host.name}...")
        
        # Send the configurations from the file
        result = task.run(task=send_configs_from_file, file=file_path)
        
        return result
    else:
        print(f"No backup configurations found for {task.host.name}.")

def main():
    # Initialize Nornir
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    
    # Run rollback
    rollback_results = nr.run(task=rollback_configs)

if __name__ == "__main__":
    main()
