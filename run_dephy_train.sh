#!/bin/bash
cd /home/gdp/github/myoassist
/home/gdp/anaconda3/envs/myoassist/bin/python rl_train/run_train.py \
  --config_file_path rl_train/train/train_configs/dephy_exo_train.json \
  --config.env_params.terrain_type "flat"
