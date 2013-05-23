#!/usr/bin/python

import socket, sys, pprint

# Constants
GLOBAL_MAX_WIDTH = 80
GLOBAL_MAX_LENGTH = 80
GLOBAL_DIM = GLOBAL_MAX_WIDTH * GLOBAL_MAX_LENGTH

MAX_WIDTH = 5
MAX_LENGTH = 5
MAX_DIM = MAX_WIDTH * MAX_LENGTH

NORTH, EAST, SOUTH, WEST = range(4)
agent_symbols = ['^', '>', 'v', '<']

MOVES = 'L R F C O B'.split()

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
    return zip(*view[::-1])

def rotate_left(view):
    return zip(*view)[::-1]

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

    pos_x, pos_y = GLOBAL_MAX_LENGTH, GLOBAL_MAX_WIDTH
    orientation = NORTH
    global_view = [[0]*(2*GLOBAL_MAX_WIDTH) for i in range(2*GLOBAL_MAX_LENGTH)]
    view = [[0]*MAX_WIDTH for i in range(MAX_LENGTH)]
    action_string = ''
    
    while True:
        view = [[0]*MAX_WIDTH for i in range(MAX_LENGTH)]
        for i in range(MAX_LENGTH):
            for j in range(MAX_WIDTH):
                if not (i == MAX_LENGTH/2 and j == MAX_WIDTH/2):
                    ch = s.recv(1)
                    view[i][j] = str(ch)
        
        simple_print(view)
        if action_string == 'l':
            orientation = (orientation - 1) % 4
        elif action_string == 'r':
            orientation = (orientation + 1) % 4
        elif action_string == 'f':
            if orientation == NORTH:
                pos_x -= 1
            elif orientation == EAST:
                pos_y += 1
            elif orientation == SOUTH:
                pos_x += 1
            elif orientation == WEST:
                pos_y -= 1

        if orientation == EAST:
            view = rotate_right(view)
        elif orientation == SOUTH:
            view = rotate_right(rotate_right(view))
        elif orientation == WEST:
            view = rotate_left(view)
        
        for i in range(MAX_LENGTH):
            for j in range(MAX_WIDTH):
                global_view[pos_x+i-2][pos_y+j-2] = view[i][j]
        
        global_view[pos_x][pos_y] = agent_symbols[orientation]
        
        strn = ''
        for row in global_view:
            for x in row:
                strn += str(x)
            strn += '\n'
        print strn
        action_string = raw_input('Enter Action(s): ')
        s.sendall(action_string)        

    sock.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())