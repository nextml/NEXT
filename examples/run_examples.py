#!/usr/bin/python
"""
author: Chris Fernandez, chris2fernandez@gmail.com
last updated: 05/26/2015

An script that can be used to create and launch all example NEXT experiments from examples/ directory.

Usage from Command line:
python run_examples.py
"""
import os


# List of example experiment directories
curr_examples = ['cartoon_tuple/',
                 'cartoon_dueling/',
                 'strange_fruit_triplet/',
                 'cartoon_cardinal/']
# List of example experiment launchers
curr_experiments = ['experiment_tuple.py',
                    'experiment_dueling.py',
                    'experiment_triplet.py',
                    'experiment_cardinal.py']
# Save the absolute path to the current directory
curr_dir = os.path.dirname(os.path.abspath(__file__))

for i, curr_ex in enumerate(curr_examples):
	# Join abs path to curr_dir with iterate from curr_examples
	temp_dir = os.path.join(curr_dir, curr_ex)
	# Change current working directory to temp_dir
	os.chdir(temp_dir)
	# Spawn a shell process using temp_dir and corresponding curr_experiments iterate
	os.system('python '+temp_dir+curr_experiments[i])
	# Return current working directory to curr_dir path
	os.chdir(curr_dir)
