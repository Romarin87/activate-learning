import os
import argparse
from ase.io import read, write

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate Gaussian input files from extxyz file.')
    parser.add_argument('--input_file', type=str, required=True, help='Path to the extxyz file containing structures.')
    parser.add_argument('--output_dir', type=str, default='gaussian_inputs', help='Directory to save the Gaussian input files.')
    parser.add_argument('--keywords', type=str, default='#P wb97xd def2tzvp nosymm force', help='Keywords for Gaussian input file.')
    return parser.parse_args()

def generate_gaussian_input(structure, index, output_dir, keywords, input_file):
    # Gaussian input file header
    header = f"""%chk=job{str(index).zfill(5)}.chk
{keywords}

{input_file}

0 1
"""
    # Atoms section
    atoms_section = ""
    for atom in structure:
        atoms_section += f"{atom.symbol} {atom.position[0]: .12f} {atom.position[1]: .12f} {atom.position[2]: .12f}\n"
    
    # Combine header and atoms section
    gaussian_input_content = header + atoms_section + '\n\n'

    # Write to Gaussian input file
    output_file = os.path.join(output_dir, f'job{str(index).zfill(5)}.gjf')
    with open(output_file, 'w') as f:
        f.write(gaussian_input_content)

def main():
    args = parse_arguments()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    structures = read(args.input_file, index=':')
    
    for index, structure in enumerate(structures):
        generate_gaussian_input(structure, index, args.output_dir, args.keywords, args.input_file)
        #print(f"Generated Gaussian input file for structure {index}")

if __name__ == "__main__":
    main()

