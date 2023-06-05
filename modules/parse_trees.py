from pathlib import Path
import os
import sys
import json
for i in range(5):
    if not (Path.cwd()/"modules").exists(): os.chdir(Path.cwd().parent.as_posix())
    else: sys.path.append(Path.cwd().as_posix())

from pathlib import Path
import numpy as np

def index_formula(raw_str):
    # Identifies operators and atoms and indexes them.
    op_idxs = list()
    paren_map = list()
    
    # Add extra terminal spaces for processing purposes:
    print('length of raw_str: ' , len(raw_str))
    formula_str = ''.join([' ',raw_str, '  '])
    print('formula_str: ', formula_str)
    print('length of formula_str: ' , len(formula_str))
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
            i = i+2
        #'and' surrounded by ')', '(', and/or spaces:
        elif formula_str[i:i+3] == 'and' and ((formula_str[i-1] == ')' or formula_str[i-1] == ' ') and (formula_str[i+3] == '(' or formula_str[i+3] == ' ')):
            op_idxs.append('and')
            paren_map.append(paren_level)
            i = i+3
        # '->':
        elif formula_str[i:i+2] == '->':
            op_idxs.append('->')
            paren_map.append(paren_level)
            i = i+2
            
        # Binary operators:
        elif formula_str[i] == 'U':
            op_idxs.append('U')  
            paren_map.append(paren_level)
            i = i+1
        elif formula_str[i] == 'R':
            op_idxs.append('R') 
            paren_map.append(paren_level)
            i = i+1
        elif formula_str[i] == 'W':
            op_idxs.append('W') 
            paren_map.append(paren_level)
            i = i+1
        elif formula_str[i] == 'M':
            op_idxs.append('M') 
            paren_map.append(paren_level)
            i = i+1
            
        # Unary operators:
        elif formula_str[i] == 'X':
            op_idxs.append('X') 
            paren_map.append(paren_level)
            i = i+1
        elif formula_str[i] == 'F':
            op_idxs.append('F') 
            paren_map.append(paren_level)
            i = i+1
        elif formula_str[i] == 'G':
            op_idxs.append('G') 
            paren_map.append(paren_level)
            i = i+1
        # 'neg' with parentheses or spaces:
        elif formula_str[i:i+3] == 'neg' and ((formula_str[i-1] == ')' or formula_str[i-1] == ' ') and (formula_str[i+3] == '(' or formula_str[i+3] == ' ')):
            op_idxs.append('neg')
            paren_map.append(paren_level)
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
                atom = ''
                
            i = i+1

        else:
            # We just have an uninteresting space.
            i = i + 1
                
    return op_idxs, paren_map



def dump_trees_json(trees, test_name='default'):
    
    config_path = f'./test_tree_making/{test_name}.json'
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)

    # Populate file
    with open(config_path, 'w') as f:
        json.dump(obj=trees, fp = f, indent = 4)
        
def parse_tree(formula_str):
    tree = list()
    
    formula_indexed, paren_map = index_formula(formula_str)
    
    #paren_map, formula = map_parentheses(formula_clean)
    print('Tests: ')
    print('formula length (indexed): ', len(formula_indexed))
    print('formula_indexed: ', formula_indexed)
    print('paren_map: ', paren_map)
    
    
    return tree


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
        'f and (a -> b U (c->d)) -> e'
    ]
    
    test_tree_parser(rule_strings)
    
    