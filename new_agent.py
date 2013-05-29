#!/usr/bin/python

import sys, socket, optparse, heapq

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

# TODO: docstring and comments
    
def retrace_path(node):
    path = []
    has_parent = True
    while has_parent:
        try:
            action, node = node.parent
            path.append(action)
        except AttributeError:
            has_parent = False
    path.reverse()
    return path

def a_star(start, goal_test, use_dynamite=True, use_tools=True, concrete_target_coordinate=False, target_coordinate=(0, 0), heuristic=lambda node: 0):
    open_set = set()
    closed_set = set()
    open_priq = []
    
    f = {}
    g = {}
    
    g[start] = 0
    f[start] = g[start] + heuristic(start)
    
    open_set.add(start)
    open_priq.append((f[start], start))
    
    while open_set:
        f_value, node = heapq.heappop(open_priq)
        if concrete_target_coordinate:
            if (node.row, node.col) == target_coordinate:
                return retrace_path(node)
        else:
            if goal_test(node):
                return retrace_path(node)
        open_set.remove(node)
        closed_set.add(node)
        for action, successor in node.successors(use_dynamite, use_tools):
            tentative_g = g[node] + 1
            if successor in closed_set and tentative_g >= g[successor]:
                continue
            
            if not successor in open_set or tentative_g < g[successor]:
                successor.parent = (action, node)
                g[successor] = tentative_g
                f[successor] = g[successor] + heuristic(successor)
                if not successor in open_set:
                    open_set.add(successor)
                    heapq.heappush(open_priq, (f[successor], successor))
    return None
    
# TODO: Actually figure out the order in which to do things, i.e. first explore as much as possible without dynamite, 
#       if gold is seen, go to it and this time use dynamite, otherwise go to tool without dynamite, etc. etc.
#       for now, don't worry about doing all this in-place in the BFS, just so seperate BFS's with different parameters (goal_test functions)
#       etc. until we figure out the correct order of operations, then improve upon performance
def get_action(state):
    
    def more_tools(node):
        for t in ('a', 'd', 'k'):
            if state.tools[t] < node.tools[t]:
                return True
        return False
    
    if state.tools['g']:
        win_path = a_star(state, use_dynamite=False, use_tools=False, goal_test=lambda node: (node.row, node.col) == (0, 0))
        if win_path:
            return win_path
    else:
        if state.explored():
            collect_gold = a_star(state, use_dynamite=True, goal_test=lambda node: node.tools['g'])
            if collect_gold:
                return collect_gold
            else:
                collect_tools = a_star(state, use_dynamite=True, goal_test=more_tools)
                if collect_tools:
                    return collect_tools
        else:
            explore_path = a_star(state, use_dynamite=False, use_tools=True, goal_test=lambda node:node.reduces_terra_incognita(node.row, node.col))
            if explore_path:
                return explore_path
            else:
                explore_path = a_star(state, use_dynamite=True, goal_test=lambda node:node.reduces_terra_incognita(node.row, node.col))
                if explore_path:
                    return explore_path
    return raw_input('Enter Action(s): ')

class State:
    def __init__(self, environment_map={}, position=(0, 0), orientation=NORTH, tools={'a': 0, 'k': 0, 'd': 0, 'g': 0,}):
        self.map = environment_map.copy()
        self.tools = tools.copy()
        self.row, self.col = position
        self.orientation = orientation
        self.last_move = ''

    def heuristic(self):
        return 0

    def reduces_terra_incognita(self, row, col):
        for d_row in range(-2, 3):
            for d_col in range(-2, 3):
                if abs(d_row) == 2 or abs(d_col) == 2:
                    if not (row+d_row, col+d_col) in self.map:
                        return True
        return False
    
    def successors(self, use_dynamite=True, use_tools=True):
        possible_actions = ['l', 'r', 'f']
        if use_tools:
            possible_actions.extend(['c', 'o'])
        if use_dynamite:
            possible_actions.append('b')
        for a in possible_actions:
            successor = self.apply(a)
            # Only return successor states that are not losing states or states that have actually changed
            if not (self == successor or successor.lost()): 
                yield (a, successor)

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
    
    def map_coord(self, fn):
        try:
            coordinates = self.map.keys()
            return map(fn, zip(*coordinates))
        except ValueError:
            return []

    def map_to_list(self):
		max_row, max_col = self.map_coord(max)
		min_row, min_col = self.map_coord(min)
		return [[self.map.get((i, j), '?') for j in range(min_col, max_col+1)] for i in range(min_row, max_row+1)]

    def position_of(self, item):
        max_row, max_col = self.map_coord(max)
        min_row, min_col = self.map_coord(min)
        for i in range(min_row, max_row+1):
            for j in range(min_col, max_col+1):
                if self.map.get((i, j)) == item:
                    yield (i, j)
					
    def explored(self):
        max_row, max_col = self.map_coord(max)
        min_row, min_col = self.map_coord(min)
        for i in range(min_row, max_row+1):
            for j in range(min_col, max_col+1):
                if self.map.get((i, j)) == ' ' and self.reduces_terra_incognita(i, j):
                    return False
        return True

    def position(self):
        return (self.row, self.col)

    def orientation(self):
        return self.orientation

    def tools(self):
        return self.tools

    def current_cell(self):
        return self.map.get((self.row, self.col))

    def position_ahead(self):
        d_row = d_col = 0     
        if self.orientation == NORTH:   d_row -= 1
        elif self.orientation == EAST:  d_col += 1
        elif self.orientation == SOUTH: d_row += 1
        elif self.orientation == WEST:  d_col -= 1
        return self.row+d_row, self.col+d_col

    def __key(self):
        attr = [self.row, self.col, self.orientation]
        attr.extend(self.map.items())
        attr.extend(self.tools.items())
        return tuple(attr)

    def __eq__(self, other):
        return type(self) == type(other) and self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        result = []
        result.append('\n'.join([''.join(row) for row in self.map_to_list()]))
        result.append('Position: {pos}'.format(pos=(self.row, self.col)))
        result.append('Orientation: {orient}'.format(orient=('N', 'E', 'S', 'W')[self.orientation]))
        result.append('Aresenal: {{Axe: {a}, Key: {k}, Gold: {g}, Dynamite: {d}}}'.format(**self.tools))
        return '\n'.join(result)


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

    # TODO: Create a world model class to encapsulate these operations
    #       Included in this is making the map_update method consistent
    #       with the immutable state.
    f = s.makefile('r', MAX_DIM)
    state = State()
    state.update_map(f)
    while not state.is_over():                
        print state
        # Get the list of actions to perform
        actions = get_action(state)
        # so we can perform more than one action each time to avoid recomputing values
        for a in actions:
            state = state.apply(a)
            s.sendall(a)
            state.update_map(f)
    s.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
