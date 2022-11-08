#!/usr/bin/python
#
#XQR:xknapo02
#Filename: xmlparser.py
#-------------------------------------------------------------------------------
# XML query - Projekt #2 pro predmet IPP 2010/2011
# Autor: Martin Knapovsky Email: xknapo02@stud.fit.vutbr.cz
# Popis: Modul slouzi pro vyhledavani elementu v XML souboru na zaklade zadaneho
#        dotazu.
# Datum: 19.4.2011

import xml.sax
import re
from xqrprint import print_error

class Handler(xml.sax.ContentHandler):
    """
    Trida pro praci s XML souborem
    """
    
    def __init__(self, params, files, pquery):
        """
        Inicializace objektu
        """
        
        self._depth = 0
        self._pquery = pquery
        self._params = params
        self._files = files
        # v XML souboru muze byt vice casti, ktere by byli prohledavany,
        # avsak mi prohledavame pouze prvni nalezeny zdroj zadany v dotazu
        self._inside_condition = False
        self._temp = ''
        self._condition = False
        self._check_data = False
        self._source_depth = False
        self._inside_source = False 
        self._is_there_condition = False
        self._selections = 0
        self._selem_depth = False
        self._selected = False
        self._result_string = ''
        self._result = [] # vysledek vyhledavani
        self._no_more = False
        self._cond_elem_found = False
        self._not_condition = False
        
        if( self._pquery["CONDITION"][2] != False ):
            self._is_there_condition = True
            
        if( (self._pquery["CONDITION"][0] % 2) == 1 ):
            self._not_condition = True
        
        #print("------------NASTAVENI---VYHLEDAVANI-------------")
        #print(self._pquery)
        #print()
        #print(self._params)
        #print()
        #print(self._files)
        #print("----------------------KONEC---------------------")
    
    def get_result(self):
        """
        Vraci vysledek dotazu
        """
        return self._result_string
    
    def _add_to_result_string( self, name, attrs ):
        """
        Zapisuje prvky a jejich atribujty obalene <>
        do vysledneho retezce vyberu
        """
        temp1 = "<" + name
        # ulozim atributy
        for attr_name in attrs.keys():
            temp1 += " " + attr_name
            temp1 += "=\"" + attrs.get(attr_name, "") + "\""
        temp1 += ">"   
        self._result_string += temp1
    
    def _add_to_temp( self, name, attrs ):
        """
        Zapisuje prvky a jejich attributy
        obalene <> do docasneho vysledku vyberu
        """
        self._temp += "<" + name
        # ulozim atributy
        for attr_name in attrs.keys():
            self._temp += " " + attr_name
            self._temp += "=\"" + attrs.get(attr_name, "") + "\""
        self._temp += ">"
        
    def _check_condition(self, name, attrs):
        """Kontrola podminky"""
        
        self._cond_elem_found = True
        
        # Zjistuji, zda pro porovnani beru element, nebo jeho atribut
        # ...zjistovani podle tecky
        if self._pquery["CONDITION"][1][1] != False:
            # ziskam zadany atribut z hashe
            element = attrs.get(self._pquery["CONDITION"][1][2], "")
            # kdyz tam nebyl, vracim False
            if not element:
                return False
        # porovnani elementu - ne atributu
        elif not attrs:
            element = name
        else:
            return True
          
        # Zjistuji, zda je je <LITERAL> string, nebo number
        if type(self._pquery["CONDITION"][3]) is float:
            # pretypovani literalu na float
            literal = self._pquery["CONDITION"][3]
            # element se musi taky pretypovat
            try:
                if self._pquery["CONDITION"][2] != "CONTAINS":
                    element = float(element)
                #else:
                    #element = str(element)
                    #literal = str(str(int(literal)))
            # pokud nejde pretypovat, vraci se false
            except Exception:
                return False 
        # Literal je retezec
        else:
            literal = self._pquery["CONDITION"][3]
            
        
        try:    
            if self._pquery["CONDITION"][2] == "CONTAINS":
                resolution = literal in element        
            elif self._pquery["CONDITION"][2] == ">":
                #print("Porovnavam {0} > {1}".format(element, literal))
                resolution = element > literal
            elif self._pquery["CONDITION"][2] == "<":
                #print("Porovnavam {0} < {1}".format(element, literal))
                resolution = element < literal
            elif self._pquery["CONDITION"][2] == "=":
                #print("Porovnavam {0} = {1}".format(element, literal))
                resolution = element == literal
        except Exception:
            return False
        
        # negace vysledku
        if self._pquery["CONDITION"][0] % 2:
            return not resolution
        else:
            return resolution
        
    def characters(self, data):
        """
        Handler, ktery zpracovava data elementu XML souboru
        """
        
        # Pokud byla nastavena kontrola dat, kontroluji
        if self._check_data:
            self._condition = self._check_condition(data, False)
            self._check_data = False
        
        # Data byla vybrana pro ulozeni do docasneho vyberu  
        if self._selected and data:
            self._temp += data
                
    def startDocument(self):
        """
        Handler, ktery nastavuje hlavicku vysledneho souboru
        Rozhoduje dle parametru, zda na zacatek vlozit tag XML, nebo
        root element
        """
        # parametr -n nebyl nastaven, na zacatek dokumentu davame tag XML
        if self._params["n"] == 0:
            self._result_string += "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
        # na zacatek dokumentu vlozime korenovy element zadany pres parametr
        # --root=[element]
        if self._params["root"] != 0:
            self._result_string += "<"+self._files["root"]+">"
            
    def startElement(self, name, attrs):
        """
        Signalizuje pocatek elementu
        name - obsahuje XML 1.0 nazev elementu jako string
        attrs - uchovava atributy elementu
        """
        # Zvyseni zanoreni
        self._depth += 1
        
        if( self._inside_source == False and not self._no_more ):
            
            # Ve zdrojovem elementu se nachazim, pokud jsem ho nalezl, jinak pokud
            # bylo nastaveno FROM na ROOT (vyhledavani v celem dokumentu), nebo
            # pokud vyhledavame pouze podle atributu elementu
            # ["FROM"][0] == False znamena, ze prohledavame atributy
        
            # Zadano FROM .attribut
            if( self._pquery["FROM"][0] == False and self._pquery["FROM"][2] in attrs.keys()):
                self._inside_source = name
                if self._source_depth == False:
                    self._source_depth = self._depth
                #self._add_to_result_string( name, attrs )
            
            # Zadano FROM element, nebo FROM ROOT
            elif( self._pquery["FROM"][0] != False and self._pquery["FROM"][2] == False ):
                if( self._pquery["FROM"][0] == "ROOT" ):
                    self._inside_source = "ROOT"
                    self._source_depth == -1
                    
                if( self._pquery["FROM"][0] == name ):
                    self._inside_source = name
                    if self._source_depth == False:
                        self._source_depth = self._depth
                    #self._add_to_result_string( name, attrs )
                        
            # Zadano FROM element.attribut  
            elif( self._pquery["FROM"][0] != False and self._pquery["FROM"][2] != False ):
                if( self._pquery["FROM"][0] == name and self._pquery["FROM"][2] in attrs.keys() ):
                    self._inside_source = name
                    if self._source_depth == False:
                        self._source_depth = self._depth
                    #self._add_to_result_string( name, attrs )
                    
        # Jsem uvnitr zdrojoveho elementu
        if( self._inside_source ):
            if( self._pquery["SELECT"] == name ):
                self._selected = True
                if self._selem_depth == False:
                    self._selem_depth = self._depth     
                # dotaz obsahuje podminku
                if( self._is_there_condition ):
                    self._inside_condition = True
        
        # Prvek byl vybran
        if self._selected:
            # Pridavam prvek do docasneho vysledku
            self._add_to_temp( name, attrs )
            # Pokud byla zadana podminka, provadim testovani
            if( self._inside_condition ):
                # Porovnani dat
                if( self._pquery["CONDITION"][1][0] == name
                    and self._pquery["CONDITION"][1][1] == False
                    ):
                        self._check_data = True
                # Porovnani atributu
                elif( self._pquery["CONDITION"][1][0] == name ):
                    self._condition = self._check_condition( name, attrs )
                elif( self._pquery["CONDITION"][1][2] in attrs.keys()):
                    self._condition = self._check_condition( name, attrs );
                    
    
    def endElement(self, name):
        """
        Handler, ktery obsluhuje signalizaci o konci elementu
        """
        # Opoustim zdrojovy element
        if( self._inside_source != False
            and self._inside_source == name
            and self._source_depth == self._depth
        ):
            self._inside_source = False
            self._source_depth = False
            # tohle mozna neni potreba, kdyz jsou XML soubory validni
            if self._selected != False:
                self._selected = False
            self._no_more = True
        
        # Vlozeni ukoncujiciho tagu        
        if( self._inside_source and self._selected ):
            self._temp += "</"+name+">"
        
        # Zapsani vybraneho prvku do vysledku    
        if( self._inside_source
            and self._pquery["SELECT"] == name
            and (self._selem_depth == self._depth or
                 self._pquery["FROM"][0] == "ROOT")
          ):
            self._selected = False
            if( self._is_there_condition ):
                if self._condition:
                    self._result += [self._temp]
                    self._selections += 1
                elif (not self._cond_elem_found) and self._not_condition:
                    self._result += [self._temp]
                    self._selections += 1
                self._temp = ''; self._cond_elem_found = False; self._condition = False
            else:
                self._result += [self._temp]
                self._selections += 1
                self._temp = ''
                
        # Snizeni zanoreni
        self._depth -= 1
     
    def endDocument(self):
        """
        Ukoncuje dokument
        """       
        # Orezani vystupu se provadi az tady, aby bylo mozne provest serazeni
        # Vypisuje jednotlive 'vyselectovane' prvky do vysledneho stringu
        i = 0
        for selection in self._result:
            if self._pquery["LIMIT"] > -1:
                if i < self._pquery["LIMIT"]:
                    self._result_string += selection
            else:
                self._result_string += selection
            i += 1
        # pokud byl nastaveny korenovy element, dokument se jim ukonci
        if( self._params["root"] ):
            self._result_string += "</"+self._files["root"]+">"     
            
            
            
# provede parsovani xml souboru a vrati vysledek
def parse_xml(params, files, pquery):
    parser = xml.sax.make_parser()
    handler = Handler(params, files, pquery)
    parser.setContentHandler(handler)
    
    # pokud byl zadan parametr --input=% nacitam parsuji zadany soubor
    if params["input"]:
        inputxml = open(files["input"], "r")
        try:
            parser.parse(inputxml)
        except Exception:
            inputxml.close()
            print_error( "INPUT" )
        inputxml.close()
        
    # soubor nebyl zadan, parsuji ze STDIN
    else:
        try:
            parser.parse(stdin)
        except Exception:
            print_error( "INPUT" )
    
    # ziskam vysledek parsovani z handleru
    result = handler.get_result()
    
    return result

    
