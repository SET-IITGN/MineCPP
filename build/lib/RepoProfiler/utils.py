
# import python_ast_utils
# import ast2vec
import ast
import lizard

def trim_child_nodes(node, line_no):

    #if node is not iterable, pass

    if hasattr(node, 'body'):
        # Filter out child nodes of the specified type
        try:
            node.body = [child for child in node.body if hasattr(child, 'lineno') and child.lineno <= line_no]
        except:
            pass

    # Recursively trim child nodes
    for child_node in ast.iter_child_nodes(node):
        trim_child_nodes(child_node, line_no) 

def _get_constructs(tree, line_no_beg, line_no_end, result={}):
    for node in ast.walk(tree):
        if hasattr(node, 'lineno') and line_no_beg <= node.lineno <= line_no_end:
            result[node.__class__.__name__] = result.get(node.__class__.__name__, 0) + 1
    return result

def get_constructs(file_path, buggy_code):
    
    codecs_list = ['utf-8', 'iso-8859-1','utf-16', 'utf-32', 'latin-1', 'cp1252']    
    for codec in codecs_list:
        try:
            with open(file_path, 'r', encoding=codec) as file:
                src = file.read()
        except:
            continue
    try:
        ast_tree = ast.parse(src)
    except:
        return {}
    line_no_beg = int(buggy_code.split('\n')[0].split(' ')[0])
    line_no_end = int(buggy_code.split('\n')[-2].split(' ')[0])
    return _get_constructs(ast_tree, line_no_beg, line_no_end)

# def vectorize_AST(file_path, line_no=0):
#     print(file_path, line_no)
#     codecs_list = ['utf-8', 'iso-8859-1','utf-16', 'utf-32', 'latin-1', 'cp1252']
        
#     for codec in codecs_list:
#         try:
#             with open(file_path, 'r', encoding=codec) as file:
#                 src = file.read()
#                 break
#         except:
#             continue

#     model = ast2vec.load_model()
#     # parse python3 code into AST if python2 code is given, return default value
#     try:
#         AST = ast.parse(src)
#     except:
#         return 'python2 code', 0
#     trim_child_nodes(AST, line_no)
#     tree = python_ast_utils.ast_to_tree(AST)
#     x = model.encode(tree)
    # return x, len(tree.pretty_print().split('\n'))

def prettyPrint(root, level):
    #print the tree in a pretty format
    if hasattr(root, 'lineno'):
        result = '  '*level + f'{root.__class__.__name__}' + f' {root.lineno}' +'\n'
    else:
        result = '  '*level + f'{root.__class__.__name__}' + '\n'
    for child in ast.iter_child_nodes(root):
        result += prettyPrint(child, level+1)
    return result

def get_lizard_features(file_path):
    liz_obj = lizard.analyze_file(file_path)
    # print(file_path)
    if len(liz_obj.function_list) == 0:
        return {}
    return str(liz_obj.function_list[0].__dict__)

if __name__ == "__main__":
    import pandas as pd
    data = pd.read_csv('geocoder.csv')
    print(get_constructs('test.py', data['Before Bug fix'][0]))
    # vectorize_AST('test.py', 4)
    
