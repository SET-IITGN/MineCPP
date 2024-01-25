from tree_sitter import Language, Parser
from pathlib import Path
import os

parent_dir = Path(__file__).resolve().parent

Language.build_library(
  # Store the library in the `build` directory
    os.path.join(parent_dir, 'build/my-languages.so'),

  # Include one or more languages
  [
    os.path.join(parent_dir, 'build/tree-sitter-c/'),
    os.path.join(parent_dir, 'build/tree-sitter-java/'),
    os.path.join(parent_dir, 'build/tree-sitter-cpp/'),
    os.path.join(parent_dir, 'build/tree-sitter-python/')
  ]
)

JAVA_LANGUAGE = Language(os.path.join(parent_dir, 'build/my-languages.so'), 'java')
CPP_LANGUAGE = Language(os.path.join(parent_dir, 'build/my-languages.so'), 'cpp')
C_LANGUAGE = Language(os.path.join(parent_dir, 'build/my-languages.so'), 'c')
PY_LANGUAGE = Language(os.path.join(parent_dir, 'build/my-languages.so'), 'python')

py_parser, cpp_parser, c_parser, jave_parser = Parser(), Parser(), Parser(), Parser()
py_parser.set_language(PY_LANGUAGE)
cpp_parser.set_language(CPP_LANGUAGE)
c_parser.set_language(C_LANGUAGE)
jave_parser.set_language(JAVA_LANGUAGE)


class ASTree:
    
    def __init__(self,  file_path, line_no):
        self.node = [] #container to find store the nodes traversed
        
        codecs_list = ['utf-8', 'iso-8859-1','utf-16', 'utf-32', 'latin-1', 'cp1252']
        
        for codec in codecs_list:
            try:
                #read first 20 lines of the file
                with open(file_path, 'r', encoding=codec) as file:
                    self.source_code = file.readlines() 
                #print(self.source_code)            
            except:
                continue

        if file_path.endswith('.py'):
            self.parser = py_parser
        elif file_path.endswith('.cpp'):
            self.parser = cpp_parser
        elif file_path.endswith('.c'):
            self.parser = c_parser
        elif file_path.endswith('.java'):
            self.parser = jave_parser

        #parse the source till line no
        self.tree = self.parser.parse(''.join(self.source_code[:line_no]).encode())
        self.root = self.tree.root_node
        self.coding_effort = len(self.printTree().split('\n'))
        
        #print(self.root.children)
        # model = ast2vec.load_model()
        # model.encode(self.root)
        
        
    def _get_constructs(self, node):
        # get the constructs from the AST
        # print(line_no_begin,node.start_point[0],line_no_end)
        # print(line_no_begin <= node.start_point[0] <= line_no_end)
        # if line_no_begin <= node.start_point[0] <= line_no_end:
        self.node.append(node)
        for child in node.children:
            self._get_constructs(child)


    def get_constructs(self, buggy_code):
        line_no_begin = int(buggy_code.split('\n')[0].split(' ')[0])-1
        try:
            line_no_end = int(buggy_code.split('\n')[-2].split(' ')[0])-1
        except:
            line_no_end = int(buggy_code.split('\n')[-1].split(' ')[0])-1
        self.buggy_code_parse = self.parser.parse(''.join(self.source_code[line_no_begin:line_no_end]).encode())
        buggy_code_root = self.buggy_code_parse.root_node
        self._get_constructs(buggy_code_root)
        constructs_count = {}
        for node in self.node:
            if node.type in constructs_count:
                constructs_count[node.type] += 1
            else:
                constructs_count[node.type] = 1
        return constructs_count

    def printTree(self):
        # print(id(self.root))
        return self.prettyPrint(self.root, 0)

    def prettyPrint(self, root, level):
        #print the tree in a pretty format
        result = '  '*level + root.type + f"({root.start_point[0]}, {root.end_point[0]})" + '\n'
        for child in root.children:
            result += self.prettyPrint(child, level+1)
        return result   
        
    def remove_nodes_after_line(self, node, line_number):
        #remove all the nodes after the line number
        if node.start_point[0] > line_number:
            return None
        else:
            #print(node.children)
            for child in node.children:
                if child.start_point[0] > line_number:
                    node.children.remove(child)
            #print(node.children)
            for child in node.children:
                self.remove_nodes_after_line(child, line_number)
            return node
                

    def extract_function_by_line(self, line_number):
        self.traverse(self.root, line_number)
        
if __name__ == '__main__':
    AST = ASTree('sim.py',10)
    # for node in ast.get_constructs(ast.root, 1, 10):
    #     print(node)
    # print(AST.printTree())
    # print(len(AST.printTree().split('\n')))
    # ast.remove_nodes_after_line(ast.root, 10)
    # print(ast.root.children)
    # print(ast.printTree())
    # ast.extract_function_by_line(43)
    # for node in ast.node:
    #     print(node)