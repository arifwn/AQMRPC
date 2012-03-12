'''
Created on Mar 12, 2012

@author: arif
'''

class StateMachine(object):
    def __init__(self):
        self.state = 'INIT'
    
    def change_state(self, state):
        self.state = state


def get_value(s_input):
    if s_input == '.true.':
        o_val = True
    elif s_input == '.false.':
        o_val = False
    elif (s_input[0] == "'") and (s_input[-1] == "'"):
        o_val = s_input[1:-1]
    else:
        try_float = False
        try:
            o_val = int(s_input)
        except ValueError:
            try_float = True
        
        if try_float:
            try:
                o_val = float(s_input)
            except ValueError:
                o_val = s_input
                
    return o_val

def get_string(value):
    if isinstance(value, float):
        s_out = '%.6g' % value
        s_out = s_out.replace('+', '')
        if (s_out.find('.') == -1) and (s_out.find('e') == -1):
            s_out += '.0'
    elif isinstance(value, bool):
        if value:
            s_out = '.true.'
        else:
            s_out = '.false.'
    elif isinstance(value, int):
        s_out = '%s' % value
    else:
        s_out = "'%s'" % value
    return s_out

    