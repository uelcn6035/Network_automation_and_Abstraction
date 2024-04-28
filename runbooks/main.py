from nornir import InitNornir
from datetime import datetime
from connection import connection_test
from backup import backup_current_configs
from configs_update import load_variables, apply_ipsec_vpn
from rollback_config import rollback_configs
from nornir_utils.plugins.functions import print_result
from termcolor import colored
import warnings
import time
import glob
import os

# Ignore Scrapli Privilege_level UserWarning for admin
warnings.filterwarnings("ignore", category=UserWarning)

def main():
    start_time = time.time()  # Record the start time

    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    
    now = datetime.now()
    date_time = now.strftime("%Y%m%d_%H%M%S")
    backup_folder = f"backup_configs/{date_time}"
    
    connection_result = nr.run(task=connection_test)
    
    if not connection_result.failed:
        print(colored("Connection Successful - Now Running Backup", 'green'))  # Moved this line here
        print("\n")
        backup_result = nr.run(task=backup_current_configs, backup_folder=backup_folder)
        if backup_result.failed:
            print(colored("Backup Failed - Operation Aborted. Review Log and Try Again.", 'red'))
            print_result(backup_result)
            return
        
        print("Backup Statuses:")
        print_result(backup_result)
        print("\n")  # Added an empty line after backup output
    
        time.sleep(1)  # Pause for 2 seconds before applying IPSEC
        print(colored("Backup Successful - Pushing Configurations:", 'green'))
        results = nr.run(task=load_variables, nr=nr)

        if results.failed:
            print(colored("Error occurred while loading variables or applying configurations. Operation stopped.", 'red'))
            print_result(results)
            
            backup_folders = glob.glob("/root/cn6000_automation/runbooks/backup_configs/*")
            
            if not backup_folders:
                print(colored("No backup folders found.", 'red'))
                return
            print("\n\n")
            backup_folder = max(backup_folders, key=os.path.getctime)
            print(colored("CRITICAL >>>>>>>>>>>", 'red') + colored(f" Rolling back from latest backup folder: {backup_folder}", 'yellow'))
            rollback_results = nr.run(task=rollback_configs, backup_folder=backup_folder)
            print("\n\n")
            print(colored("Rollback was successful. Please review the log file for details.", 'green'))
            print("\n\n")
        else:
            print("\n\n")
            time.sleep(1)  # Pause for 2 seconds
            print(colored(" Configuration successful to all devices.", 'green'))
            print("\n")
            print("Configured Technologies:")
            technologies = {
                "VLAN": "",
                "VXLAN": "",
                "DHCP": "",
                "ETHERCHANNEL": "",
                "HSRP": "",
                "OSPF": "",
                "IPSEC": "",
                "LLDP": "",
                "RAOS": ""
            }
            for tech in technologies.keys():
                if tech in results and results[tech].failed:
                    technologies[tech] = colored("Failed", 'red')
                else:
                    technologies[tech] = colored("complete", 'green')

            for tech, status in technologies.items():
                print(f"{tech}: {status}")
            print("\n")
            print(colored("You may now perform the ping test.", 'yellow'))  # Instruction in yellow color

            end_time = time.time()  # Record the end time
            elapsed_time = end_time - start_time  # Calculate the elapsed time
            print(colored(f"\nTotal running time: {elapsed_time} seconds\n", 'green', attrs=['bold']))  # Print the elapsed time in green and bold

    else:
        print(colored("Connection test failed. Configuration aborted.", 'red'))

if __name__ == "__main__":
    main()
