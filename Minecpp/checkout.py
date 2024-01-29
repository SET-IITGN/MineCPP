from pydriller import Git
import os
from pathlib import Path

parent_dir = Path(__file__).resolve().parent

def checkout(commit, prev, prev_path, curr_path, ):
    '''
    checkout to a specific commit
    '''
    # gr=Git(repo_path)
    # print('checkout to commit: ', commit)
    # print(repo_path)
    prev_comm = Git(prev_path)
    curr_comm = Git(curr_path)
    prev_comm.checkout(prev)
    curr_comm.checkout(commit)
