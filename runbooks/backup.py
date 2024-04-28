import pathlib
from napalm import get_network_driver
from nornir.core.task import Result

def backup_current_configs(task, backup_folder):
    device = None
    try:
        # Connect to the device using NAPALM
        driver = get_network_driver(task.host.platform)
        device = driver(hostname=task.host.hostname, username=task.host.username, password=task.host.password)
        device.open()
        
        # Get the running configuration
        running_config = device.get_config(retrieve='running')['running']

        # Create backup folder if it doesn't exist
        pathlib.Path(backup_folder).mkdir(parents=True, exist_ok=True)

        # Write the configuration to a file
        with open(f"{backup_folder}/{task.host}.txt", "w") as f:
            f.write(running_config)

        return Result(host=task.host, changed=True)
    except Exception as e:
        error_msg = f"Backup failed for {task.host.name}. Error: {str(e)}"
        print(error_msg)
        with open("backup_errors.log", "a") as log_file:
            log_file.write(error_msg + "\n")
        return Result(host=task.host, failed=True, exception=e)
    finally:
        # Ensure the connection is closed
        if device is not None:
            device.close()
