#! /bin/bash
export CUDA_VISIBLE_DEVICES=0
cd train/000/
nohup dp train input.json &
export CUDA_VISIBLE_DEVICES=1
cd ../../train/001/
nohup dp train input.json &
export CUDA_VISIBLE_DEVICES=2
cd ../../train/002/
nohup dp train input.json &
export CUDA_VISIBLE_DEVICES=3
cd ../../train/003/
nohup dp train input.json &
