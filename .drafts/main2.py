from nornir import InitNornir
from nornir_scrapli.tasks import send_configs
from nornir_jinja2.plugins.tasks import template_file
from nornir_utils.plugins.tasks.data import load_yaml
from tqdm import tqdm

nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")

def load_variables(task, nr):
    data = task.run(
        task=load_yaml, 
        file=f"/root/cn6000_automation/templates/host_variables/{task.host}.yaml"
    )
    task.host["cn6000_facts"] = data.result
    test_templates(task, nr)


def test_templates(task, nr):
    # Apply int_config.j2 and ospf_&_static.j2 templates first
    first_templates = ["int_&_roas_config.j2", "ospf_&_static.j2"]
    for template_name in tqdm(first_templates, desc="Applying base int_&_raos configs"):
        rendered = task.run(
            task=template_file, 
            template=template_name, 
            path="/root/cn6000_automation/templates/"
        )
        configuration = rendered.result.splitlines()
        task.run(task=send_configs, configs=configuration)

    # Apply other templates as before
    templates = {
        "vlan_&_vrrp.j2": [host for host in nr.inventory.hosts.values() if "load_balancing" in host.groups or "leaf_switches" in host.groups],
        "etherchannel.j2": [host for host in nr.inventory.hosts.values() if "load_balancing" in host.groups],
        "vxlan_config.j2": [host for host in nr.inventory.hosts.values() if "leaf_switches" in host.groups],
        "dhcp_pool.j2": [host for host in nr.inventory.hosts.values() if "dhcp_server" in host.groups],
    }

    for template_name, hosts in templates.items():
        for host in tqdm(hosts, desc=f"Applying {template_name}"):
            rendered = task.run(
                task=template_file, 
                template=template_name, 
                path="/root/cn6000_automation/templates/"
            )
            configuration = rendered.result.splitlines()
            # Ensure the configuration list is not empty before sending it
            if configuration:
                task.run(task=send_configs, configs=configuration)
        print(f"\nDevices successfully configured with {template_name[:-3]} as filtered.\n")

    print("\nDEVICES IN ALL SITES SUCCESSFULLY CONFIGURED.\n")

def apply_ipsec_vpn(task, nr):
    # List of hosts to apply the IPsec configuration to
    ipsec_hosts = ["SPINE-HQ-1-5", "SPINE-HQ-2-6", "C-LAG-1-4", "C-TOK-1-3"]

    # Check if the current host is in the list of IPsec hosts
    if task.host.name in ipsec_hosts:
        rendered = task.run(
            task=template_file, 
            template="ipsec_vpn.j2", 
            path="/root/cn6000_automation/templates/"
        )
        configuration = rendered.result.splitlines()
        # Ensure the configuration list is not empty before sending it
        if configuration:
            task.run(task=send_configs, configs=configuration)
        print(f"\nSite to Site traffic encryption implemented successfully on {task.host.name}.\n")

if __name__ == "__main__":
    # Load variables and test templates
    nr.run(task=load_variables, nr=nr)
    nr.run(task=test_templates, nr=nr)
    # Apply IPsec VPN
    nr.run(task=apply_ipsec_vpn, nr=nr)
