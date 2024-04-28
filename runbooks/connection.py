# connection.py
from nornir import InitNornir
from nornir_napalm.plugins.tasks import napalm_get
from nornir.core.exceptions import NornirExecutionError
from nornir_napalm.plugins.tasks import napalm_get
from nornir.core.exceptions import NornirExecutionError

def connection_test(task):
    try:
        # Open connection
        task.run(task=napalm_get, getters=["get_facts"])

        # Print device name
        print(f"Connected to {task.host.name}")

    except Exception as e:
        print(f"Unable to connect to {task.host.name}")

# Initialize Nornir and run the task
if __name__ == "__main__":
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    result = nr.run(task=connection_test)
