#!/usr/bin/python

import socket, sys, optparse, json

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

actions = []
with open('actions.json', 'r') as infile:
	actions = json.load(infile)	
	
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
        self.won = self.lost = False

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
        result.append('\n'.join([str(a) for a in self.neighbors((self.row, self.col))]))
        result.append(' '.join(str(coord) for coord in self.explore((self.row, self.col))))
        return '\n'.join(result)

    def is_over(self):
        return self.won or self.lost

    def action_is_effective(self, action):
        pass

    def apply_action(self, action):
        # Normalize input
        action = action.lower()
        self.action_history.append(action)
      	with open('actions.json', 'w') as outfile:
      		json.dump(self.action_history, outfile)
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
                
                self.lost = (cell_ahead == '~')
                
                self.won = (self.tools['g'] and self.row == GLOBAL_MAX_LENGTH and self.col == GLOBAL_MAX_WIDTH)
                
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

    def neighbors(self, coord):
        x, y = coord
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if bool(dx) ^ bool(dy): # eXclusive OR
                    if 0 <= x+dx < 2*GLOBAL_MAX_LENGTH and 0 <= y+dy < 2*GLOBAL_MAX_LENGTH:
                        if not self.global_map[x+dx][y+dy] in ['*', 'T', '-', '~']:
                            yield (x+dx, y+dy)
                    
    def explore(self, start):
        parent = {}
        queue = []
        queue.append(start)
        while queue:
            node = queue.pop(0)
            (x, y) = node
            if self.global_map[x][y] in self.tools.keys():
                path = [node]
                while not path[-1] == start:
                    path.append(parent[path[-1]])
                path.reverse()
                return path                
            for neighbor in self.neighbors(node):
                if not neighbor in parent:
                    parent[neighbor] = node
                    queue.append(neighbor)
        return []

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
    while not state.is_over():
        state.update_map(f)
        print state

        #action_string = raw_input('Enter Action(s): ')
        
        try:
            action_string = actions.pop(0)
        except IndexError:
            action_string = raw_input('Enter Action(s): ')
        
        state.apply_action(action_string)

        s.sendall(action_string)

    s.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
