import os
import yaml

def load_yaml_file(file_path):
    """Loads a YAML file and returns its content."""
    with open(file_path, 'r') as file:
        try:
            return yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            print(f"Error loading {file_path}: {exc}")
            return {}

def save_yaml_file(file_path, data):
    """Saves data to a YAML file."""
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file)

def clean_hosts(inventory_base_path, analysis_results):
    """Remove duplicated hosts in groups and hosts without corresponding files in host_vars."""
    hosts_ini_path = os.path.join(inventory_base_path, "hosts")
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")

    # Step 1: Read the original hosts.ini file
    with open(hosts_ini_path, 'r') as file:
        lines = file.readlines()

    # Step 2: Open hosts.ini for writing (after cleaning)
    with open(hosts_ini_path, 'w') as file:
        for line in lines:
            # Skip comments or empty lines
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or stripped_line.startswith("["):
                file.write(line)
                continue

            # Extract the host name from the line
            host_name = stripped_line.split()[0]

            # Check for hosts to be removed
            if host_name in analysis_results:
                if analysis_results[host_name]["Duplicated Host"] != "No duplication in groups":
                    # Skip writing this line to remove duplicates
                    print(f"Removing duplicated host '{host_name}' from group definitions in hosts.ini")
                    continue
                if analysis_results[host_name]["Missing File in host_vars"] == "Yes":
                    # Skip writing this line to remove missing file entries
                    print(f"Removing host '{host_name}' without corresponding file in host_vars")
                    continue

            # Write non-duplicated and valid hosts to the cleaned hosts.ini
            file.write(line)

    print(f"Completed cleaning hosts.ini for duplicated and inconsistent entries.")

def clean_host_vars(inventory_base_path, analysis_results):
    """Remove duplicated and inconsistent variables from host_vars, handling case-insensitive variable names."""
    host_vars_dir = os.path.join(inventory_base_path, "host_vars")

    for host, analysis in analysis_results.items():
        host_file_path = os.path.join(host_vars_dir, f"{host}.yml")
        
        try:
            # Load the host's YAML file data
            host_data = load_yaml_file(host_file_path)
        except FileNotFoundError:
            print(f"Warning: Host file '{host_file_path}' not found. Skipping this host.")
            continue

        # Create a case-insensitive dictionary for host_data to match variables in any case
        host_data_ci = {key.lower(): key for key in host_data}  # Maps lowercase to original case

        # Remove duplicated variables
        if analysis["Duplicated Variables"] != "No duplicated variables":
            duplicated_vars = [var.split(" (")[0].lower() for var in analysis["Duplicated Variables"].split("; ")]
            for var in duplicated_vars:
                original_var = host_data_ci.get(var)
                if original_var and original_var in host_data:
                    print(f"Removing duplicated variable '{original_var}' from {host_file_path}")
                    del host_data[original_var]

        # Remove inconsistent variables
        if analysis["Inconsistent Variables"] != "No inconsistent variables":
            inconsistent_vars = [var.split(" (")[0].lower() for var in analysis["Inconsistent Variables"].split("; ")]
            for var in inconsistent_vars:
                original_var = host_data_ci.get(var)
                if original_var and original_var in host_data:
                    print(f"Removing inconsistent variable '{original_var}' from {host_file_path}")
                    del host_data[original_var]

        # Save the updated host file
        save_yaml_file(host_file_path, host_data)


def clean_inventory(inventory_base_path, analysis_results):
    """Clean the inventory by removing duplicates and inconsistencies."""
    clean_hosts(inventory_base_path, analysis_results)
    clean_host_vars(inventory_base_path, analysis_results)