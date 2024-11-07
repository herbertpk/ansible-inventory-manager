import os
import yaml
from collections import defaultdict
import csv


def save_analysis_to_csv(analysis_results, output_csv="inventory_analysis.csv"):
    """Save the analysis results to a CSV file."""
    # Define the CSV headers
    headers = [
        "Host", 
        "Groups", 
        "Duplicated Variables", 
        "Inconsistent Variables", 
        "Duplicated Host", 
        "Missing File in host_vars", 
        "Orphaned Host Var"
    ]

    # Open the CSV file for writing
    with open(output_csv, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write the header row
        writer.writerow(headers)
        
        # Write the data rows
        for host, data in analysis_results.items():
            writer.writerow([
                host,
                data.get("Groups", "N/A"),
                data.get("Duplicated Variables", "N/A"),
                data.get("Inconsistent Variables", "N/A"),
                data.get("Duplicated Host", "N/A"),
                data.get("Missing File in host_vars", "N/A"),
                data.get("Orphaned Host Var", "No")
            ])

    print(f"Analysis results saved to {output_csv}")


def load_yaml_file(file_path):
    """Loads a YAML file and returns its content."""
    with open(file_path, 'r') as file:
        try:
            return yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            print(f"Error loading {file_path}: {exc}")
            return {}

def load_all_vars(dir_path):
    """Loads all YAML files from a directory and returns a dictionary with their content."""
    vars_data = {}
    for file_name in os.listdir(dir_path):
        if file_name.endswith('.yaml') or file_name.endswith('.yml'):
            full_path = os.path.join(dir_path, file_name)
            vars_data[file_name] = load_yaml_file(full_path)
    return vars_data

def check_duplicate_vars(group_vars, host_vars):
    """Checks for duplicate variables between group_vars and host_vars."""
    duplicates = defaultdict(list)
    for group_file, group_data in group_vars.items():
        for host_file, host_data in host_vars.items():
            host_name = os.path.splitext(host_file)[0]  # Strip the .yaml/.yml extension
            for var in group_data:
                if var in host_data:
                    duplicates[var].append((group_file, host_name))
    return duplicates

def check_inconsistent_values(group_vars, host_vars):
    """Checks for inconsistencies in variable values between group_vars and host_vars."""
    inconsistencies = defaultdict(list)
    for group_file, group_data in group_vars.items():
        for host_file, host_data in host_vars.items():
            host_name = os.path.splitext(host_file)[0]  # Strip the .yaml/.yml extension
            for var, group_value in group_data.items():
                if var in host_data and host_data[var] != group_value:
                    inconsistencies[var].append({
                        "group_file": group_file,
                        "host_file": host_name,
                        "group_value": group_value,
                        "host_value": host_data[var]
                    })
    return inconsistencies

def find_duplicates(groups):
    """Identify hosts that appear multiple times within the same group."""
    duplicated_hosts = defaultdict(list)

    for group, hosts in groups.items():
        # Count each host occurrence within the group
        host_counts = Counter(hosts)
        for host, count in host_counts.items():
            if count > 1:  # Host appears more than once in this group
                duplicated_hosts[host].append(group)

    # Filter to only include hosts with duplicates within groups
    duplicated_hosts = {host: group_list for host, group_list in duplicated_hosts.items() if group_list}

    return duplicated_hosts

def find_inconsistent_hosts(host_groups, inventory_base_path):
    """Identify hosts that are in hosts.ini but don't have a corresponding file in host_vars."""
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")
    inconsistent_hosts = []

    for host in host_groups:
        # Check for the existence of corresponding .yaml or .yml file in host_vars
        host_file_yaml = os.path.join(host_vars_dir, f"{host}.yaml")
        host_file_yml = os.path.join(host_vars_dir, f"{host}.yml")
        
        if not (os.path.exists(host_file_yaml) or os.path.exists(host_file_yml)):
            inconsistent_hosts.append(host)

    return inconsistent_hosts

def find_orphaned_host_vars(host_groups, inventory_base_path):
    """Identify hosts that have files in host_vars but are not defined in hosts.ini."""
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")
    defined_hosts = set(host_groups.keys())  # Hosts defined in hosts.ini
    orphaned_hosts = []

    # Iterate over files in host_vars to find hosts without entries in hosts.ini
    for file_name in os.listdir(host_vars_dir):
        if file_name.endswith(('.yaml', '.yml')):
            host_name = os.path.splitext(file_name)[0]  # Remove the extension
            if host_name not in defined_hosts:
                orphaned_hosts.append(host_name)

    return orphaned_hosts

def parse_hosts_ini(inventory_base_path):
    """Parse the hosts.ini file manually, allowing duplicates and only including hosts with files in host_vars."""
    hosts_ini_path = os.path.join(inventory_base_path, "hosts")
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")

    hosts = defaultdict(dict)
    groups = defaultdict(list)

    current_group = None

    with open(hosts_ini_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                # Skip comments or empty lines
                continue
            
            # Detect a new group section
            if line.startswith("[") and line.endswith("]"):
                current_group = line[1:-1].strip()
                groups[current_group] = []
            elif current_group:
                # Process each host entry, allowing duplicates
                if ' ' in line:  # If host has inline variables
                    host_name = line.split()[0].strip()
                else:
                    host_name = line
                
                # Check if a corresponding host_vars file exists
                host_file_yaml = os.path.join(host_vars_dir, f"{host_name}.yaml")
                host_file_yml = os.path.join(host_vars_dir, f"{host_name}.yml")

                # Only add host if a corresponding file is found in host_vars
                if os.path.exists(host_file_yaml) or os.path.exists(host_file_yml):
                    groups[current_group].append(host_name)
                    hosts[host_name].setdefault('groups', []).append(current_group)

    return hosts, groups


def analyze_inventory(inventory_base_path,save_csv=False):
    """Analyze the inventory for each host and return duplicates, inconsistencies, and missing files in a dictionary."""
    # Parse the hosts.ini file to get host-group associations
    hosts, groups = parse_hosts_ini(inventory_base_path)

    # Load group_vars and host_vars directories
    group_vars_dir = os.path.join(inventory_base_path, "group_vars")
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")
    group_vars = load_all_vars(group_vars_dir)
    host_vars = load_all_vars(host_vars_dir)

    # Check for duplicate and inconsistent variables
    duplicate_vars = check_duplicate_vars(group_vars, host_vars)
    inconsistent_values = check_inconsistent_values(group_vars, host_vars)

    # Prepare the results dictionary
    analysis_results = {}
    duplicated_hosts = {host: groups for host, groups in hosts.items() if len(groups['groups']) > 1}
    missing_files = []
    orphaned_files = []

    # Check for missing files in host_vars
    for host in hosts:
        host_file_yaml = os.path.join(host_vars_dir, f"{host}.yaml")
        host_file_yml = os.path.join(host_vars_dir, f"{host}.yml")
        
        if not (os.path.exists(host_file_yaml) or os.path.exists(host_file_yml)):
            missing_files.append(host)

    # Check for orphaned files in host_vars (files without corresponding entry in hosts.ini)
    defined_hosts = set(hosts.keys())
    for file_name in os.listdir(host_vars_dir):
        if file_name.endswith(('.yaml', '.yml')):
            host_name = os.path.splitext(file_name)[0]  # Remove the extension
            if host_name not in defined_hosts:
                orphaned_files.append(host_name)

    # Analyze and collect duplicates and inconsistencies for each host
    for host, details in hosts.items():
        related_groups = details['groups']
        duplicated_vars = []
        inconsistent_vars = []

        # Collect duplicates specific to this host
        for var, files in duplicate_vars.items():
            for group_file, host_file in files:
                if host_file == host:
                    duplicated_vars.append(f"{var} (in {group_file} and {host_file})")

        # Collect inconsistencies specific to this host
        for var, conflicts in inconsistent_values.items():
            for conflict in conflicts:
                if conflict["host_file"] == host:
                    inconsistent_vars.append(
                        f"{var} ({conflict['group_file']} value = {conflict['group_value']}, "
                        f"{host} value = {conflict['host_value']})"
                    )

        # Add results for this host to the dictionary
        analysis_results[host] = {
            "Groups": ", ".join(related_groups),
            "Duplicated Variables": "; ".join(duplicated_vars) if duplicated_vars else "No duplicated variables",
            "Inconsistent Variables": "; ".join(inconsistent_vars) if inconsistent_vars else "No inconsistent variables",
            "Duplicated Host": ", ".join(duplicated_hosts[host]['groups']) if host in duplicated_hosts else "No duplication in groups",
            "Missing File in host_vars": "Yes" if host in missing_files else "No",
            "Orphaned Host Var": "No"
        }

    # Add orphaned hosts to the analysis_results dictionary
    for orphaned_host in orphaned_files:
        analysis_results[orphaned_host] = {
            "Groups": "No group assigned",
            "Duplicated Variables": "N/A",
            "Inconsistent Variables": "N/A",
            "Duplicated Host": "No duplication in groups",
            "Missing File in host_vars": "No",
            "Orphaned Host Var": "Yes"
        }
        

    if save_csv:
        save_analysis_to_csv(analysis_results)  
        
    return analysis_results

    


