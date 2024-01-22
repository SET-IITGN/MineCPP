from pydriller import Git
import os
from pathlib import Path

parent_dir = Path(__file__).resolve().parent

def checkout(repo_path, commit, prev):
    '''
    checkout to a specific commit
    '''
    # gr=Git(repo_path)
    # print('checkout to commit: ', commit)
    # print(repo_path)
    prev_path = os.path.join(parent_dir,'prev')
    curr_path = os.path.join(parent_dir,'curr')
    prev_comm = Git(prev_path)
    curr_comm = Git(curr_path)
    prev_comm.checkout(prev)
    curr_comm.checkout(commit)
