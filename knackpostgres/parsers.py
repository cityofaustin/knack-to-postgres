"""
Lark parser definitions for handling knack foruma fields.
"""

from lark import Lark

# define grammars here, with the top level always named `values`
CONCATENATION = r"""
    values: (method | (text_before_method|text_without_method) )+

    method.1: (_method_with_two_param | _method_with_one_param)
    
    _method_with_two_param.1: method_name_two_param _OPEN_PARENS first_param _COMMA second_param _CLOSED_PARENS

    _method_with_one_param.2: method_name_one_param _OPEN_PARENS only_param _CLOSED_PARENS

    first_param: (method | text_before_comma)+
    
    second_param: (method | text_before_method | text_before_closed_parens)+

    only_param: (method | text_before_method | text_before_closed_parens)+  // identical to second param, but makes parsing the tree easier to distinguish between them

    _CLOSED_PARENS: /\)/
    
    _OPEN_PARENS: /\(/

    method_name_one_param: /(trim|trimLeft|trimRight|length|lower|upper|capitalize|random|numberToWords)/ -> method_name

    method_name_two_param: /(left|right|mid|regexReplace|extractRegex|replace)/ -> method_name

    text_before_method: /.+?(?=((trim|length|lower|left)\())/ -> text_content
    
    text_without_method: /.+/ -> text_content
    
    text_before_comma: /.+?(?=,)/ -> text_content
  
    text_before_closed_parens: /.+?(?=\))/ -> text_content
    
    _COMMA: /,/
"""

GRAMMAR = {"concatenation": CONCATENATION}


def get_parser(grammar):
    return Lark(GRAMMAR[grammar], start="values", debug=False, propagate_positions=True)
