from pathlib import Path
import os
import sys
import json
for i in range(5):
    if not (Path.cwd()/"pointwise_in_time").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np

def index_formula(raw_str):
    # Identifies operators and atoms and indexes them.
    op_idxs = list()
    paren_map = list()
    operator_strength = list()
    empty_tree_nodes = list()
    
    # Add extra terminal spaces for processing purposes:
    #print('length of raw_str: ' , len(raw_str))
    formula_str = ''.join([' ',raw_str, '  '])
    #print('formula_str: ', formula_str)
    #print('length of formula_str: ' , len(formula_str))
    # Initialize parenthetical grouping level to 0:
    paren_level = 0
    # Initialize empty atom string
    atom = ''
    
    i = 1
    #for i in range(1, len(raw_str)+1):
    while i < len(raw_str) + 1:
        #print('i is: ', i)
        #'or' surrounded by ')', '(', and/or spaces:
        if formula_str[i:i+2] == 'or' and ((formula_str[i-1] == ')' or formula_str[i-1] == ' ') and (formula_str[i+2] == '(' or formula_str[i+2] == ' ')):
            op_idxs.append('or')
            paren_map.append(paren_level)
            operator_strength.append(0)
            empty_tree_nodes.append(["or",list(),list()])
            i = i+2
        #'and' surrounded by ')', '(', and/or spaces:
        elif formula_str[i:i+3] == 'and' and ((formula_str[i-1] == ')' or formula_str[i-1] == ' ') and (formula_str[i+3] == '(' or formula_str[i+3] == ' ')):
            op_idxs.append('and')
            paren_map.append(paren_level)
            operator_strength.append(0)
            empty_tree_nodes.append(["and",list(),list()])
            i = i+3
        # '->':
        elif formula_str[i:i+2] == '->':
            op_idxs.append('->')
            paren_map.append(paren_level)
            operator_strength.append(0)
            empty_tree_nodes.append(["->",list(),list()])
            i = i+2
            
        # Binary operators:
        elif formula_str[i] == 'U':
            op_idxs.append('U')  
            paren_map.append(paren_level)
            operator_strength.append(1)
            empty_tree_nodes.append(["U",list(),list()])
            i = i+1
        elif formula_str[i] == 'R':
            op_idxs.append('R') 
            paren_map.append(paren_level)
            operator_strength.append(1)
            empty_tree_nodes.append(["R",list(),list()])
            i = i+1
        elif formula_str[i] == 'W':
            op_idxs.append('W') 
            paren_map.append(paren_level)
            operator_strength.append(1)
            empty_tree_nodes.append(["W",list(),list()])
            i = i+1
        elif formula_str[i] == 'M':
            op_idxs.append('M') 
            paren_map.append(paren_level)
            operator_strength.append(1)
            empty_tree_nodes.append(["M",list(),list()])
            i = i+1
            
        # Unary operators:
        elif formula_str[i] == 'X':
            op_idxs.append('X') 
            paren_map.append(paren_level)
            operator_strength.append(2)
            empty_tree_nodes.append(["X",list()])
            i = i+1
        elif formula_str[i] == 'F':
            op_idxs.append('F') 
            paren_map.append(paren_level)
            operator_strength.append(2)
            empty_tree_nodes.append(["F",list()])
            i = i+1
        elif formula_str[i] == 'G':
            op_idxs.append('G') 
            paren_map.append(paren_level)
            operator_strength.append(2)
            empty_tree_nodes.append(["G",list()])
            i = i+1
        # 'neg' with parentheses or spaces:
        elif formula_str[i:i+3] == 'neg' or formula_str[i:i+3] == 'not' and ((formula_str[i-1] == ')' or formula_str[i-1] == ' ') and (formula_str[i+3] == '(' or formula_str[i+3] == ' ')):
            op_idxs.append('neg')
            paren_map.append(paren_level)
            operator_strength.append(2)
            empty_tree_nodes.append(["neg",list()])
            i = i+3
        
        # eliminate parentheses, but map them: 
        elif formula_str[i] == '(':
            paren_level = paren_level + 1
            i = i+1
        elif formula_str[i] == ')':
            paren_level = paren_level - 1
            i = i+1
            
        # Finally, handle atoms:    
        elif formula_str[i] != ' ':
            # we encounter a character which is neither a space nor an operator (atom!)
            atom = ''.join([atom, formula_str[i]])
            
            if formula_str[i+1] in [' ', 'U', 'R', 'W', 'M', 'X', 'F', 'G', '(', ')','-']:
                # we've reached the end of the atom
                op_idxs.append(atom)
                paren_map.append(paren_level)
                operator_strength.append(-1)
                empty_tree_nodes.append(["AP",[atom]])
                atom = ''
                
            i = i+1

        else:
            # We just have an uninteresting space.
            i = i + 1
                
        index_dict = dict()
        index_dict['op_idxs'] = op_idxs
        index_dict['paren_map'] = paren_map
        index_dict['operator_strength'] = operator_strength
        index_dict['empty_tree_nodes'] = empty_tree_nodes
        
    return index_dict

def populate_node(node_dict):
    # Flag for if we've reached a leaf:
    is_leaf = False
    #print('populate_node was called!')
    node = list()
    
    formula_indexed = node_dict['op_idxs']
    paren_map = node_dict['paren_map']
    operator_strength = node_dict['operator_strength']
    empty_tree_nodes = node_dict['empty_tree_nodes'] 
    
    num_elements = len(formula_indexed)
    #print('num_elements: ', num_elements)
    
    # Check if the provided argument is a leaf:
    if len(operator_strength) == 1 and operator_strength[0] == -1:
        is_leaf = True       
        args_list = []
        node = empty_tree_nodes[0]
        #print('Leaf: ', node)
        return node, args_list, is_leaf
    
    # Move through formula segment by operator strength and 
    # parenthetical level until weakest is found:
    
    break_loops = False
    #print('paren map max: ', max(paren_map))
    for i in range(0, max(paren_map)+1): # parenthetical level
        #print('i: ', i)
        for j in range(0,3): # operator strength
            #print('j: ', j)
            for idx in range(0, num_elements): # position in indexed formula segment
                
                if paren_map[idx] == i and operator_strength[idx] == j:
                    node = empty_tree_nodes[idx]
                    break_loops = True
                    #print('Operator was: ', formula_indexed[idx])
                    break
            if break_loops:
                break
        if break_loops:
            break
    
    args_list = list()
    left_arg = dict()
    right_arg = dict()
    
    if len(node) == 3: # two-argument operator
        
        # Split all strings into the two arguments of the operator
        left_arg['op_idxs'] = formula_indexed[0:idx]
        left_arg['paren_map'] = paren_map[0:idx]
        left_arg['operator_strength'] = operator_strength[0:idx]
        left_arg['empty_tree_nodes'] = empty_tree_nodes[0:idx]
        
        right_arg['op_idxs'] = formula_indexed[idx+1:num_elements]
        right_arg['paren_map'] = paren_map[idx+1:num_elements]
        right_arg['operator_strength'] = operator_strength[idx+1:num_elements]
        right_arg['empty_tree_nodes'] = empty_tree_nodes[idx+1:num_elements]
        
        args_list = [left_arg, right_arg]
        
    elif len(node) == 2: # one-argument operator            
        
        right_arg['op_idxs'] = formula_indexed[idx+1:num_elements]
        right_arg['paren_map'] = paren_map[idx+1:num_elements]
        right_arg['operator_strength'] = operator_strength[idx+1:num_elements]
        right_arg['empty_tree_nodes'] = empty_tree_nodes[idx+1:num_elements]    
            
        args_list = [right_arg]   
            
        # if node[0] == 'AP': 
        #     is_leaf = True       
        #     print('Leaf: ', node[1])     
        #     args_list = []
            
        # else: # not a leaf
        #     right_arg['op_idxs'] = formula_indexed[idx+1:num_elements]
        #     right_arg['paren_map'] = paren_map[idx+1:num_elements]
        #     right_arg['operator_strength'] = operator_strength[idx+1:num_elements]
        #     right_arg['empty_tree_nodes'] = empty_tree_nodes[idx+1:num_elements]    
            
        #     args_list = [right_arg]   
            
    return node, args_list, is_leaf

def nest_nodes(node_dict):
    #print('nest_nodes was called!')
    node, args_list, is_leaf = populate_node(node_dict)
    #print('args_list length: ', len(args_list))
    if is_leaf:
        #print('Leaf. Node: ', node)
        pass
        
    elif len(args_list) == 1:
        #print('args_list[0]: ', args_list[0])
        node[1] = nest_nodes(args_list[0])
        #print('op had one argument. Node: ', node)
        
    elif len(args_list) == 2:

        node[1] = nest_nodes(args_list[0])
        node[2] = nest_nodes(args_list[1])
        #print('op had two arguments. Node: ', node)
        
    return node

def dump_trees_json(trees, test_name='default'):
    
    config_path = f'./test_tree_making/{test_name}.json'
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)

    # Populate file
    with open(config_path, 'w') as f:
        json.dump(obj=trees, fp = f, indent = 4)
        
        
def parse_tree(formula_str):
    
    index_dict = index_formula(formula_str)
    
    formula_indexed = index_dict['op_idxs']
    paren_map = index_dict['paren_map']
    operator_strength = index_dict['operator_strength']
    empty_tree_nodes = index_dict['empty_tree_nodes']
    #paren_map, formula = map_parentheses(formula_clean)
    #print('Tests: ')
    #print('formula length (indexed): ', len(formula_indexed))
    #print('formula string: ', formula_str)
    #print('formula_indexed: ', formula_indexed)
    #print('paren_map: ', paren_map)
    #print('operator_strength: ', operator_strength)
    #print('empty tree nodes: ', empty_tree_nodes)
    
    # Recursively generate trees from indexed formula
    # (big oof)
    full_tree = list()
    
    full_tree = nest_nodes(index_dict)
    
    
    return full_tree


def test_tree_parser(form_strs):
    trees = dict()
    trees['formula_trees'] = list()
    
    for rule in form_strs:
        tree = parse_tree(rule)
        trees['formula_trees'].append(tree)
    
    dump_trees_json(trees)
    pass


if __name__ == '__main__':
    
    rule_strings = [
        
        'GXa -> (b or c U d)',
        'a -> bUc -> Xd',
        'f and (apple ->b U (cat_box->d)) ->eggs'
    ]
    
    test_tree_parser(rule_strings)
    
    