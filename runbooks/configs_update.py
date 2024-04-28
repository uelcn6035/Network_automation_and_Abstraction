from nornir import InitNornir
from nornir_scrapli.tasks import send_configs
from nornir_jinja2.plugins.tasks import template_file
from nornir_utils.plugins.tasks.data import load_yaml
from nornir_utils.plugins.functions import print_result
from tqdm import tqdm

def load_variables(task, nr):
    data = task.run(
        task=load_yaml, 
        file=f"/root/cn6000_automation/templates/host_variables/{task.host}.yaml"
    )
    task.host["cn6000_facts"] = data.result
    test_templates(task, nr)
    return data

def test_templates(task, nr):
    # Apply int_config.j2 and ospf_&_static.j2 templates first
    first_templates = ["int_&_roas_config.j2", "ospf_&_static.j2", "snmp.j2",]
    results = []
    for template_name in tqdm(first_templates, desc="Applying base int_&_raos configs"):
        rendered = task.run(
            task=template_file, 
            template=template_name, 
            path="/root/cn6000_automation/templates/"
        )
        configuration = rendered.result.splitlines()
        result = task.run(task=send_configs, configs=configuration)
        results.append(result)

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
                result = task.run(task=send_configs, configs=configuration)
                results.append(result)

    apply_ipsec_vpn(task, nr)

def apply_ipsec_vpn(task, nr):
    # List of hosts to apply the IPsec configuration to
    ipsec_hosts = ["SPINE-HQ-1-5", "SPINE-HQ-2-6", "C-LAG-1-4", "C-TOK-1-3"]
    results = []
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
            result = task.run(task=send_configs, configs=configuration)
            results.append(result)
    return results

def main():
    nr = InitNornir(config_file="/root/cn6000_automation/inventory/config.yaml")
    results = nr.run(task=load_variables, nr=nr)
    if __name__ == "__main__":
        for result in results.values():
            print_result(result)

if __name__ == "__main__":
    main()
