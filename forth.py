#!/usr/bin/env python


import sys


def is_int(x, base=10):
    try:
        int(x, base)
        return True
    except ValueError:
        return False


def to_hex(n):
    return hex(n)[2:].upper()


# states

INTERPRET = 0
DEFINITION = 1
COMPILE = 2
COMMENT = 3
DOT_QUOTE = 4
SEE = 5

class Forth:
    
    def __init__(self):
        self.stack = []
        self.state = INTERPRET
        self.def_stack = []
        self.dot_quote_stack = []
        
        # @@@ at the moment, this is a dict in the python sense and doesn't
        # allow multiple definitions of a word the way Forth does
        self.dictionary = {}
        
        # because some parts of Forth need to refer to things by address, here
        # is an index-addressable memory. eventually the dictionary and stack
        # may actually go this way too (and interesting impedence mis-match
        # implementing a low-level language on top of a high-level language)
        self.memory = [0] * 256
        
    def add(self, name, func):
        def stack_func():
            num_args = func.func_code.co_argcount
            self.stack, args = self.stack[:-num_args], self.stack[-num_args:]
            self.stack.extend(func(*args) or tuple())
        self.dictionary[name] = stack_func
    
    def execute(self, token_list):
        for token in token_list:
            if self.state == INTERPRET:
                if token in self.dictionary:
                    word = self.dictionary[token]
                    if callable(word):
                        word()
                    else:
                        error = self.execute(word)
                        if error:
                            return error
                elif is_int(token, self.memory[0]): # @@@ assumes BASE is in 0
                    self.stack.append(int(token, self.memory[0]))
                elif token == ":":
                    self.state = DEFINITION
                elif token == "(":
                    self.state = COMMENT
                elif token == '."':
                    self.state = DOT_QUOTE
                elif token == "SEE":
                    self.state = SEE
                elif token == "!":
                    # because this needs memory access, it's not a normal
                    # dictionary word (yet)
                    addr = self.stack.pop()
                    value = self.stack.pop()
                    self.memory[addr] = value
                elif token == "@":
                    # because this needs memory access, it's not a normal
                    # dictionary word (yet)
                    addr = self.stack.pop()
                    value = self.memory[addr]
                    self.stack.append(value)
                elif token == ".":
                    # had to move this back here so it can access BASE
                    n = self.stack.pop()
                    if self.memory[0] == 16: # @@@ assumes BASE is in 0
                        sys.stdout.write(to_hex(n) + " ")
                    else:
                        sys.stdout.write(str(n) + " ")
                else:
                    return "UNKNOWN TOKEN: %s" % token
            elif self.state == DEFINITION:
                name = token
                self.state = COMPILE
            elif self.state == COMPILE:
                if token == ":":
                    return ": INSIDE :"
                elif token == ";":
                    self.dictionary[name] = self.def_stack[:]
                    self.def_stack = []
                    self.state = INTERPRET
                else:
                    self.def_stack.append(token)
            elif self.state == COMMENT:
                if token == ")":
                    self.state = INTERPRET
            elif self.state == DOT_QUOTE:
                if token.endswith('"'):
                    self.dot_quote_stack.append(token[:-1])
                    # @@@ should this print an extra space before the ok?
                    sys.stdout.write(" ".join(self.dot_quote_stack))
                    self.dot_quote_stack = []
                    self.state = INTERPRET
                else:
                    self.dot_quote_stack.append(token)
            elif self.state == SEE:
                self.state = INTERPRET # @@@ how do we know we weren't in COMPILE?
                if token in self.dictionary:
                    print self.dictionary[token],
                else:
                    return "UNKNOWN TOKEN: %s" % token
            else:
                return "UNKNOWN STATE: %s" % self.state


forth = Forth()

forth.add("+", lambda x, y: (x + y,))
forth.add("-", lambda x, y: (x - y,))
forth.add("*", lambda x, y: (x * y,))
forth.add("/", lambda x, y: (x / y,))
forth.add("/MOD", lambda x, y: divmod(x, y)[::-1])
forth.add("MOD", lambda x, y: (x % y,))
forth.add("SWAP", lambda n1, n2: (n2, n1))
forth.add("DUP", lambda n: (n, n))
forth.add("OVER", lambda n1, n2: (n1, n2, n1))
forth.add("ROT", lambda n1, n2, n3: (n2, n3, n1))
forth.add("DROP", lambda n: None)
forth.add("TUCK", lambda n1, n2: (n2, n1, n2))

# words that can't be defined as a stack-expression

def spaces(n):
    sys.stdout.write(" " * n)

def emit(c):
    sys.stdout.write(chr(c))

def bye():
    sys.exit(0)

forth.add("SPACES", spaces)
forth.add("EMIT", emit)
forth.add("BYE", bye)


# initial code

forth.execute("""

: BASE 0 ;

: CR 13 EMIT 10 EMIT ;
: HEX 16 BASE ! ;
: DECIMAL 10 BASE ! ;

DECIMAL

""".split())

def run():
    while True:
        line = raw_input("> ")
        error = forth.execute(line.split())
        if error:
            print error
        else:
            print "ok"

if __name__ == "__main__":
    run()
