import argparse
parser = argparse.ArgumentParser(
        description="""A tool to mine a GitHub repository and obtain a dataset containing a list of bug-fix pairs and related information. 
The tool, with the argument -U [GitHub URL], mines the repository and provides the output dataset.csv. The schema of dataset.csv contains 14 columns and each row in it represents a potential bug-fix pair.

The 14 columns are as follows:

- 'Before Bug fix': Represents the code snippet containing a bug.
- 'After Bug fix': Represents the code snippet after the bug is fixed.
- 'Location': Represents the line numbers. The 'after' field represents the line number where the bug is fixed, and 'before' represents the line number where the bug was found.
- 'Bug type': Represents the type of bug obtained from LLM using the git diff between the fixed commit and the buggy commit.
- 'Commit Message': Represents the author's description of the commit.
- 'File Path': Represents the path of the file in which the change is present or the bug is fixed.
- 'Test File': Denotes whether the test file is present for the bug. Here, 1 represents that the test file is present, and 0 represents that the test file is absent.
- 'Coding Effort': Represents the effort an author makes before a bug occurs (obtained from the AST of the source code).
- 'Constructs': Represents the type of constructs in which the bug occurred.
- 'Lizard Features Buggy': Denotes the cyclomatic complexity of the buggy file.
- 'Lizard Features Fixed': Denotes the cyclomatic complexity of the bug-fix file.
- 'BLEU', 'crystalBLEU_score', 'bert_score': Represent three different algorithms that estimate the similarity between buggy and fixed code. The similarity score lies in the range 0 to 1, where 1 indicates similarity, and 0 indicates dissimilarity.

        
"""
,  formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--version', action='version', version='YourTool v1.0')
parser.add_argument('-u', help='Provide the GitHub repo link to anlyse the repo')

# Parse command-line arguments
args = parser.parse_args()

#if no arguments passed display args error
if not any(vars(args).values()):
    parser.print_help()
    parser.error('No arguments provided. Please provide the required arguments.')

import pandas as pd
import sys
import os
import subprocess
import webbrowser
from tqdm import tqdm
from . import getCommits
from . import szz
from . import checkout
from . import diff
from . import AST
import shutil
from . import bug_type_gen
from .gitOps import GitOps, Project
from .testCase import find_test_file
from .AST_tree_sitter import ASTree
from .utils import get_lizard_features
from .sim import get_similiraityScores
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from pathlib import Path

def main():
    PARENT_DIR = Path(__file__).resolve().parent
    LOG_COMMIT_PATH = os.path.join(PARENT_DIR, 'log_commit.txt')
    DATASET_SAVE = os.path.join(os.getcwd(), 'dataset.csv')
    LOG_PATH = os.path.join(PARENT_DIR, 'log.txt')
    PROJECT_LOG = os.path.join(PARENT_DIR, 'projects_done.txt')
    PROJECTS_PATH = os.path.join(PARENT_DIR, 'projects.csv')


    commit_count = 0
    project_link = args.u
    project_name = '/'.join(project_link.split('/')[-2:])
    projects = pd.DataFrame([[project_link, project_name]], columns = ['URL', 'Project_name']) #read csv file of projects

    def get_project_name():
        return projects['Project_name']

    def get_project_url():
        return projects['URL']

    def get_last_processed_project():
        if os.path.exists(LOG_COMMIT_PATH):
            with open(LOG_COMMIT_PATH, 'r') as file:
                last_project = file.readlines()
            return last_project[-1].split()

    if not os.path.exists(DATASET_SAVE): 
        dataframe = pd.DataFrame(columns=['Before Bug fix', 'After Bug fix', 'Location', 'Bug type',
        'Commit Message', 'Project URL', 'File Path', 'Fixed Commit',
        'Buggy Commit', 'Test File', 'Coding Effort', 'Constructs',
        'Lizard Features Buggy', 'Lizard Features Fixed', 'BLEU', 'crystalBLEU_score', 'bert_score'])
        dataframe.to_csv(DATASET_SAVE, index=False)

    try:
        processing_project, commit_hash = get_last_processed_project()
        last_project_index = projects[projects['Project_name'] == processing_project].index[0]
    except:
        last_project_index = 0
        commit_hash = None

    for i in range(last_project_index,len(projects)):
        project_name = get_project_name()[i].split('/')[1]
        print(f"Processing for project:  {project_name}")
        project_url = get_project_url()[i]
        # if os.path.exists(project_name):
        #     shutil.rmtree(project_name)
        repo_path = os.path.join(PARENT_DIR, project_name) 
        repo_curr_path = os.path.join(PARENT_DIR, 'curr')
        repo_prev_path = os.path.join(PARENT_DIR, 'prev')
        #create a git object

        if not os.path.exists(repo_path):
            cmd = ['git', 'clone', project_url]
            result = subprocess.run(cmd, cwd=PARENT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd = ['cp', '-R', repo_path, repo_curr_path]
            subprocess.run(cmd, cwd=PARENT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            cmd = ['cp', '-R', repo_path, repo_prev_path]
            subprocess.run(cmd, cwd=PARENT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        
        commits_map = getCommits.get_fixed_commits(repo_path)
        print('Processing SZZ')
        if commit_hash is None:
            szz_index=0
            for commits in commits_map:
                modified_files = szz.get_szz(repo_path, commits[0]) #get modified files of current commit
                commits.append(modified_files)
        else:
            for index, commits in enumerate(commits_map):
                if commit_hash == commits[0].hash:
                    szz_index = index
                    break
            for _, commits in enumerate(commits_map[szz_index:],start=szz_index):
                modified_files = szz.get_szz(repo_path, commits[0]) #get modified files of current commit
                commits.append(modified_files)
        for commit, prev, modified_files in tqdm(commits_map[szz_index:], desc='Processing Commits'):
            commit_count += 1
            if os.path.exists(LOG_COMMIT_PATH):
                with open(LOG_COMMIT_PATH, 'a') as f:
                    f.write(get_project_name()[i]+' '+commit.hash+'\n')
            else:
                with open(LOG_COMMIT_PATH, 'w') as f:
                    f.write(get_project_name()[i]+' '+commit.hash+'\n')
            print("Processing for commit: ", commit.hash)
            print("Corresponding commit msg: ", commit.msg.split('\n')[0]) 
            checkout.checkout(repo_path, commit.hash, prev.hash)
            for file_path in modified_files:
                diff_text = diff.git_diff(repo_path, prev.hash, commit.hash, file_path)
                bug_type = bug_type_gen.predict(diff_text)
                pairs = diff.get_pairs(diff_text)
                for deletion, addition in pairs:
                    line_no_fixed = int(addition.split(',')[0])
                    line_no_buggy = int(deletion.split(',')[0])
                    file_path_prev = os.path.join(repo_prev_path, file_path)
                    file_path_curr = os.path.join(repo_curr_path, file_path)
                    # print(file_path_prev, file_path_curr)
                    fixed_code = AST.extract_function_by_line(file_path_curr,line_no_fixed)
                    # print(fixed_code)
                    line_no_curr = int(addition.split(',')[0])
                    buggy_code = AST.extract_function_by_line(file_path_prev, line_no_buggy)
                    # print(buggy_code)
                    location = 'Before: ' + deletion + '\n' +'After: ' + addition
                    fixed_commit_hash = commit.hash
                    buggy_commit_hash = prev.hash
                    if find_test_file(file_path_curr, file_path.split('/')[-1]):
                        test_file = 1
                    else:
                        test_file = 0
                    # GET CODING EFFORT AND CONSTRUCTS USINGS AST
                    AST_T = ASTree(file_path_prev, list(map(int, location.split('\n')[0].split(':')[1].strip().split(',')))[0])
                    # get constructs
                    constructs = AST_T.get_constructs(buggy_code)
                    # get coding effort
                    coding_effort = AST_T.coding_effort
                    # get lizard features
                    lizard_features_buggy = get_lizard_features(file_path_prev)
                    lizard_features_fixed = get_lizard_features(file_path_curr)
                    # get bleu score
                    crystalBLEU_score, sbleu, bert_score = get_similiraityScores(buggy_code, fixed_code)
                    new_row = pd.DataFrame([[buggy_code, fixed_code, location, bug_type,
                                            commit.msg.split('\n')[0], project_url, file_path, fixed_commit_hash,
                                            buggy_commit_hash, test_file, coding_effort, constructs,
                                            lizard_features_buggy, lizard_features_fixed, sbleu, crystalBLEU_score, bert_score]], 
                                            columns=['Before Bug fix', 'After Bug fix', 'Location', 'Bug type',
                                            'Commit Message', 'Project URL', 'File Path', 'Fixed Commit',
                                            'Buggy Commit', 'Test File', 'Coding Effort', 'Constructs',
                                            'Lizard Features Buggy', 'Lizard Features Fixed', 'BLEU', 
                                            'crystalBLEU_score', 'bert_score'])
                    new_row.to_csv(DATASET_SAVE, mode='a',header=False,index=False)
        print('Removing project folder: ', project_name)
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH,'a') as f:
                f.write(get_project_name()[i])
        else:
            with open(LOG_PATH,'w') as f:
                f.write(get_project_name()[i])
        if os.path.exists(PROJECT_LOG):
            with open(PROJECT_LOG,'r') as f:
                projects_done = int(f.readline())
                
            with open(PROJECT_LOG, 'w') as f:
                f.write(str(projects_done+1))
        else:
            with open(PROJECT_LOG, 'w') as f:
                f.write(str(1))
        shutil.rmtree(repo_path)
        shutil.rmtree(repo_curr_path)
        shutil.rmtree(repo_prev_path)
        commit_hash = None

    from . import app
    webbrowser.open('http://127.0.0.1:5000')
    app.app.run()
    # dataframe.to_csv('./out_2.csv')
            

