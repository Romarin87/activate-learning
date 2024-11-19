import os
import dpdata
from glob import glob

# Function to check if a Gaussian log file ended normally
def is_gaussian_log_finished_normally(log_file_path):
    try:
        with open(log_file_path, 'r') as file:
            return 'Normal termination of Gaussian' in file.read()
    except:
        print(f'{log_file_path} not finished normally')
        return False

# Main directory containing MR_ prefixed folders
main_directory = 'gaussian_inputs'

# Create a MultiSystems object
ms = dpdata.MultiSystems(type_map= ["C","H","N","O"])

# Process each Gaussian log file in the subfolder
for file in glob(f'{main_directory}/*.log'):
    print(file)
    # Check if the Gaussian log file ended normally
    if is_gaussian_log_finished_normally(file):
        # Append the log file to the MultiSystems object
        try:
            ms.append(dpdata.LabeledSystem(file, type_map= ["C","H","N","O"], fmt="gaussian/log"))
        except:
            continue

# Output the data for DeepMD-kit
print(ms)
ms.to_deepmd_npy_mixed('../train_add_mix')

