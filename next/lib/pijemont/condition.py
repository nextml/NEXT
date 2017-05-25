from __future__ import print_function
from builtins import object
import ply.yacc as yacc
import ply.lex as lex

class condition_lexer(object):
    def __init__(self):
        self.lexer = lex.lex(module=self)

    tokens = ('LT', 'GT', 'EQ', 'AND', 'OR', 'NOT', 'NUMBER', 'LPAREN','RPAREN')

    t_LT    = r'<|lt'
    t_GT    = r'>|gt'
    t_EQ    = r'=|eq'
    t_AND    = r'&|and'
    t_OR    = r'\||or'
    t_NOT    = r'!|not'
    t_LPAREN    = r'\('
    t_RPAREN    = r'\)'
    
    def t_NUMBER(self,t):
        r'\-?\d+\.?(\d+)?'
        try:
            t.value = float(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    # Ignored characters
    t_ignore = " \t"
    
    def t_error(self,t):
        raise Exception("Illegal character '%s'" % t.value[0])
    
    def tokenize(self,data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if tok:
                yield tok
            else:
                break    

class condition_parser(object):
    def __init__(self):
        self.lexer = condition_lexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self,write_tables=0,debug=False)
        self.the_num = 0
        
    def parse(self,data):
        if data:
            return self.parser.parse(data,self.lexer.lexer,0,0,None)
        else:
            return []    

    def p_statement(self, t):
        'statement : NUMBER set_the_num expr'
        t[0] = t[3]
        
    def p_set_the_num(self, t):
        'set_the_num :'
        self.the_num = t[-1]
        
    def p_expr_paren(self, t):
        'expr : LPAREN expr RPAREN'
        t[0] = t[2]

    def p_expr_op(self, t):
        '''expr : expr OR expr
        | expr AND expr
        | NOT expr'''
        if t[1] == '!': t[0] = not t[2]
        elif t[2] == '&': t[0] = t[1] and t[3]
        elif t[2] == '|': t[0] = t[1] or t[3]

    def p_expr(self, t):
        '''expr : GT NUMBER
        | LT NUMBER
        | GT EQ NUMBER
        | LT EQ NUMBER
        | NOT EQ NUMBER
        | EQ NUMBER'''
        if t[1] == '!' and t[2] == '=':
            t[0] = (self.the_num != t[3])
        elif t[1] == '>' and t[2] == '=':
            t[0] = (self.the_num >= t[3])
        elif t[1] == '<' and t[2] == '=':
            t[0] = (self.the_num <= t[3])
        elif t[1] == '=':
            t[0] = (self.the_num == t[2])
        elif t[1] == '>':
            t[0] = (self.the_num > t[2])
        elif t[1] == '<':
            t[0] = (self.the_num < t[2])

    def p_error(self, t):
        raise Exception("Syntax error at '%s'" % t.value)

if __name__ == "__main__":
    p = condition_parser()
    print(p.parse('2 > 3'))
    print(p.parse('2 ( > 1 & > -1.5 )'))
    try:
        print(p.parse('2 ( > 1 & > -1a5 )'))
    except Exception as exc:
        print("oops",exc)
