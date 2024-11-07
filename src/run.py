from modules.analyze_inventory import analyze_inventory
from modules.clean_inventory import clean_inventory

inventory_path = 'your/inventory/path'


analysis_results = analyze_inventory(inventory_path,save_csv=True)

#clean_inventory(inventory_path, analysis_results)