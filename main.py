import argparse

import numpy as np
import pandas as pd
from pandas import Series

import json
import random
import torch
import utils
from agent import Agent
from brain import Brain
from constants import *
from env import Environment
from log import Log
from pool import Pool

#=============================
def is_time(epoch, trigger):
	return (trigger > 0) and (epoch % trigger == 0)
    

#np.set_printoptions(threshold=np.inf)
#
##=============================
#parser = argparse.ArgumentParser()
#parser.add_argument('-ff', type=float, help="feature factor")
#args = parser.parse_args()
#
#if args.ff:
#	FEATURE_FACTOR = args.ff
#	print("FEATURE_FACTOR = {}".format(FEATURE_FACTOR))

#==============================
np.random.seed(SEED)
random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed(SEED)

#============================== data loading
data = pd.read_pickle(DATA_FILE)
data_val = pd.read_pickle(DATA_FILE)
costs: Series = pd.Series(np.ones(32))


# removing null
#for col in COLUMN_DROP:
#	if col in data.columns:      # column 한개씩 순서대로 들어감
#		data.drop(col, axis=1, inplace=True)
#		data_val.drop(col, axis=1, inplace=True)
#print("Using", DATA_FILE, "with", len(data), "samples.")

#=================================
pool  = Pool(POOL_SIZE)          # 1.000.000
env   = Environment(data, costs, FEATURE_FACTOR)
brain = Brain(pool)
agent = Agent(env, pool, brain)
log   = Log(data_val, costs, FEATURE_FACTOR, brain)

#==============================
epoch_start = 0

# if not BLANK_INIT:
# 	print("Loading progress...")
# 	brain._load()
#
# 	with open('run.state', 'r') as file:
# 		save_data = json.load(file)
#
# 	epoch_start = save_data['epoch']

brain.update_lr(epoch_start)
agent.update_epsilon(epoch_start)

#==============================
print("Initializing pool..")
for i in range(POOL_SIZE // AGENTS):
	utils.print_progress(i, POOL_SIZE // AGENTS)
	agent.step()

pool.cuda()

	
print("Starting..")
for epoch in range(epoch_start + 1, TRAINING_EPOCHS + 1):
	# SAVE
	if is_time(epoch, SAVE_EPOCHS):
		brain._save()

		save_data = {}
		save_data['epoch'] = epoch

		with open('run.state', 'w') as file:
			json.dump(save_data, file)

	# SET VALUES
	if is_time(epoch, EPSILON_UPDATE_EPOCHS):
		agent.update_epsilon(epoch)

	if is_time(epoch, LR_SC_EPOCHS):
		brain.update_lr(epoch)

	# LOG
	if is_time(epoch, LOG_EPOCHS):
		print("Epoch: {}/{}".format(epoch, TRAINING_EPOCHS))
		log.log()
		log.print_speed()

	if is_time(epoch, LOG_PERF_EPOCHS):
		log.log_perf()

	# TRAIN
	brain.train()
	
	for i in range(EPOCH_STEPS):
		agent.step()
	# sys.stdout.write('.'); sys.stdout.flush()

#    del pool, brain
