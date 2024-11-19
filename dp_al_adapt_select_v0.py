import os
import argparse
import random
import stat
from collections import defaultdict
from ase.io import read, write

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process and filter candidate structures from index files.')
    parser.add_argument('--iter', type=str, default='iter001', help='Iteration number to process.')
    parser.add_argument('--data_root', type=str, default='.', help='Root directory for data files.')
    parser.add_argument('--max_candidates', type=int, default=20000, help='Maximum number of candidate structures to select.')
    parser.add_argument('--output_file', type=str, default=None, help='Output file for selected candidate structures.')
    parser.add_argument('--log_file', type=str, default=None, help='Log file for recording selected candidate structures.')
    parser.add_argument('--folders', type=str, default='folders_list', help='Path to the folders list.')
    return parser.parse_args()

def read_index_files(data_root, folders, iter_num):
    candidates = defaultdict(list)
    for folder in folders:
        index_file = os.path.join(data_root, folder, f'index_{iter_num}.txt')
        if not os.path.exists(index_file):
            print(f"Index file {index_file} does not exist.")
            continue
        
        with open(index_file, 'r') as f:
            next(f)  # Skip header
            for line in f:
                parts = line.strip().split(',')
                idx = int(parts[0])
                candidate_flag = parts[4]
                selected_flag = int(parts[5])
                if candidate_flag == 'candidate' and selected_flag == 0:
                    candidates[folder].append(idx)
    return candidates

def process_candidates(candidates, max_candidates):
    all_candidates = [(folder, index) for folder, indices in candidates.items() for index in indices]
    if len(all_candidates) > max_candidates:
        all_candidates = random.sample(all_candidates, max_candidates)
    return all_candidates

def update_selected_flag(data_root, candidates, iter_num):
    for folder, index in candidates:
        index_file = os.path.join(data_root, folder, f'index_{iter_num}.txt')
        # Remove read-only permission
        os.chmod(index_file, stat.S_IWUSR | stat.S_IREAD)

        lines = []
        with open(index_file, 'r') as f:
            header = f.readline()
            for line in f:
                parts = line.strip().split(',')
                idx = int(parts[0])
                if idx == index:
                    parts[-1] = '1'  # Update selected flag to 1
                lines.append(','.join(parts))

        with open(index_file, 'w') as f:
            f.write(header)
            f.write('\n'.join(lines))

        # Set read-only permission back
        os.chmod(index_file, stat.S_IREAD)

def save_candidates_to_file(data_root, output_file, candidates):
    selected_structures = []
    for folder, index in candidates:
        xyz_file = os.path.join(data_root, folder, 'remaining_structures.extxyz')
        structures = read(xyz_file, index=':')
        selected_structures.append(structures[index])
    write(output_file, selected_structures)

def write_log_file(log_file, candidates):
    with open(log_file, 'w') as f:
        for folder, index in candidates:
            f.write(f"{folder},{index}\n")

def create_done_file(done_file):
    with open(done_file, 'w') as f:
        f.write('Done')

if __name__ == "__main__":
    args = parse_arguments()
    
    done_file = os.path.join(os.getcwd(), f'done_{args.iter}.txt')
    if os.path.exists(done_file):
        print(f"Iteration {args.iter} already processed. Skipping.")
        exit(0)

    log_file = args.log_file or f'selected_candidates_log_{args.iter}.txt'
    output_file = args.output_file or f'selected_candidates_{args.iter}.extxyz'

    with open(args.folders, 'r') as f:
        folders = f.read().splitlines()

    candidates = read_index_files(args.data_root, folders, args.iter)
    selected_candidates = process_candidates(candidates, args.max_candidates)
    update_selected_flag(args.data_root, selected_candidates, args.iter)
    save_candidates_to_file(args.data_root, output_file, selected_candidates)
    write_log_file(log_file, selected_candidates)
    create_done_file(done_file)
    
    print(f"There are a total of {len(candidates)} candidate structures in {args.iter} iteration ")
    print(f"Selected {len(selected_candidates)} candidate structures and saved to {output_file}. Log written to {log_file}.")
