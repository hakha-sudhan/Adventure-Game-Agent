#!/usr/bin/python

import socket, sys, optparse

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
    """
    Instances of this class are mutable objects encapsulating the state of the game. 
    
    State object only mutated when fed a new view and also if apply_action() returns True 
    """

    def __init__(self):
        self.global_map = [['?' for j in range(2*GLOBAL_MAX_WIDTH)] for i in range(2*GLOBAL_MAX_LENGTH)]
        self.action_history = []
        self.row, self.col = GLOBAL_MAX_LENGTH, GLOBAL_MAX_WIDTH
        self.orientation = NORTH
        self.tools = {
            'a': 0,
            'k': 0,
            'g': 0,
            'd': 0,
        }

    def __str__(self):
        result = []
        # Agent's view of the map
        # TODO: Print only the part of the map we have knowledge of, not the entire map 
        result.append('\n'.join([''.join(row) for row in self.global_map]))
        # Agent's position (note deliberate use of tuple)
        result.append('Position: {pos}'.format(pos=(self.row, self.col)))
        # Agent's orientation (Positional tuple created on the fly)
        result.append('Orientation: {orient}'.format(orient=('N', 'E', 'S', 'W')[self.orientation]))
        # Tools in the agent's arsenal
        result.append('Aresenal: {{Axe: {a}, Key: {k}, Gold: {g}, Dynamite: {d}}}'.format(**self.tools))
        result.append('Moves: {num_moves}'.format(num_moves=len(self.action_history)))
        return '\n'.join(result)
    
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
                if cell_ahead in self.tools.keys():
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

    def update_map(self, f):
        r = c = 0
        for i in range(-2, 3):
            for j in range(-2, 3):
                if self.orientation == NORTH:
                    r, c = self.row+i, self.col+j
                elif self.orientation == EAST:
                    r, c = self.row+j, self.col-i
                elif self.orientation == SOUTH:
                    r, c = self.row-i, self.col-j
                elif self.orientation == WEST:
                    r, c = self.row-j, self.col+i

                if (i == 0 and j == 0):
                    ch = agent_symbols[self.orientation]
                else:
                    ch = f.read(1)

                self.global_map[r][c] = str(ch)
        
        # view = [[0 for j in range(MAX_WIDTH)] for i in range(MAX_LENGTH)]
        # for i in range(MAX_LENGTH):
        #     for j in range(MAX_WIDTH):
        #         if not (i == MAX_LENGTH/2 and j == MAX_WIDTH/2):
        #             ch = f.read(1)
        #             view[i][j] = str(ch)
        # 
        # new_view = self.__normalize_view(view)
        # Update global map
        # for i in range(MAX_LENGTH):
        #     for j in range(MAX_WIDTH):
        #         self.global_map[self.row+i-2][self.col+j-2] = new_view[i][j]
        # self.global_map[self.row][self.col] = agent_symbols[self.orientation]
        # #f.close()

def main():
    # Get and process command line arguments. 
    parser = optparse.OptionParser(usage='usage: %prog [options]', version='%prog version 0.1')
    parser.add_option('-p', '--port', action="store", type="int", dest="port", help='server port number to bind to (between 1025 and 65535)')
    options, args = parser.parse_args()

    # Make port a "required option"
    if not options.port:
        parser.print_help()
        return 1
    
    # Create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(('localhost', options.port))
    except socket.error:
        print 'Could not bind to port: {0}'.format(options.port)
        return 1

    action_string = ''
    f = s.makefile('r', MAX_DIM)
    state = State()
    while True:
        state.update_map(f)
        
        print state

        action_string = raw_input('Enter Action(s): ')
        
        state.apply_action(action_string)

        s.sendall(action_string)

    s.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())