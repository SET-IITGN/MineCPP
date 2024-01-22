# get the hash of git commits using commit message using pydriller

from pydriller import Git
import os
import pandas as pd
import subprocess
from typing import Literal






class Project:
    def __init__(self, project_path):
        self.PATH = project_path
        self.git = Git(self.PATH)
        self.commits = []
        self.get_commits()

    def get_commits(self):
        self.commits = []
        self.commits_msg = []
        commits_gen=self.git.get_list_commits()  # get all commits
        for i in commits_gen:
            self.commits.append(i)
            self.commits_msg.append(i.msg.split('\n')[0])
        

class GitOps:
    def __init__(self, dataset_path, repo_path):
        self.DATASET_PATH = dataset_path
        self.data = pd.read_csv(dataset_path)
        self.REPO_PATH = repo_path
        self.count = 0
        self.commit_msg = 0
        self.notMatch = set()

    def remove_repos(self):
        if os.listdir(self.REPO_PATH):
            #shutil.rmtree(self.REPO_PATH, ignore_errors=True)
            os.system(f'rm -rf {self.REPO_PATH}*')
            

    def clone_repo(self, repo_url):
        self.remove_repos()
        print("Cloning repo: ", repo_url)
        project_name = repo_url.split('/')[-1]
        os.system('git clone '+repo_url+f' {self.REPO_PATH}/{project_name}')
        
        # os.system('git clone '+repo_url+f' {self.REPO_PATH}/{project_name}/prev')
        # os.system('git clone '+repo_url+f' {self.REPO_PATH}/{project_name}/curr')
        project_path = os.path.join(self.REPO_PATH, project_name)
        #check if prev dir exist in project_path
        # if 'prev' not in os.listdir(project_path):
        #     os.mkdir(os.path.join(project_path,'prev'))
        # #check if curr dir exist in project_path
        # if 'curr' not in os.listdir(project_path):
        #     os.mkdir(os.path.join(project_path,'curr'))
        #copy the repo to /gitrepos/curr and /gitrepos/prev
        # shutil.copytree(os.path.join(self.REPO_PATH, project_name), os.path.join(self.REPO_PATH, project_name, 'prev'))
        # shutil.copytree(os.path.join(self.REPO_PATH, project_name), os.path.join(self.REPO_PATH, project_name, 'curr'))
        print("Cloning repo: ", repo_url, "done")

    def check_repo_exists(self, project_name):
        # check if any repo exists in ./gitRepos/
        print("Checking if repo exists...")
        if project_name in os.listdir(f'{self.REPO_PATH}'):
            return True
        return False
    
    def get_git_diff(self, project_path, prev_commit, commit, file_path):
        cmd = ['git', 'diff', prev_commit, commit, file_path]
        result = subprocess.run(cmd, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        codecs_list = ['utf-8', 'iso-8859-1','utf-16', 'utf-32', 'latin-1', 'cp1252']
        for codec in codecs_list:
            try:
                decoded_text = result.stdout.decode(codec)
                return decoded_text
            except:
                continue
        print('error in decoding')
        return None 

    def diffEqual(self, project_path, prev_commit, commit, file_path, location):
        diff = self.get_git_diff(project_path, prev_commit, commit, file_path)
        if diff == '' or diff == None:
            return False
        # print(prev_commit, commit, file_path, location)
        flag = False
        location = list(map(int, location.split('\n')[0].split(':')[1].strip().split(',')))
        # print('before offset', location)
        # print(diff)
        offset = []
        processed_diff = []
        for i, line in enumerate(diff.splitlines()):
            if line.startswith('@@'):
                # print(line,'line')
                try:
                    offset_temp = int(line.split('-')[1].split(',')[0])
                except:
                    offset_temp = int(line.split('-')[1].split('+')[0].strip())
                if offset_temp <= location[0]:
                    offset = offset_temp
                    del processed_diff
                    processed_diff = []
                    flag = True
                else:
                    break
            if flag:
                processed_diff.append(line)
        # print(processed_diff)  
        if offset == []:
            return False  
        location_temp = [i-offset for i in location]
        # print(offset, 'offset')
        # print(location_temp)
        # print(len(processed_diff),'len')
        if location_temp[-1] > len(processed_diff):
            return False
        # check if values in location as index in diff starts with '-'
        if all(processed_diff[location_temp[i]].startswith('-') for i in range(len(location_temp))):
            return True
        return False

    def checkout(self, project_path, commit):
        '''
        checkout the commit in curr or prev
        '''
        chkout = Git(project_path)
        chkout.checkout(commit)
        return 
    
    def get_label(self, project_path, commit):
        return Git(project_path).get_commit(commit).tag

    def isCodeEqual(self, project_path, prev_commit, commit, file_path, location, buggy_code, fixed_code):
        self.checkout(os.path.join(project_path,'prev'), prev_commit)
        
        codecs_list = ['utf-8', 'iso-8859-1','utf-16', 'utf-32', 'latin-1', 'cp1252']
        prev_code = []
        code = []
        for codec in codecs_list:
            try:
                with open(os.path.join(project_path, 'prev', file_path), 'r', encoding=codec) as f:
                    prev_code = f.readlines()
            except:
                continue
        self.checkout(os.path.join(project_path,'curr'), commit)
        #input()
        for codec in codecs_list:
            try:
                with open(os.path.join(project_path, 'curr', file_path), 'r', encoding=codec) as f:
                    code = f.readlines()
            except:
                continue
        # with open(os.path.join(project_path, 'curr', file_path), 'r', encoding="utf8") as f:
        #     code = f.readlines()
        location = list(map(int, location.split('\n')[0].split(':')[1].strip().split(',')))
        #add line number to each line in code
        prev_code = [str(i+1)+' '+prev_code[i].strip('\n') for i in range(len(prev_code))]
        code = [str(i+1)+' '+code[i].strip('\n') for i in range(len(code))]
        #check if buggy code is present in prev_code
        # print(buggy_code)
        buggy_line_no = int(buggy_code.split('\n')[0].split(' ')[0])
        fixed_line_no = int(fixed_code.split('\n')[0].split(' ')[0])
        buggy_code = buggy_code.split('\n')[:-1]
        fixed_code = fixed_code.split('\n')[:-1]
        # print('**************************************************')
        # print(buggy_code)
        # print(prev_code[buggy_line_no-1:buggy_line_no+len(buggy_code)-1])
        # print(file_path)
        # print('**************************************************')
        #input()
        if buggy_code == prev_code[buggy_line_no-1:buggy_line_no+len(buggy_code)-1]:
            # print('buggy code matched')
            # print(fixed_code)
            # print(code[fixed_line_no-1:fixed_line_no+len(fixed_code)-1])
           # input()
            if fixed_code == code[fixed_line_no-1:fixed_line_no+len(fixed_code)-1]:
                return True
            return False
        return False


    def get_hash(self, project, row):
        commit_msg = row['Commit Message']
        location = row['Location']
        #location = location.split('\n')[0].split(':')[1].split(',')[-1].strip()
        file_path = row['File Path']
        commits = project.commits
        for i in range(1,len(commits)):
            commit = commits[i]
            prev_commit = commits[i-1]

            if commit_msg not in project.commits_msg:
                self.notMatch.add(commit_msg)
            
            if commit_msg == commit.msg.split('\n')[0]:
                #print(commit.msg.split('\n')[0])
                print(commit.hash, commit.msg.split('\n')[0])
                self.commit_msg += 1
                if self.isCodeEqual(project.PATH, prev_commit.hash, commit.hash, file_path, location,
                                    row['Before Bug fix'], row['After Bug fix']):
                    project.commits = commits[i-1:]
                    return prev_commit.hash, commit.hash
            #     #self.matched_commits.append(commit)
            #     if self.diffEqual(project.PATH, prev_commit.hash, commit.hash, file_path, location):
            #        #
            #        #  self.count += 1 
            #         # print(len(project.commits))
            #         project.commits = commits[i-1:]
            #         # print(len(project.commits))
            #         return prev_commit.hash, commit.hash
            # #preprocess location of bug
        return None, None
    
    def data_iterator(self):
        project_name = None
        print(len(self.data))
        #check index in log.txt
        if not os.path.exists('log.txt'):
            with open('log.txt', 'w') as f:
                f.write('0')
        with open('log.txt', 'r') as f:
            processed_index = int(f.readlines()[0])
        for index, row in self.data.iterrows():
            if index <= processed_index:
                continue
            curr_project = row['Project URL'].split('/')[-1]
            #print(curr_project)
            if row['Project URL'] == 'https://github.com/microsoft/forecasting':
                continue
            if curr_project != project_name:
                project_name = curr_project
                if not self.check_repo_exists(project_name):
                    self.clone_repo(row['Project URL'])
                project = Project(os.path.join(self.REPO_PATH, project_name))
            
            buggy_commit, fixed_commit = self.get_hash(project, row)
            
            # if row['Commit Message'] in project.commits_msg:
            #     self.commit_msg += 1
            #     buggy_commit, fixed_commit = self.get_hash(project, row)
            #     if buggy_commit == None:
            #         selnetweb
            # f.notMatch.add(row['Commit Message'])
            self.data.at[index, 'Fixed Commit'] = fixed_commit
            self.data.at[index, 'Buggy Commit'] = buggy_commit
            #print(self.data.iloc[index])
            
            self.data.iloc[index].to_csv('dataset1.csv',  mode='a',header=False,index=False)
            with open('log.txt', 'w') as f:
                f.write(str(index))
            

    def save_data(self):
        self.data.to_csv(self.DATASET_PATH, index=False)


# try:
# gitOps = GitOps('./dataset.csv')
# if not os.path.exists('./gitRepos'):
#     os.mkdir('gitRepos')
# gitOps.data_iterator()
# #gitOps.save_data()
# gitOps.remove_repos()
# print(gitOps.count)
# print(gitOps.notMatch)
# print(gitOps.commit_msg)
# except Exception as e:
#     #send the whole run time error message to slack
#     error_message = f"Error: {e}"
    



#     error_message = f"Error: {e}"
#     print(error_message)
#     send_slack_message(f"Script encountered an error:\n{error_message}")
