from pyparsing import (Literal, CaselessKeyword, Forward, Regex, QuotedString, Suppress,
    Optional, Group, FollowedBy, infixNotation, opAssoc, ParseException, ParserElement)
ParserElement.enablePackrat()

COLON,LBRACK,RBRACK,LBRACE,RBRACE,TILDE,CARAT = map(Literal,":[]{}~^")
LPAR,RPAR = map(Suppress,"()")
and_ = CaselessKeyword("AND")
or_ = CaselessKeyword("OR")
not_ = CaselessKeyword("NOT")
to_ = CaselessKeyword("TO")
keyword = and_ | or_ | not_

expression = Forward()

valid_word = Regex(r'([a-zA-Z0-9*_+.-]|\\[!(){}\[\]^"~*?\\:])+').setName("word")
valid_word.setParseAction(
    lambda t : t[0].replace('\\\\',chr(127)).replace('\\','').replace(chr(127),'\\')
    )

string = QuotedString('"')

required_modifier = Literal("+")("required")
prohibit_modifier = Literal("-")("prohibit")
integer = Regex(r"\d+").setParseAction(lambda t:int(t[0]))
proximity_modifier = Group(TILDE + integer("proximity"))
number = Regex(r'\d+(\.\d+)?').setParseAction(lambda t:float(t[0]))
fuzzy_modifier = TILDE + Optional(number, default=0.5)("fuzzy")

term = Forward()
field_name = valid_word.copy().setName("fieldname")
incl_range_search = Group(LBRACK + term("lower") + to_ + term("upper") + RBRACK)
excl_range_search = Group(LBRACE + term("lower") + to_ + term("upper") + RBRACE)
range_search = incl_range_search("incl_range") | excl_range_search("excl_range")
boost = (CARAT + number("boost"))

string_expr = Group(string + proximity_modifier) | string
word_expr = Group(valid_word + fuzzy_modifier) | valid_word
term << (Optional(field_name("field") + COLON) + 
         (word_expr | string_expr | range_search | Group(LPAR + expression + RPAR)) +
         Optional(boost))
term.setParseAction(lambda t:[t] if 'field' in t or 'boost' in t else None)
    
expression << infixNotation(term,
    [
    (required_modifier | prohibit_modifier, 1, opAssoc.RIGHT),
    ((not_ | '!').setParseAction(lambda:"NOT"), 1, opAssoc.RIGHT),
    ((and_ | '&&').setParseAction(lambda:"AND"), 2, opAssoc.LEFT),
    (Optional(or_ | '||').setParseAction(lambda:"OR"), 2, opAssoc.LEFT),
    ])

def flatten(lis):
    """Given a list, possibly nested to any level, return it flattened."""
    new_lis = []
    for item in lis:
        if type(item) == type([]):
            new_lis.extend(flatten(item))
        else:
            new_lis.append(item)
    return new_lis

def get_objects_from_query_string(qstring):
    results = expression.parseString(qstring.replace('&','+'), parseAll=True)[0]
    check = len([e.asList() for e in results if not isinstance(e, basestring)])
    if check == 0:
        # Query string one of these cases
        #  1. object:<name>
        #  2. object:"<string, possibly with Boolean operators"
        objlist = results[-1].replace(' AND ','$').replace(' OR ','$').split('$')
    elif check == 1:
        # Query string is of the following form
        #  1. object:(<expression, possibly nested>)
        tmp = [e.asList() for e in results if not isinstance(e, basestring)]
        objlist = [o for o in flatten(tmp) if o not in ['OR','AND']]
    else:
        # We are left with cases with additional modifiers
        tmp = [e.asList() for e in results if not isinstance(e, basestring) and 'object' in e.values()]
        objs = [o for o in flatten(tmp) if o not in ['OR','AND',':','object']]
        if 'object:"' in qstring:
            # In this case we have to be careful that object string could contain Boolean operators
            objlist =  flatten([o.replace(' AND ','$').replace(' OR ','$').split('$') for o in objs])
        else:
            objlist = objs

    return objlist
