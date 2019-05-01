#
#
#
from instruction import InstructionPointer

class Symbol:
    __instance = None


    def __init__(self):
        if Symbol.__instance is None:
            self.__major = [ 'EQU','SET','SECTION','EQUS','MACRO','ENDM',
                             'EXPORT','GLOBAL','PURGE','DB','DS','INCBIN',
                             'UNION','NEXTU','ENDU','DW','DL' ]
            self.__minor = [ '@','_PI','_RS','_NARG','__LINE__','__FILE__',
                             '__DATE__','__TIME__' ]
            Symbol.__instance = self
            
    def __new__(cls):
        if Symbol.__instance is None:
            Symbol.__instance = Symbol()
        return Symbol.__instance


        
    
