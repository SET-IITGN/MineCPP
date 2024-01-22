import os
import re

def find_test_file(directory, base_fileName):
    test_files = []
    base_fileName_withoutExtension, _ = os.path.splitext(base_fileName)
    pattern = re.compile(r'test[^a-zA-Z]*{}|{}[^a-zA-Z]*test'.format(re.escape(base_fileName_withoutExtension), re.escape(base_fileName_withoutExtension)), re.IGNORECASE)
    # print(directory)
    # print(base_fileName)
    #print(os.walk(directory))
    
    for root, dirs, files in os.walk(directory):
        # print(files)
        
        for file in files:
            # print(os.path.join(root, file))

            if pattern.match(file):
                test_files.append(os.path.join(root, file))
    # input()
    if test_files:
        # print(test_files)
        return True
    else:
        return False
    
# repo_path = './gitRepos'
# project_name = 'geocoder'
# directory = os.path.join(repo_path, project_name)
# base_fileName = 'google.py'
# find_test_file(directory, base_fileName)
