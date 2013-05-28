#!/usr/bin/python

import sys, socket, optparse

# Constants
GLOBAL_MAX_WIDTH = 20
GLOBAL_MAX_LENGTH = 20
GLOBAL_DIM = GLOBAL_MAX_WIDTH * GLOBAL_MAX_LENGTH

MAX_WIDTH = 5
MAX_LENGTH = 5
MAX_DIM = MAX_WIDTH * MAX_LENGTH

UNKNOWN_SYMBOL = '?'

# Make shift enums
NORTH, EAST, SOUTH, WEST = range(4)

AGENT_SYMBOL = ('^', '>', 'v', '<')

def backtrace(parent, start, end):
    path = [end]
    moves = [end.last_move]
    while not path[-1] == start:
        the_parent = parent[path[-1]]
        path.append(the_parent)
        moves.append(the_parent.last_move)
    moves.pop()
    moves.reverse()
    return moves

def BFS(state, dynamite=True, goal_test=lambda node: node.tools['g'] and (node.row, node.col) == (0, 0)):
    queue = []
    parent = {}
    queue.append(state)
    parent[state] = state
    while queue:
        node = queue.pop(0)
        if goal_test(node):
            return backtrace(parent, state, node)
        for successor in node.successors(dynamite):
            if not successor in parent:
                parent[successor] = node
                queue.append(successor)

def get_action(state):
    explore = BFS(state, dynamite=False, goal_test=lambda node:node.terra_incognita())
    if explore:
        return explore
    else:
        return raw_input('Enter Action(s): ')

class State:
    def __init__(self, environment_map={}, position=(0, 0), orientation=NORTH, tools={'a': 0, 'k': 0, 'd': 0, 'g': 0,}):
        self.map = environment_map.copy()
        self.tools = tools.copy()
        self.row, self.col = position
        self.orientation = orientation
        self.last_move = ''

    def terra_incognita(self):
        for d_row in range(-2, 3):
            for d_col in range(-2, 3):
                if abs(d_row) == 2 or abs(d_col) == 2:
                    if not (self.row+d_row, self.col+d_col) in self.map:
                        return True
        return False
    
    def move_history(self):
        return self.action_history
        
    def current_cell(self):
        return self.map.get((self.row, self.col))
    
    def successors(self, use_dynamite=True):
        possible_actions = ['l', 'r', 'f', 'c', 'o']
        if use_dynamite:
            possible_actions.append('b')
        for a in possible_actions:
            successor = self.apply(a)
            if not (self == successor or successor.is_over()): 
                yield successor

    def apply(self, action):
        # No action is valid when the game is over
        # Normalize input
        action = action.lower()

        new_state = State(self.map, (self.row, self.col), self.orientation, self.tools)
        new_state.last_move = action

        if self.is_over():
            return new_state
        else:
            if action == 'l':
                new_state.orientation = (new_state.orientation - 1) % 4
                new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
            elif action == 'r':
                new_state.orientation = (new_state.orientation + 1) % 4
                new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
            else:
                new_row, new_col = new_state.position_ahead()
                cell_ahead = new_state.map.get((new_row, new_col))
                
                if action == 'f':
                    if not cell_ahead or cell_ahead in ('*', 'T', '-'):
                        return new_state
                    else:
                        new_state.map[(new_state.row, new_state.col)] = ' '
                        new_state.row, new_state.col = new_row, new_col
                        if not cell_ahead == '~': 
                            new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
                            if cell_ahead in new_state.tools.keys():
                                new_state.tools[cell_ahead] += 1
                elif action == 'c':
                    if cell_ahead == 'T' and new_state.tools['a']:
                        new_state.map[(new_row, new_col)] = ' '
                elif action == 'o':
                    if cell_ahead == '-' and new_state.tools['k']:
                        new_state.map[(new_row, new_col)] = ' '                    
                elif action == 'b':
                    if cell_ahead in ('*', 'T', '-') and new_state.tools['d']:
                        new_state.map[(new_row, new_col)] = ' '
                        new_state.tools['d'] -= 1

            return new_state

    def update_map(self, file_object):
        if not self.is_over():
            for i in range(-2, 3):
                for j in range(-2, 3):
                    if self.orientation == NORTH:
                        position = self.row+i, self.col+j
                    elif self.orientation == EAST:
                        position = self.row+j, self.col-i
                    elif self.orientation == SOUTH:
                        position = self.row-i, self.col-j
                    elif self.orientation == WEST:
                        position = self.row-j, self.col+i

                    if (i == 0 and j == 0):
                        ch = AGENT_SYMBOL[self.orientation]
                    else:
                        ch = file_object.read(1)

                    self.map[position] = str(ch)
    
    def won(self):
        return (self.row, self.col) == (0, 0) and self.tools['g']
        
    def lost(self):
        return self.map.get((self.row, self.col)) == '~'
        
    def is_over(self):
        return self.won() or self.lost()
    
    def map_to_list(self):
        coordinates = self.map.keys()
        try:
            max_row, max_col = map(max, zip(*coordinates))
            min_row, min_col = map(min, zip(*coordinates))  
            return [[self.map.get((i, j), '?') for j in range(min_col, max_col+1)] for i in range(min_row, max_row+1)]
        except ValueError:
            return []
    
    def __str__(self):
        result = []
        result.append('\n'.join([''.join(row) for row in self.map_to_list()]))
        result.append('Position: {pos}'.format(pos=(self.row, self.col)))
        result.append('Orientation: {orient}'.format(orient=('N', 'E', 'S', 'W')[self.orientation]))
        result.append('Aresenal: {{Axe: {a}, Key: {k}, Gold: {g}, Dynamite: {d}}}'.format(**self.tools))
        #if self.action_history:
        #    result.append(''.join(self.action_history))
        return '\n'.join(result)

    def __key(self):
        attr = [self.row, self.col, self.orientation]
        attr.extend(self.map.items())
        attr.extend(self.tools.items())
        return tuple(attr)

    def position(self):
        return (self.row, self.col)

    def orientation(self):
        return self.orientation

    def tools(self):
        return self.tools

    def position_ahead(self):
        d_row = d_col = 0     
        if self.orientation == NORTH:   d_row -= 1
        elif self.orientation == EAST:  d_col += 1
        elif self.orientation == SOUTH: d_row += 1
        elif self.orientation == WEST:  d_col -= 1
        return self.row+d_row, self.col+d_col

    def __eq__(self, other):
        return type(self) == type(other) and self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

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
    state.update_map(f)
    while not state.is_over():                
        print state
        #print '\n'.join([str(st) for st in state.successors()])
        #print state.effective_actions()
        #print '\n'.join([str(st) for st in state.terra_incognita_1()])
        action_string = get_action(state)
        #action_string = raw_input('Enter Action(s): ')
        print action_string
        for a in action_string:
            print a
            state = state.apply(a)
            s.sendall(a)
            state.update_map(f)
            
    s.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
