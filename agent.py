#!/usr/bin/python

import socket, sys, pprint

# Constants
MAX_LEN = 5*5

def simple_print(view):
    string = '+' + '-'*5 + '+\n'
    for i in range(0, 5):
        string += '|'
        for j in range(0, 5):
            if (i == 2 and j == 2):
                string += '^'
            else:
                string += view[i][j]
        string += '|\n'
    string += '+' + '-'*5 + '+'
    print string
    
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
    s.connect(('localhost', port))

    view = [[0]*5 for i in range(5)]
    #pprint.pprint(view)
    while True:
        for i in range(0, 5):
            for j in range(0, 5):
                if not (i == 2 and j == 2):
                    ch = s.recv(1)  
                    view[i][j] = str(ch)
        simple_print(view)        
        action_string = raw_input('Enter Action(s): ')
        s.sendall(action_string)

    # while True:
    #     raw_environment_string = ''
    #     while len(raw_environment_string) < MAX_LEN - 1:
    #         raw_environment_string += s.recv(MAX_LEN)     
    #     print raw_environment_string
    #     action_string = raw_input('Enter Action(s): ')
    #     s.sendall(action_string)

    sock.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())