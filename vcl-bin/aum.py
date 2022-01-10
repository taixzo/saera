import sys
import os
import argparse

MODE = 'NORMAL'
CURSOR = 0
CURSOR2 = 0
MIN_PHONETIC = 3

editbuffer = ''
yankbuffer = ''
STATELIST = []
filename = ''
file = None

# Utility functions
def safe_rindex(s, n):
    try:
        return s.rindex(n) + 1
    except ValueError:
        return 0
def safe_index(s, n):
    try:
        return s.index(n) + 1
    except ValueError:
        return len(s)
def segment_around(n, separator):
    return editbuffer[safe_rindex(editbuffer[:n], separator):safe_index(editbuffer[n:], separator)+n]





# Editor functions
def word():
    global CURSOR
    new_cursor = safe_index(editbuffer[CURSOR:], ' ') + CURSOR
    if MODE=='SELECT':
        if CURSOR==CURSOR2:
            new_cursor = max(new_cursor-2, CURSOR)
        else:
            if new_cursor < len(editbuffer):
                new_cursor = max(safe_index(editbuffer[new_cursor:], ' ') - 2, 0) + new_cursor
    if new_cursor < len(editbuffer):
        CURSOR = new_cursor
    return print_word()

def back():
    global CURSOR
    CURSOR = safe_rindex(editbuffer[:max(CURSOR-1, 0)], ' ')
    return print_word()

def print_word():
    return segment_around(CURSOR, ' ')

def line():
    global CURSOR
    new_cursor = safe_index(editbuffer[CURSOR:], '\n') + CURSOR
    if new_cursor < len(editbuffer):
        CURSOR = new_cursor
    return print_line()

def print_line():
    return segment_around(CURSOR, '\n')

def clump():
    pass

def line_list():
    pass

def clump_list():
    pass

def undo():
    global editbuffer, CURSOR, MODE
    STATELIST.pop() # undo the "undo" command
    editbuffer, CURSOR, MODE = STATELIST.pop()
    return editbuffer[CURSOR:].split()[0]

def yank():
    global yankbuffer, MODE
    if MODE=='SELECT':
        yankbuffer = editbuffer[min(CURSOR, CURSOR2):max(CURSOR, CURSOR2)+1]
        MODE = 'NORMAL'
        return 'yanked ' + (yankbuffer if len(yankbuffer) < 100 else str(yankbuffer.count(' ')+1) + ' words')

def paste():
    global editbuffer, MODE
    if MODE=='SELECT':
        editbuffer = editbuffer[:min(CURSOR, CURSOR2)] + yankbuffer + editbuffer[max(CURSOR,CURSOR2)+1:]
        MODE='NORMAL'
    else:
        editbuffer = editbuffer[:CURSOR] + yankbuffer +' '+ editbuffer[CURSOR:]

def respell():
    global MODE, editbuffer
    MODE = 'RESPELL'
    secondhalf = editbuffer[CURSOR:].split()
    editbuffer = [editbuffer[:CURSOR], secondhalf[0], ' '.join(secondhalf[1:])]
    return 'respell '+secondhalf[0]

def input():
    global MODE, editbuffer
    editbuffer = [editbuffer[:CURSOR], editbuffer[CURSOR:]]
    MODE = 'INPUT'
    return 'input mode'

def select():
    global MODE, CURSOR2
    MODE = 'SELECT'
    CURSOR2 = CURSOR
    return 'select mode'

def print_select():
    return editbuffer[min(CURSOR, CURSOR2):max(CURSOR, CURSOR2)+1]

def escape():
    global MODE, editbuffer
    editbuffer = ' '.join(editbuffer)
    MODE = 'NORMAL'
    return 'normal mode'

def save():
    pass

command_words = [
    "word",
    "back",
    "line",
    "print_word",
    "print_line",
    "clump",
    "line_list",
    "clump_list",
    "undo",
    "yank",
    "paste",
    "respell",
    "input",
    "select",
    "print_select",
]

nato_alphabet = {
    'alpha': 'a',
    'bravo': 'b',
    'charlie': 'c',
    'delta': 'd',
    'echo': 'e',
    'foxtrot': 'f',
    'golf': 'g',
    'hotel': 'h',
    'india': 'i',
    'juliet': 'j',
    'kilo': 'k',
    'lima': 'l',
    'mike': 'm',
    'november': 'n',
    'oscar': 'o',
    'papa': 'p',
    'quebec': 'q',
    'romeo': 'r',
    'sierra': 's',
    'tango': 't',
    'uniform': 'u',
    'victor': 'v',
    'whiskey': 'w',
    'xray': 'x',
    'yankee': 'y',
    'zulu': 'z',
    'apostrophe': "'"
}

punctuation = {
    'comma': ',',
    'period': '.',
    'question_mark': '?',
    'apostrophe': "'",
    'exclamation_mark': '!',
    'open_parentheses': '(',
    'close_parentheses': ')',
}

commands = {command: globals()[command] for command in command_words}

def process_command(cmd):
    global MODE, editbuffer
    if MODE in ('NORMAL', 'SELECT'):
        STATELIST.append((editbuffer, CURSOR, MODE))
        cmd = cmd.lower().replace(' ', '_')
        if cmd in commands:
            print (commands[cmd]())
        else:
            print("Command not found: ", cmd)
    elif MODE=='INPUT':
        if cmd.lower() == 'escape':
            print(escape())
        else:
            words = []
            tempwords = []
            phonetic_count = 0
            for word in cmd.split():
                if word in nato_alphabet:
                    tempwords.append(word)
                    phonetic_count += 1
                else:
                    if phonetic_count:
                        if phonetic_count >= MIN_PHONETIC:
                            words.append(''.join([nato_alphabet[i] for i in tempwords]))
                        else:
                            words += tempwords
                        phonetic_count = 0
                        tempwords = []
                    if word in punctuation:
                        words.append(punctuation[word])
                    else:
                        words.append(word)
            if phonetic_count:
                if phonetic_count >= MIN_PHONETIC:
                    words.append(''.join([nato_alphabet[i] for i in tempwords]))
                else:
                    words += tempwords
            newstring = ' '.join(words)
            editbuffer[0] += newstring
            print (newstring)
    elif MODE=='RESPELL':
        if cmd.lower() == 'escape':
            print(escape())
        else:
            words = cmd.split()
            for word in words:
                if not word in nato_alphabet:
                    # TODO: correct close misses via levenshtein or something
                    print (word + " unrecognized, try again")
                    break
            else:
                word = ''.join([nato_alphabet[i] for i in words])
                editbuffer = editbuffer[0] + word + ' ' + editbuffer[2]
                MODE = 'NORMAL'
                print (word)

def main():
    buf = ''
    while True:
        buf += sys.stdin.read(1)
        if buf.endswith('\n'):
            process_command(buf[:-1])
            buf = ''

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs='?', help="The filename to edit. Can be an existing or new filename.")
    parser.add_argument("-r", "--readonly", help="Open a file for reading only, no writing.", action="store_true")
    args = parser.parse_args()
    if args.file:
        if os.path.exists(args.file):
            filename = args.file
            if args.readonly:
                try:
                    file = open(filename, 'r')
                    editbuffer = file.read()
                except PermissionError:
                    print ("Cannot open the file "+args.file+" for reading.")
                    sys.exit(0)
            else:
                try:
                    file = open(filename, 'r+')
                    editbuffer = file.read()
                except PermissionError:
                    print ("Cannot open the file "+args.file+" for writing.")
                    sys.exit(0)
        else:
            if args.readonly:
                print ("File "+args.file+" does not exist.")
                sys.exit(0)
            filename = os.path.dirname(os.path.abspath(args.file))
            try:
                file = open(filename, 'w')
            except PermissionError:
                print ("Cannot create the file "+args.file)
    main()
