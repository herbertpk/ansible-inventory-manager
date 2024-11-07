# Ansible Inventory Manager

A Python tool to validate, clean, and manage large Ansible inventories by checking configurations in `hosts.ini`, `group_vars`, and `host_vars` YAML files. This tool helps identify and resolve inconsistencies, duplicates, and orphaned configurations, ensuring a streamlined and accurate Ansible inventory setup.

## Features

- **Identify Duplicated Hosts**:
  - Detects hosts that are listed multiple times within the same group in `hosts.ini`.
  
- **Check for Inconsistencies**:
  - Finds hosts defined in `hosts.ini` without corresponding files in `host_vars`.
  - Finds hosts with files in `host_vars` but without definitions in `hosts.ini`.
  - Identifies variables duplicated between `group_vars` and `host_vars`.
  - Detects inconsistent variable values across `group_vars` and `host_vars`.

- **Inventory Cleanup**:
  - Cleans up hosts with duplicated entries.
  - Removes hosts missing a corresponding file in `host_vars`.
  - Removes orphaned entries from `host_vars`.

- **Generate CSV Reports**:
  - Automatically saves analysis results to a CSV file, providing an easy-to-read summary of inventory issues.

## Project Structure

The project includes the following main components:

- **`analyze_inventory.py`**: Core module to parse `hosts.ini`, analyze the inventory, and identify duplicates, inconsistencies, and orphaned hosts.
- **`clean_inventory.py`**: Contains functions to clean up duplicated and inconsistent entries in both `hosts.ini` and `host_vars`.
- **`run.py`**: Main script to run the analysis and cleanup operations and save results to CSV.

## Usage

1. **Setup**:
   - Ensure the required dependencies are installed.
   - Place the `hosts.ini`, `group_vars`, and `host_vars` directories within your inventory directory.

2. **Run Analysis with CSV Output**:
   - Use the `analyze_inventory` function to check for issues in the inventory and automatically save results to CSV:
     ```python
     from modules.analyze_inventory import analyze_inventory
     
     inventory_path = '/path/to/your/inventory'
     analysis_results = analyze_inventory(inventory_path, save_csv=True)
     ```
   - Setting `save_csv=True` will generate a CSV report, `inventory_analysis.csv`, with the analysis results.

3. **Clean Inventory**:
   - Use `clean_inventory` to remove duplicated and missing hosts from `hosts.ini`, as well as inconsistencies from `host_vars`:
     ```python
     from modules.clean_inventory import clean_inventory
     clean_inventory(inventory_path, analysis_results)
     ```

## Example

```bash
# Run the analysis and cleanup script
python run.py
