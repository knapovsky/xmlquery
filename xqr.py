#!/usr/bin/python
#
#XQR:xknapo02
#Filename: xqr.py
#-------------------------------------------------------------------------------
# XML query - Projekt #2 pro predmet IPP 2010/2011
# Autor: Martin Knapovsky Email: xknapo02@stud.fit.vutbr.cz
# Popis: Program zpracuje dotaz zadany pomoci parametru programu a nasledne
#        vyhleda v zadanem XML souboru pozadovane elementy.
# Datum: 19.4.2011

import sys
import re
import xmlparser
from xqrprint import *

# Rozhoduje o tom, zda testovat identifikátor na klíčové slovo
keyword_checking = True

# Dotaz
query = ''
# Globalni slovnik parametru
params = {
            "error"     : 0,
            "help"      : 0,
            "input"     : 0,
            "output"    : 0,
            "query"     : 0,
            "qf"        : 0,
            "root"      : 0,
            "n"         : 0
        }

# Globalni slovnik s retezci z parametru
files = {
            "input"     : 0,
            "output"    : 0,
            "qf"        : 0,
            "root"      : 0,
            "query"    : ''
        }

# Globalni slovnik pro dotaz
pquery = {
            "SELECT"    : '',
            "LIMIT"     : -1,
            "FROM"      : [False, False, False],
            #             [not    elem      .    attr    rel    lit  ]
            "CONDITION" : [False, [False, False, False], False, False],
            "ORDER"     : [False, False],
          }

# Ziska parametry programu -----------------------------------------------------
def get_args( args ):
    global params
    # pokud nejsou zadany parametry, tisknu napovedu
    if len( args ) <= 1:
        # tiskne se napoveda
        params["help"] = 1
        return
    i = 1
    query_now = 0
    # pruchod argumenty
    for arg in args[1:]:
        i += 1
        # napoveda
        if re.match( r"^--help$", arg.lower()):
            params["help"] += 1
        # vstupni soubor
        elif re.match( r"^--input=.+$", arg.lower()):
            params["input"] += 1
            files["input"] = arg[8:]
        # vystupni soubor
        elif re.match( r"^--output=.+$", arg.lower()):
            params["output"] += 1
            files["output"] = arg[9:]
        # dotaz
        elif re.match( r"^--query=.+$", arg.lower()):
            params["query"] += 1
            query_now = 1
            files["query"] = arg[8:]
        # externi dotaz
        elif re.match( r"^--qf=.+$", arg.lower()):
            params["qf"] += 1
            files["qf"] = arg[5:]
        # korenovy element
        elif re.match( r"^--root=.+$", arg.lower()):
            params["root"] += 1
            files["root"] = arg[7:]
        # generovani XML hlavicky na vystup
        elif re.match( r"^-n$", arg.lower()):
            params["n"] += 1
        # nacitani dotazu z parametru
        elif query_now == 1:
            # narazili jsme na zacatec dalsiho parametru
            if re.match( r"^-.+", arg.lower()):
                query_now = 0
            # pridani argumentu k dotazu
            else:
                files["query"] += ' ' + arg
        # chyba
        else:
            params["error"] = 1
            return
    
    # kontrola zda parametry nejsou zadany vicekrat    
    for param, occurrence in params.items():
        if occurrence > 1:
            params["error"] = 1
    
    # kontrola kombinovatelnosti parametru
    if( params["query"] != 0 and params["qf"] != 0 ):
            params["error"] = 1
    return

# kontroluje, zda se jedna o klicove slovo 
def is_keyword( word ):
	if keyword_checking:
		if re.match( r"^(FROM)|(SELECT)|(WHERE)|(ORDER)|(LIMIT)|(ROOT)|(ASC)|(DESC)|(CONTAINS)|(BY)|(AND)|(OR)|(NOT)$", word.upper() ):
			return True
		else:
			return False
	else:
		return False
    
# lexikalni analyzator
def get_token():
    global query
    if len( query ) == 0:
        return ''
    
    # zaciname ve stavu START
    state = "START"
    token = ''
    # konecny automat bezi, dokud nenacte cely vstup
    while(1):
        if len( query ) == 0:
            return token
        else:
            character = query[0]
        
        # pocatecni stav
        if state == "START":
            if re.match(r"^\s$", character):
                query = query[1:]
                continue
            elif re.match(r"^[_a-zA-Z]$", character):
                state = "ALPHA"
                token += query[0]
                query = query[1:]
            elif re.match(r"^[0-9]$", character):
                state = "NUMBER"
                token += query[0]
                query = query[1:]
            elif re.match(r"^(|)|<|>|=|\.|\"$", character):
                query = query[1:]
                return character
        
        # token je retezec       
        elif state == "ALPHA":
            if re.match(r"^\s$", character):
                query = query[1:]
                state = "KW_CHECK"
            elif re.match(r"^[_a-zA-Z]$", character):
                state = "ALPHA"
                token += query[0]
                query = query[1:]
            elif re.match(r"^[0-9]$", character):
                state = "ALPHA"
                token += query[0]
                query = query[1:]
            elif re.match(r"^(|)|<|>|=$|\.|\"", character):
                return token
        
        # token je cislo  
        elif state == "NUMBER":
            if re.match(r"^\s$", character):
                query = query[1:]
                return token
            elif re.match(r"^[_a-zA-Z]$", character):
                print_error( "SYNTAX" )
            elif re.match(r"^[0-9]$", character):
                state = "NUMBER"
                token += query[0]
                query = query[1:]
            elif re.match(r"^(|)|<|>|=$|\.|\"", character):
                return token
        
        # kontrola, zda se jedna o klicove slovo, nebo nikoliv
        elif state == "KW_CHECK":
            if is_keyword( token ):
                return token.upper()
            else:
                return token
                

# zpracuje <CONDITION>
def parse_condition():
    token = get_token()
    
    # <CONDITION> --> NOT <CONDITION> 
    if token == "NOT":
        # licha hodnota znamena negaci
        pquery["CONDITION"][0] += 1
        parse_condition()
        return
    
    # <CONDITION> --> <ELEMENT-OR-ATTRIBUTE> <RELATION-OPERATOR> <LITERAL> 
    elif (not is_keyword( token )) or token == ".":
        # jedna se o atribut
        if token == ".":
            pquery["CONDITION"][1][1] = token
            token = get_token()
            pquery["CONDITION"][1][2] = token
            token = get_token()
        else:    
            # zpracovani elementu
            pquery["CONDITION"][1][0] = token
            token = get_token()
            if token == ".":
                pquery["CONDITION"][1][1] = token
                token = get_token()
                pquery["CONDITION"][1][2] = token
                token = get_token()
        
        if re.match( r"^=|>|<|(CONTAINS)$", token):
            # zpracovani relacniho operatoru
            pquery["CONDITION"][2] = token
        else:
            print_error( "SYNTAX" )
        
        # <LITERAL> (cislo, nebo string ohraniceny uvozovkami)
        token = get_token()
        if token == "\"":
            token = get_token()
            pquery["CONDITION"][3] = token
            token = get_token()
            if token != "\"":
                print_error( "SYNTAX" )
        
        elif re.match( r"^[0-9]+$", token ):
            # CONTAINS neprijima celociselny literal
            if pquery["CONDITION"][2] == "CONTAINS":
                print_error( "SYNTAX" )
            else:
                pquery["CONDITION"][3] = float(token)
        else:
            print_error( "SYNTAX" )
        
    else:
        print_error( "SYNTAX" )

# parsuje nonterminal <LIMITn>  
def parse_limit():
    token = get_token()
    if token.isupper():
        print_error( "SYNTAX" )
    # nasli jsme cislo, ktere jsme ocekavali
    elif re.match( r"^\d+$", token ):
        pquery["LIMIT"] = int(token)
    else:
        print_error( "SYNTAX" )

# parsuje nonterminal <FROM-ELM>        
def parse_from():
    token = get_token()
    if token == "ROOT":
        pquery["FROM"][0] = token
    elif token == ".":
            pquery["FROM"][1] = token
            token = get_token()
            pquery["FROM"][2] = token
    # ocekavame element, ne klicove slovo
    elif token.isupper():
        print_error( "SYNTAX" )
    # nasli jsme element
    
    else:    
        # zpracovani elementu
        pquery["FROM"][0] = token
        token = get_token()
        if token == ".":
            pquery["FROM"][1] = token
            token = get_token()
            pquery["FROM"][2] = token
        else:
            global query
            query = token + query

# parsuje nonterminal <ORDERING>       
def parse_order():
    token = get_token()
    # musi nasledovat BY
    if token != "BY":
        print_error( "SYNTAX" )
    # <ORDER-CLAUSE> --> ORDER BY <ELEMENT-OR-ATTRIBUTE> <ORDERING>
    token = get_token()
    # ocekavame element, ne klicove slovo
    if token.isupper():
        print_error( "SYNTAX" )
    # nasli jsme element
    else:
        pquery["ORDER"][0] = token
            
    # ocekavame <ORDERING>
    token = get_token()
    if re.match( r"^(ASC)|(DESC)$", token):
        pquery["ORDER"][1] = token
    # chybi <ORDERING>
    else:
        print_error( "SYNTAX" )

# Parsuje dotaz        
# po tokenech nacita dotaz, testuje jeho spravnost (syntakticka analyza) a
# a nastavuje slovnik pquery
def parse_query():
    global pquery
    token = get_token()
    
    # prvni musi byt SELECT
    if token == "SELECT":
        # ziskam dalsi token, coz by mel byt element
        token = get_token()
        # element nesmi byt klicovym slovem?
        if token.isupper():
            print_error( "SYNTAX" )
        else:
            pquery["SELECT"] = token
    # nenasli jsme SELECT
    else:
        print_error( "SYNTAX" )
    
    # dalsi token => bud LIMIT, nebo FROM    
    token = get_token()
    if token == "LIMIT":
        parse_limit()
        token = get_token()
        if token == "FROM":
            parse_from()
        # nenasli jsme FROM
        else:
            print_error( "SYNTAX" )
    # nasli jsme FROM
    elif token == "FROM":
        parse_from()
    # nenasli jsme ani LIMIT ani FROM
    else:
        print_error( "SYNTAX" )
    
    token = get_token()
    if token == "WHERE":
        # nalezli jsme WHERE, dalsi token musi byt <CONDITION>
        # zpracovani condition pomoci funkce parse_condition
        parse_condition()        
        # ----------------------------------------------------------------------
        # tady pak jeste nacitame dalsi token je testujeme na <ORDER-CLAUSE>
        token = get_token()
        if token == "ORDER":
            parse_order()
        # dosli jsme na konec dotazu <ORDER-CLAUSE> --> empty
        else:
            return
    # muze nasledovat ORDER BY, jelikoz <WHERE-CLAUSE> --> empty
    elif token == "ORDER":
        parse_order()
    # <ORDER-CLAUSE> --> empty, <WHERE-CLAUSE> --> empty
    elif token == '':
        return
    else:
        print_error( "SYNTAX" )
    
    # KONEC PARSOVANI 
    return
    
# ------------------------------------------------------------------------------
# ------------------------------------PROGRAM-----------------------------------
# ------------------------------------------------------------------------------
# ziskani parametru programu
get_args( sys.argv )
# tisk napovedy
if params["help"] == 1:
    print_help()
    exit( 0 )
# spatne zadane parametry programu  
elif params["error"] == 1:
    print_error( "ARGS" )

# nacteni query z parametru
if params["query"] == 1:
    query = files["query"]
# cteni ze souboru
elif params["qf"] == 1:
    # otevreni souboru a nacteni dotazu
    try:
        f = open(files["qf"])
    except Exception:
        print_error( "queryFILE" )
    while True:
        line = f.readline()
        if len(line) == 0: # preskakuji prazdny radek
            break
        query += line

# argumenty v poradku, pokracuji
parse_query()
selection = xmlparser.parse_xml(params, files, pquery)

# vypis vysledku vyhledavani
if params["output"] == 1:
    # otevreni souboru a nacteni dotazu
    try:
        fw = open(files["output"], 'w')
    except Exception:
        print_error( "OUTPUT" )
    fw.write(selection)
    fw.close()
else:
    print(selection)
