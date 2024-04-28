# Import modules
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_configure
from nornir_utils.plugins.functions import print_result
import logging

# Set up logging
logging.basicConfig(filename='network_automation.log', level=logging.INFO)

def replace_configs(task):
    try:
        # Load and apply configuration
        task.run(task=napalm_configure, filename=f"/root/cn6000_automation/runbooks/backup_configs/{task.host}.txt", replace=True)
        
    except Exception as e:
        logging.error(f"Error applying configuration: {e}")
        print(f"Error applying configuration: {e}")
        print("Rolling back changes...")
        task.run(task=napalm_configure, filename=f"/root/cn6000_automation/runbooks/backup_configs/{task.host}.txt", replace=True)

# Initialize Nornir and run task
nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
results = nr.run(task=replace_configs)

# Print and log results
print_result(results)
logging.info(results)



