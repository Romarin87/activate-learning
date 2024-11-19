import numpy as np
import argparse
import os
import re
import time
from ase.io import read
from ase.units import mol, kcal, eV
from deepmd.pt.utils.ase_calc import DPCalculator
import random

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process and filter XYZ file in batches.')
    parser.add_argument('--folders', type=str, default='folders_list', help='Path to the folders list.')
    parser.add_argument('--batch_size', type=int, default=100, help='Batch size for processing.')
    parser.add_argument('--low', type=float, default=1, help='Lower RMSD threshold for candidate structures.')
    parser.add_argument('--high', type=float, default=3, help='Upper RMSD threshold for candidate structures.')
    parser.add_argument('--candidate_num', type=int, default=10, help='Number of candidate structures to randomly select.')
    parser.add_argument('--select_num', type=int, default=10, help='Number of structures to select from each folder.')
    parser.add_argument('--iter', type=str, default='iter001', help='Current iteration number.')
    parser.add_argument('--data_root', type=str, default=os.getcwd(), help='Root directory for data files.')
    parser.add_argument('--model_root', type=str, default=os.getcwd(), help='Root directory for model files.')
    return parser.parse_args()

def initialize_structures(structures, previous_flags=None):
    for i, structure in enumerate(structures):
        structure.set_cell([10, 10, 10], scale_atoms=False)
        if previous_flags:
            structure.info['flags'] = previous_flags[i]
        else:
            structure.info['flags'] = {'accuracy': 0, 'candidate': 0, 'failure': 0, 'selected': 0}
        structure.info['model_energies'] = []

def read_previous_flags(folder, previous_iter):
    previous_index_filename = os.path.join(folder, f'index_{previous_iter}.txt')
    if not os.path.exists(previous_index_filename):
        return None
    
    previous_flags = []
    with open(previous_index_filename, 'r') as f:
        next(f)  # Skip header
        for line in f:
            idx, accuracy, candidate, failure, current_flag, selected = line.strip().split(',')
            previous_flags.append({
                'accuracy': int(accuracy),
                'candidate': int(candidate),
                'failure': int(failure),
                'selected': int(selected)
            })
    return previous_flags

def calculate_energies(structures, selected_indices, model_paths):
    model_energies = {model_path: [] for model_path in model_paths}
    for model_path in model_paths:
        calculator = DPCalculator(model=model_path)
        for idx in selected_indices:
            structure = structures[idx]
            structure.calc = calculator
            energy = structure.get_potential_energy() * eV * mol / kcal  # 能量单位转换
            model_energies[model_path].append(energy)
            structure.info['model_energies'].append(energy)
    return model_energies

def update_flags_and_log(structures, selected_indices, args, log_file, folder):
    accurate_structures_indices = []
    candidates_indices = []
    for i, idx in enumerate(selected_indices):
        structure = structures[idx]
        energies = structure.info['model_energies']
        rmsd = np.sqrt(np.mean(np.square(np.subtract(energies, np.mean(energies)))))
        current_flag = ''

        if rmsd <= args.low:
            structure.info['flags']['accuracy'] += 1
            current_flag = 'accuracy'
            if structure.info['flags']['accuracy'] >= 3:
                accurate_structures_indices.append(idx)
        elif args.low < rmsd <= args.high:
            structure.info['flags']['candidate'] += 1
            current_flag = 'candidate'
            candidates_indices.append(idx)
        else:
            structure.info['flags']['failure'] += 1
            current_flag = 'failure'

        structure.info['current_flag'] = current_flag
        structure.info['rmsd'] = rmsd

        log_file.write(f"{folder},{idx},{rmsd},{structure.info['flags']['accuracy']},{structure.info['flags']['candidate']},{structure.info['flags']['failure']},{current_flag}\n")

    return accurate_structures_indices, candidates_indices

def write_index_file(folder, all_structures, new_iter, selected_indices):
    index_filename = os.path.join(folder, f'index_{new_iter}.txt')
    with open(index_filename, 'w') as index_file:
        index_file.write("Index,Accuracy,Candidate,Failure,Current Flag,Selected\n")
        for idx, structure in enumerate(all_structures):
            flags = structure.info['flags']
            current_flag = structure.info.get('current_flag', 'none') if idx in selected_indices else 'none'
            index_file.write(f"{idx},{flags['accuracy']},{flags['candidate']},{flags['failure']},{current_flag},{flags['selected']}\n")
    os.chmod(index_filename, 0o444)

def process_folder(folder, args, model_paths, previous_iter):
    done_file = os.path.join(folder, f'done_{args.iter}.txt')
    if os.path.exists(done_file):
        print(f"Folder {folder} already processed for iteration {args.iter}. Skipping.")
        return

    xyz_file = os.path.join(folder, 'remaining_structures.extxyz')
    if not os.path.exists(xyz_file):
        print(f"File {xyz_file} does not exist. Skipping folder {folder}.")
        return

    start_time = time.time()

    all_structures = read(xyz_file, index=':')
    num_structures = len(all_structures)

    previous_flags = read_previous_flags(folder, previous_iter)
    if previous_flags is None:
        if args.iter == 'iter001':
            print(f"No previous index file found for {folder}. Initializing flags to zero.")
        else:
            print(f"No previous index file found for {folder}. Skipping.")
            return

    initialize_structures(all_structures, previous_flags)

    # 筛选满足条件的结构
    valid_indices = [i for i, structure in enumerate(all_structures)
                     if structure.info['flags']['accuracy'] < 3 and structure.info['flags']['selected'] < 1]

    if len(valid_indices) <= args.select_num:
        selected_indices = valid_indices
    else:
        selected_indices = random.sample(valid_indices, args.select_num)

    log_file_path = os.path.join(root_dir, f'calculation_log_{args.iter}.txt')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"Processing folder: {folder}\n")
        log_file.write("Folder,Index,RMSD,Accuracy,Candidate,Failure,Current Flag\n")
        model_energies = calculate_energies(all_structures, selected_indices, model_paths)
        accurate_structures_indices, candidates_indices = update_flags_and_log(all_structures, selected_indices, args, log_file, folder)

        # 写入 accurate_structures_indices 和 candidates_indices 到总日志文件
        log_file.write(f"Accurate Structures for {folder}: {','.join(map(str, accurate_structures_indices))}\n")
        log_file.write(f"Candidate Structures for {folder}: {','.join(map(str, candidates_indices))}\n")
        log_file.write("-" * 80 + "\n")  # 分隔符行

    # 删除 'model_energies' 项
    for structure in all_structures:
        if 'model_energies' in structure.info:
            del structure.info['model_energies']

    write_index_file(folder, all_structures, args.iter, selected_indices)

    with open(done_file, 'w') as f:
        f.write('Done')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Time taken for folder {folder}: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    args = parse_arguments()
    root_dir = os.getcwd()
    
    previous_iter = None
    if args.iter != 'iter001':
        iter_num = int(args.iter[4:])
        previous_iter = f'iter{iter_num-1:03d}'

    model_paths = [os.path.join(args.model_root, path) for path in ['000/model.ckpt.pt', '001/model.ckpt.pt', '002/model.ckpt.pt', '003/model.ckpt.pt']]

    with open(args.folders, 'r') as f:
        folders = f.read().splitlines()

    for folder in folders:
        folder_path = os.path.join(args.data_root, folder)
        process_folder(folder_path, args, model_paths, previous_iter)
