#!/usr/bin/python
#
#XQR:xknapo02
#Filename: xqrprint.py
#-------------------------------------------------------------------------------
# XML query - Projekt #2 pro predmet IPP 2010/2011
# Autor: Martin Knapovsky Email: xknapo02@stud.fit.vutbr.cz
# Popis: Modul slouzi pro tisk napovedy a chybovych hlaseni 
# Datum: 19.4.2011

import re

# Tiskne napovedu programu -----------------------------------------------------
def print_help():
    print("XML query")
    print("Autor: Martin Knapovsky")
    print("")
    print("PARAMETRY: ")
    print("[--help]     - vytiskne tuto napovedu")
    print("[--input=%]  - vstupni soubor ve formatu XML")
    print("[--output=%] - vystupni soubor ve formatu XML s obsahem podle zadaneho dotazu")
    print("[--query=%]  - dotaz v dotazovacim jazyce (viz. zadani)")
    print("[--qf=%]     - dotaz z externiho souboru (nelze kombinovat s [--query=%])")
    print("[--root=%]   - jmeno paroveho korenove elementu obalujici vysledky")
    print("             - pokud neni zadan, vysledky se neobaluji korenovym elementem")
    print("[-n]         - negenerovat XML hlavicku na vystup skriptu")
    print("")
    print("SYNTAXE DOTAZOVACIHO JAZYKA: ")
    print("SELECT element LIMIT n FROM element|element.attribute|ROOT WHERE condition")
    print("                       ORDER BY element|element.attribute ASC|DESC")
    
    exit(0)
    
# Tiskne chybove hlasky --------------------------------------------------------
def print_error( error ):
    if re.match( r"^ARGS$", error ):
        print("Chyba: Spatne zadane parametry!")
        exit( 1 )
    elif re.match( r"^INPUT$", error ):
        print("Chyba: Nelze precist vstupni soubor XML!")
        exit( 2 )
    elif re.match( r"^queryFILE$", error ):
        print("Chyba: Nelze precist soubor s dotazem!")
        exit( 2 )
    elif re.match( r"^OUTPUT$", error ):
        print("Chyba: Nelze otevrit soubor pro zapis!")
        exit( 3 )
    elif re.match( r"^XMLSYNTAX$", error ):
        print("Chyba: Vstupni XML soubor neni platny!")
        exit( 4 )
    elif re.match( r"^ROOT$", error ):
        print("Chyba: Nelze nalezt zadany korenovy element pro obaleni vysledku!")
        exit( 100 )
    elif re.match( r"^SYNTAX$", error ):
        print("Chyba: Spatna syntaxe dotazu!")
        exit( 1 )

# Tiskne nactene argumenty programu z globalnich slovniku ----------------------
def print_args():
    for param, occurrence in params.items():
        print("{0} : {1}".format(param, occurrence))
        
    print()
    for file, name in files.items():
        print("{0} : {1}".format(file, name))