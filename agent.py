#!/usr/bin/python

import sys, socket, optparse, heapq, itertools

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

def manhattan_distance(p, q):
    p1, p2 = p
    q1, q2 = q
    return abs(p1-q1) + abs(p2-q2)

def a_star(start, goal_test=lambda node: False, use_concrete_goal_coordinate = False, goal_coordinate=(0, 0), use_dynamite=True, use_tools=True, heuristic = lambda node, goal_coordinate: manhattan_distance((node.row, node.col), goal_coordinate)):
    if not use_concrete_goal_coordinate:
        heuristic = lambda node, goal_coordinate: 0
    
    open_set = set()
    closed_set = set()
    open_priq = []
    
    f = {}
    g = {}
    
    g[start] = 0
    f[start] = g[start] + heuristic(start, goal_coordinate)
    
    open_set.add(start)
    open_priq.append((f[start], start))
    
    while open_set:
        f_value, node = heapq.heappop(open_priq)
        print node
        #print use_concrete_goal_coordinate
        #print goal_coordinate
        #print use_dynamite
        if use_concrete_goal_coordinate:
            if (node.row, node.col) == goal_coordinate:
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
                
                gold_pos = successor.gold_position()
                if gold_pos:
                    heuristic = lambda node, goal_coordinate: manhattan_distance((node.row, node.col), gold_pos)
                else:
                    heuristic = lambda node, goal_coordinate: 0
                f[successor] = g[successor] + heuristic(successor, goal_coordinate)
                if not successor in open_set:
                    open_set.add(successor)
                    heapq.heappush(open_priq, (f[successor], successor))
    return None

def get_action(state):  
    if state.tools['g']:
        win_path = a_star(state, goal_coordinate=(0,0), use_dynamite=False, use_tools=False, use_concrete_goal_coordinate=True)
        if win_path:
            return win_path
    else:
        
        explore_path = a_star(state, goal_test = lambda node: node.current_cell() == 'g' or not state.ordered_exploration_nodes() or state.reduces_terra_incognita(node.row, node.col), use_dynamite=False)
        if explore_path:
            return explore_path

        gold_pos = state.gold_position()
        if gold_pos:
            collect_gold = a_star(state, goal_coordinate=gold_pos, use_concrete_goal_coordinate=True, use_dynamite=False)
            if collect_gold:
                return collect_gold

        try:
            closest_tool = state.ordered_position_of(['d', 'k', 'a']).pop()
        except IndexError:
            closest_tool = None    
        if closest_tool:
            collect_tool = a_star(state, goal_coordinate=closest_tool, use_concrete_goal_coordinate=True, use_dynamite=False)
            if collect_tool:
                return collect_tool

        if state.tools['d']:
            gold_pos = state.gold_position()
            if gold_pos:
                collect_gold = a_star(state, goal_coordinate=gold_pos, use_concrete_goal_coordinate=True, use_dynamite=True, heuristic=lambda node, goal_coordinate: -100*node.tools['d'] + manhattan_distance((node.row, node.col), goal_coordinate))
                if collect_gold:
                    return collect_gold

            try:
                closest_tool = state.ordered_position_of(['d', 'k', 'a']).pop()
            except IndexError:
                closest_tool = None    
            if closest_tool:
                collect_tool = a_star(state, goal_coordinate=closest_tool, use_concrete_goal_coordinate=True, use_dynamite=True)
                if collect_tool:
                    return collect_tool
            
            explore_path = a_star(state, goal_test = lambda node: state.reduces_terra_incognita(node.row, node.col), use_dynamite=True)
            if explore_path:
                return explore_path        
            
            # try:
            #     closest_explore = state.ordered_exploration_nodes().pop()
            # except IndexError:
            #     closest_explore = None
            # if closest_explore:
            #     explore_path = a_star(state, goal_coordinate=closest_explore, use_concrete_goal_coordinate=True, use_dynamite=d)
            #     if explore_path:
            #         return explore_path
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
        rel_up, rel_down, rel_left, rel_right = self.neighborhood()
        up = self.map.get(rel_up, '?')
        down = self.map.get(rel_down, '?')
        left = self.map.get(rel_left, '?')
        right = self.map.get(rel_right, '?')
        possible_actions = []
        if up not in ('*', 'T', '-', '?', '~'):
            possible_actions.append('f')
        if down not in ('*', 'T', '-', '?', '~'):
            possible_actions.append('llf')
        if left not in ('*', 'T', '-', '?', '~'):
            possible_actions.append('lf')
        if right not in ('*', 'T', '-', '?', '~'):
            possible_actions.append('rf')
        if use_tools:
            if self.tools['a']:
                if up == 'T':
                    possible_actions.append('cf')
                if down == 'T':
                    possible_actions.append('llcf')
                if left == 'T':
                    possible_actions.append('lcf')
                if right == 'T':
                    possible_actions.append('rcf')
            if self.tools['k']:
                if up == '-':
                    possible_actions.append('of')
                if down == '-':
                    possible_actions.append('llof')
                if left == '-':
                    possible_actions.append('lof')
                if right == '-':
                    possible_actions.append('rof')
        if use_dynamite:
            if self.tools['d']:
                if up in ('*', 'T', '-'):
                    possible_actions.append('bf')
                if down in ('*', 'T', '-'):
                    possible_actions.append('llbf')
                if left in ('*', 'T', '-'):
                    possible_actions.append('lbf')
                if right in ('*', 'T', '-'):
                    possible_actions.append('rbf')
        for a in possible_actions:
            successor = self.apply(a)
            # Only return successor states that are not losing states or states that have actually changed
            if not (self == successor or successor.lost()):
#            if not successor.lost():
                yield (a, successor)

    def apply(self, actions):
        # No action is valid when the game is over
        # Normalize input
        actions = actions.lower()

        new_state = State(self.map, (self.row, self.col), self.orientation, self.tools)

        for action in actions:
            if new_state.is_over():
                return new_state
            else:
                if action == 'l':
                    new_state.orientation = (new_state.orientation - 1) % 4
                    new_state.map[(new_state.row, new_state.col)] = ' '
                    #new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
                elif action == 'r':
                    new_state.orientation = (new_state.orientation + 1) % 4
                    new_state.map[(new_state.row, new_state.col)] = ' '
                    #new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
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
                                #new_state.map[(new_state.row, new_state.col)] = AGENT_SYMBOL[new_state.orientation]
                                new_state.map[(new_state.row, new_state.col)] = ' '
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

    def position_of_items(self, items):
        max_row, max_col = self.map_coord(max)
        min_row, min_col = self.map_coord(min)
        for i in range(min_row, max_row+1):
            for j in range(min_col, max_col+1):
                if self.map.get((i, j)) in items:
                    yield (i, j)

    def ordered_position_of(self, items):
        tool_positions = list(self.position_of_items(items))
        return sorted(tool_positions, reverse=True, key=lambda position: manhattan_distance((self.row, self.col), position))

    def gold_position(self):
	    try:
	        return self.ordered_position_of(['g']).pop()
	    except IndexError:
	        return None

    def explored(self):
        max_row, max_col = self.map_coord(max)
        min_row, min_col = self.map_coord(min)
        for i in range(min_row, max_row+1):
            for j in range(min_col, max_col+1):
                if self.map.get((i, j)) in (' ', 'a', 'k', 'g', 'd') and self.reduces_terra_incognita(i, j):
                    return False
        return True
		
    def exploration_nodes(self):
        max_row, max_col = self.map_coord(max)
        min_row, min_col = self.map_coord(min)
        for i in range(min_row, max_row+1):
            for j in range(min_col, max_col+1):
                if self.map.get((i, j)) in (' ', 'a', 'k', 'g', 'd') and self.reduces_terra_incognita(i, j):
                    yield (i, j)

    def ordered_exploration_nodes(self):
        explore_node_list = list(self.exploration_nodes())
        return sorted(explore_node_list, reverse=True, key=lambda position: manhattan_distance((self.row, self.col), position))

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

    def neighborhood(self):
        d_row = d_col = 0     
        if self.orientation == NORTH:   
            return (self.row-1, self.col), (self.row+1, self.col), (self.row, self.col-1), (self.row, self.col+1)
        elif self.orientation == EAST:
            return (self.row, self.col+1), (self.row, self.col-1), (self.row-1, self.col), (self.row+1, self.col)
        elif self.orientation == SOUTH:
            return (self.row+1, self.col), (self.row-1, self.col), (self.row, self.col+1), (self.row, self.col-1)
        elif self.orientation == WEST:
            return (self.row, self.col-1), (self.row, self.col+1), (self.row+1, self.col), (self.row-1, self.col)

    def __key(self):
        attr = [self.row, self.col]#, self.orientation]
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

    f = s.makefile('r', MAX_DIM)
    state = State()
    state.update_map(f)
    while not state.is_over():                
        print state
        #print 'SUCCESSORS:'
        #print '\n'.join([str(suc) for act, suc in state.successors()])
        # Get the list of actions to perform
        actions = [a for action in get_action(state) for a in list(action)]
        #actions = raw_input('Enter move: ')
        #print actions
        for a in actions:
            state = state.apply(a)
            s.sendall(a)
            state.update_map(f)
    s.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
