#!/usr/bin/python

import socket, sys

# Constants
GLOBAL_MAX_WIDTH = 20
GLOBAL_MAX_LENGTH = 20
GLOBAL_DIM = GLOBAL_MAX_WIDTH * GLOBAL_MAX_LENGTH

MAX_WIDTH = 5
MAX_LENGTH = 5
MAX_DIM = MAX_WIDTH * MAX_LENGTH

# Make shift enums
NORTH, EAST, SOUTH, WEST = range(4)

agent_symbols = ['^', '>', 'v', '<']

def simple_print(view):
    string = '+' + '-'*5 + '+\n'
    for i in range(MAX_LENGTH):
        string += '|'
        for j in range(MAX_WIDTH):
            if (i == 2 and j == 2):
                string += '^'
            else:
                string += str(view[i][j])
        string += '|\n'
    string += '+' + '-'*5 + '+'
    print string
    
def rotate_right(view):
    return map(list, zip(*view[::-1]))

def rotate_left(view):
    return map(list, zip(*view)[::-1])

class State:
    def __init__(self):
        self.global_map = [['?' for j in range(2*GLOBAL_MAX_WIDTH)] for i in range(2*GLOBAL_MAX_LENGTH)]
        self.action_history = []
        self.view_history = []
        self.row, self.col = GLOBAL_MAX_LENGTH, GLOBAL_MAX_WIDTH
        self.orientation = NORTH
        self.tools = {
            'a': 0,
            'k': 0,
            'g': 0,
            'd': 0
        }

    def __str__(self):
        strn = ''
        for row in self.global_map:
            for ch in row:
                strn += str(ch)
            strn += '\n'
        strn += str((self.row, self.col))
        strn += agent_symbols[self.orientation]
        return strn
        
    def __update_orientation(self, action):
        if action == 'l':
            self.orientation = (self.orientation - 1) % 4
        elif action == 'r':
            self.orientation = (self.orientation + 1) % 4

    def __view_changed(self, view):
        try:
            last_view = self.view_history[-1]
        except IndexError:
            last_view = []
        return (last_view != view)
    
    def __normalize_view(self, view):
        # Normalize view buffer
        if self.orientation == NORTH:
            return view
        elif self.orientation == EAST:
            return rotate_right(view)
        elif self.orientation == SOUTH:
            return rotate_right(rotate_right(view))
        elif self.orientation == WEST:
            return rotate_left(view)
    
    def apply_action(self, action):
        # Normalize input
        action = action.lower()
        self.action_history.append(action)
        
        if action == 'l':
            self.orientation = (self.orientation - 1) % 4
            return True
        elif action == 'r':
            self.orientation = (self.orientation + 1) % 4
            return True
        else:
            d_row = d_col = 0
            if self.orientation == NORTH:   d_row -= 1
            elif self.orientation == EAST:  d_col += 1
            elif self.orientation == SOUTH: d_row += 1
            elif self.orientation == WEST:  d_col -= 1
            
            new_row, new_col = self.row+d_row, self.col+d_col
            cell_ahead = self.global_map[new_row][new_col] 
            
            if action == 'f':
                if cell_ahead in ['*', 'T', '-']:
                    return False
                
                self.row, self.col = new_row, new_col
                if cell_ahead in ['a', 'k', 'g', 'd']:
                    self.tools[cell_ahead] += 1
                return True    
                
            elif action == 'c':
                if cell_ahead == 'T' and self.tools['a']:
                    return True
            elif action == 'o':
                if cell_ahead == '-' and self.tools['k']:
                    return True
            elif action == 'b':
                if cell_ahead in ['*', 'T', '-'] and self.tools['d']:
                    self.tools['d'] -= 1
                    return True
            return False

    def update_map(self, view):
        self.view_history.append(view)
        new_view = self.__normalize_view(view)
        # Update global map
        for i in range(MAX_LENGTH):
            for j in range(MAX_WIDTH):
                self.global_map[self.row+i-2][self.col+j-2] = new_view[i][j]
        self.global_map[self.row][self.col] = agent_symbols[self.orientation]

def main():
    # Get and process command line arguments. 
    # TODO: Would really like to use 'optparse' if permitted.
    try:
        port = int(sys.argv[1])
    except (IndexError, TypeError):
        print 'Usage: {program_name} <port>'.format(program_name=sys.argv[0])
        return 1

    # Create a TCP/IP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', port))
    except socket.error:
        print 'Could not bind to port: {0}'.format(port)
        return 1

    action_string = ''
    state = State()
    while True:
        # View buffer
        view = [[0 for j in range(MAX_WIDTH)] for i in range(MAX_LENGTH)]
        for i in range(MAX_LENGTH):
            for j in range(MAX_WIDTH):
                if not (i == MAX_LENGTH/2 and j == MAX_WIDTH/2):
                    ch = s.recv(1)
                    view[i][j] = str(ch)
        simple_print(view)

        state.update_map(view)
        
        print state
        
        action_string = raw_input('Enter Action(s): ')
        
        state.apply_action(action_string)
        
        s.sendall(action_string)

    sock.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())