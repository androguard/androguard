# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

# risks from AndroidManifest.xml :
    # Permissions : 
        # dangerous
        # signatureOrSystem
        # signature
        # normal
        
        # money
        # internet
        # sms
        # call
        # privacy

    # Files :
        # binary file
        # shared library

# risks from classes.dex :
    # API <-> Permissions 
        # method X is more dangerous than another one
    # const-string -> apk-tool
        # v0 <- X
        # v1 <- Y

        # v10 <- X
        # v11 <- Y

        # CALL( v0, v1 )
    # obfuscated names

GENERAL_RISK            = 0
DANGEROUS_RISK          = 1
SIGNATURE_SYSTEM_RISK   = 2 
SIGNATURE_RISK          = 3
NORMAL_RISK             = 4

MONEY_RISK              = 5 
SMS_RISK                = 6
PHONE_RISK              = 7
INTERNET_RISK           = 8
PRIVACY_RISK            = 9 

BINARY_RISK             = 10
EXPLOIT_RISK            = 11

RISK_VALUES = {
    DANGEROUS_RISK          : 4,
    SIGNATURE_SYSTEM_RISK   : 10,
    SIGNATURE_RISK          : 10,
    NORMAL_RISK             : 0,
    
    MONEY_RISK              : 6,
    SMS_RISK                : 4,
    PHONE_RISK              : 4,
    INTERNET_RISK           : 2,
    PRIVACY_RISK            : 6,

    BINARY_RISK             : 5,
    EXPLOIT_RISK            : 18,
}

GENERAL_PERMISSIONS_RISK = {
    "dangerous"                 : DANGEROUS_RISK,
    "signatureOrSystem"         : SIGNATURE_SYSTEM_RISK,
    "signature"                 : SIGNATURE_RISK,
    "normal"                    : NORMAL_RISK,
}

PERMISSIONS_RISK = {
    "SEND_SMS"                  : [ MONEY_RISK, SMS_RISK ],
    
    "RECEIVE_SMS"               : [ SMS_RISK ],
    "READ_SMS"                  : [ SMS_RISK ],
    "WRITE_SMS"                 : [ SMS_RISK ],
    "RECEIVE_SMS"               : [ SMS_RISK ],
    "RECEIVE_MMS"               : [ SMS_RISK ],


    "PHONE_CALL"                : [ MONEY_RISK ],
    "PROCESS_OUTGOING_CALLS"    : [ MONEY_RISK ],
    "CALL_PRIVILEGED"           : [ MONEY_RISK ],


    "INTERNET"                  : [ INTERNET_RISK ],
    
    "READ_PHONE_STATE"          : [ PRIVACY_RISK ],
    "READ_CONTACTS"             : [ PRIVACY_RISK ],
    "ACCESS_FINE_LOCATION"      : [ PRIVACY_RISK ],
    "ACCESS_COARSE_LOCATION"    : [ PRIVACY_RISK ],
}

HIGH_RISK                   = "high"
LOW_RISK                    = "low"
AVERAGE_RISK                = "average"
NULL_MALWARE_RISK           = "null"
AVERAGE_MALWARE_RISK        = "average"
HIGH_MALWARE_RISK           = "high"
UNACCEPTABLE_MALWARE_RISK   = "unacceptable"

from androconf import error, warning, debug, set_debug, get_debug

def create_system() :
    try :
        import fuzzy
    except ImportError :
        error("please install pyfuzzy to use this module !")

    import fuzzy.System
    import fuzzy.InputVariable
    import fuzzy.fuzzify.Plain
    import fuzzy.OutputVariable
    import fuzzy.defuzzify.COGS
    import fuzzy.set.Polygon
    import fuzzy.set.Singleton
    import fuzzy.set.Triangle
    import fuzzy.Adjective
    import fuzzy.operator.Input
    import fuzzy.operator.Compound
    import fuzzy.norm.Min
    import fuzzy.norm.Max
    import fuzzy.Rule
    
    system = fuzzy.System.System()

    input_Dangerous_Risk = fuzzy.InputVariable.InputVariable(fuzzify=fuzzy.fuzzify.Plain.Plain())
    input_Money_Risk = fuzzy.InputVariable.InputVariable(fuzzify=fuzzy.fuzzify.Plain.Plain())
    input_Privacy_Risk = fuzzy.InputVariable.InputVariable(fuzzify=fuzzy.fuzzify.Plain.Plain())
    input_Binary_Risk = fuzzy.InputVariable.InputVariable(fuzzify=fuzzy.fuzzify.Plain.Plain())
    input_Internet_Risk = fuzzy.InputVariable.InputVariable(fuzzify=fuzzy.fuzzify.Plain.Plain())
    
    # Input variables

        # Dangerous Risk
    system.variables["input_Dangerous_Risk"] = input_Dangerous_Risk
    in1_set = fuzzy.set.Polygon.Polygon([(0.0, 1.0), (8.0, 1.0), (12.0, 0.0)])
    in1 = fuzzy.Adjective.Adjective(in1_set)
    input_Dangerous_Risk.adjectives[LOW_RISK] = in1

    in2_set = fuzzy.set.Polygon.Polygon([(8.0, 0.0), (16.0, 1.0), (20.0, 0.0)])
    in2 = fuzzy.Adjective.Adjective(in2_set)
    input_Dangerous_Risk.adjectives[AVERAGE_RISK] = in2

    in3_set = fuzzy.set.Polygon.Polygon([(16.0, 0.0), (24.0, 1.0)])
    in3 = fuzzy.Adjective.Adjective(in3_set)
    input_Dangerous_Risk.adjectives[HIGH_RISK] = in3
    
        # Money Risk
    system.variables["input_Money_Risk"] = input_Money_Risk
    in4_set = fuzzy.set.Polygon.Polygon([(0.0, 1.0), (5.0, 0.0)])
    in4 = fuzzy.Adjective.Adjective(in4_set)
    input_Money_Risk.adjectives[LOW_RISK] = in4

    in5_set = fuzzy.set.Polygon.Polygon([(4.0, 0.0), (6.0, 1.0), (30.0, 1.0)])
    in5 = fuzzy.Adjective.Adjective(in5_set)
    input_Money_Risk.adjectives[HIGH_RISK] = in5

        # Privacy Risk
    system.variables["input_Privacy_Risk"] = input_Privacy_Risk
    in6_set = fuzzy.set.Polygon.Polygon([(0.0, 1.0), (6.0, 0.0)])
    in6 = fuzzy.Adjective.Adjective(in6_set)
    input_Privacy_Risk.adjectives[LOW_RISK] = in6

    in7_set = fuzzy.set.Polygon.Polygon([(4.0, 0.0), (30.0, 1.0)])
    in7 = fuzzy.Adjective.Adjective(in7_set)
    input_Privacy_Risk.adjectives[HIGH_RISK] = in7

        # Binary Risk
    system.variables["input_Binary_Risk"] = input_Binary_Risk
    in8_set = fuzzy.set.Polygon.Polygon([(0.0, 1.0), (20.0, 0.0)])
    in8 = fuzzy.Adjective.Adjective(in8_set)
    input_Binary_Risk.adjectives[LOW_RISK] = in8

    in9_set = fuzzy.set.Polygon.Polygon([(10.0, 0.0), (30.0, 1.0)]) 
    in9 = fuzzy.Adjective.Adjective(in9_set)
    input_Binary_Risk.adjectives[HIGH_RISK] = in9

        # Internet Risk
    system.variables["input_Internet_Risk"] = input_Internet_Risk
    in10_set = fuzzy.set.Polygon.Polygon([(0.0, 1.0), (4.0, 0.0)])
    in10 = fuzzy.Adjective.Adjective(in10_set)
    input_Internet_Risk.adjectives[LOW_RISK] = in10

    in11_set = fuzzy.set.Polygon.Polygon([(2.0, 0.0), (27.0, 1.0)]) 
    in11 = fuzzy.Adjective.Adjective(in11_set)
    input_Internet_Risk.adjectives[HIGH_RISK] = in11


    # Output variables
    output_malware_risk = fuzzy.OutputVariable.OutputVariable(
                            defuzzify=fuzzy.defuzzify.COGS.COGS(),
                            description="malware risk",
                            min=0.0,max=100.0,
                        )
    output_malware_risk.adjectives[NULL_MALWARE_RISK] = fuzzy.Adjective.Adjective(fuzzy.set.Singleton.Singleton(0.0))
    output_malware_risk.adjectives[AVERAGE_MALWARE_RISK] = fuzzy.Adjective.Adjective(fuzzy.set.Singleton.Singleton(20.0))
    output_malware_risk.adjectives[HIGH_MALWARE_RISK] = fuzzy.Adjective.Adjective(fuzzy.set.Singleton.Singleton(80.0))
    output_malware_risk.adjectives[UNACCEPTABLE_MALWARE_RISK] = fuzzy.Adjective.Adjective(fuzzy.set.Singleton.Singleton(100.0))

    system.variables["output_malware_risk"] = output_malware_risk

    # Rules
    #RULE 1 : IF input_Dangerous_Risk IS Faible THEN output_risk_malware IS Nul;
    rule1 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[NULL_MALWARE_RISK]],
                operator=fuzzy.operator.Input.Input( system.variables["input_Dangerous_Risk"].adjectives[LOW_RISK] )
    )
     
    #RULE 2 : IF input_Dangerous_Risk IS Moyen THEN output_risk_malware IS Moyen;
    rule2 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[AVERAGE_MALWARE_RISK]],
                operator=fuzzy.operator.Input.Input( system.variables["input_Dangerous_Risk"].adjectives[AVERAGE_RISK] )
    )
     
     
    #RULE 3 : IF input_Dangerous_Risk IS Eleve THEN output_risk_malware IS Eleve;
    rule3 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[HIGH_MALWARE_RISK]],
                operator=fuzzy.operator.Input.Input( system.variables["input_Dangerous_Risk"].adjectives[HIGH_RISK] )
    )
      
     
    #RULE 4 : IF input_Dangerous_Risk IS Faible AND input_Binary_Risk IS Eleve THEN output_risk_malware IS Eleve;
    rule4 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[HIGH_MALWARE_RISK]],
                operator = fuzzy.operator.Input.Input( system.variables["input_Binary_Risk"].adjectives[HIGH_RISK] )
    )
    
    #RULE 5 : IF input_Money_Risk IS Eleve THEN output_risk_malware IS Inacceptable;
    rule5 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[UNACCEPTABLE_MALWARE_RISK]],
                operator=fuzzy.operator.Input.Input( system.variables["input_Money_Risk"].adjectives[HIGH_RISK] )
    )
    
    #RULE 6 : IF input_Dangerous_Risk IS Eleve AND input_Binary_Risk IS Eleve THEN output_risk_malware IS Inacceptable;
    rule6 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[UNACCEPTABLE_MALWARE_RISK]],
                operator=fuzzy.operator.Compound.Compound(
                    fuzzy.norm.Min.Min(),
                    fuzzy.operator.Input.Input( system.variables["input_Dangerous_Risk"].adjectives[HIGH_RISK] ),
                    fuzzy.operator.Input.Input( system.variables["input_Binary_Risk"].adjectives[HIGH_RISK] ) )
    )


    #RULE 7 : IF input_Internet_Risk IS Faible AND input_Privacy_Risk IS Eleve THEN output_risk_malware IS Eleve;
    rule7 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[HIGH_MALWARE_RISK]],
                operator=fuzzy.operator.Compound.Compound(
                    fuzzy.norm.Min.Min(),
                    fuzzy.operator.Input.Input( system.variables["input_Internet_Risk"].adjectives[LOW_RISK] ),
                    fuzzy.operator.Input.Input( system.variables["input_Privacy_Risk"].adjectives[HIGH_RISK] ) )
    )
    
    #RULE 8 : IF input_Internet_Risk IS Eleve AND input_Privacy_Risk IS Eleve THEN output_risk_malware IS Inacceptable;
    rule8 = fuzzy.Rule.Rule(
                adjective=[system.variables["output_malware_risk"].adjectives[UNACCEPTABLE_MALWARE_RISK]],
                operator=fuzzy.operator.Compound.Compound(
                    fuzzy.norm.Min.Min(),
                    fuzzy.operator.Input.Input( system.variables["input_Internet_Risk"].adjectives[HIGH_RISK] ),
                    fuzzy.operator.Input.Input( system.variables["input_Privacy_Risk"].adjectives[HIGH_RISK] ) )
    )
        
    system.rules["r1"] = rule1
    system.rules["r2"] = rule2
    system.rules["r3"] = rule3
    system.rules["r4"] = rule4
    system.rules["r5"] = rule5
    system.rules["r6"] = rule6
    system.rules["r7"] = rule7
    system.rules["r8"] = rule8

    return system

def export_system(system, directory) :
    from fuzzy.doc.plot.gnuplot import doc
    
    d = doc.Doc(directory)
    d.createDoc(system)

    import fuzzy.doc.structure.dot.dot
    import subprocess
    for name,rule in system.rules.items():
            cmd = "dot -T png -o '%s/fuzzy-Rule %s.png'" % (directory,name)
            f = subprocess.Popen(cmd, shell=True, bufsize=32768, stdin=subprocess.PIPE).stdin
            fuzzy.doc.structure.dot.dot.print_header(f,"XXX")
            fuzzy.doc.structure.dot.dot.print_dot(rule,f,system,"")
            fuzzy.doc.structure.dot.dot.print_footer(f)
    cmd = "dot -T png -o '%s/fuzzy-System.png'" % directory
    f = subprocess.Popen(cmd, shell=True, bufsize=32768, stdin=subprocess.PIPE).stdin
    fuzzy.doc.structure.dot.dot.printDot(system,f)

    d.overscan=0
    in_vars = [name for name,var in system.variables.items() if isinstance(var,fuzzy.InputVariable.InputVariable)]
    out_vars = [name for name,var in system.variables.items() if isinstance(var,fuzzy.OutputVariable.OutputVariable)]
    
    if len(in_vars) == 2 and not (
            isinstance(system.variables[in_vars[0]].fuzzify,fuzzy.fuzzify.Dict.Dict)
        or
            isinstance(system.variables[in_vars[1]].fuzzify,fuzzy.fuzzify.Dict.Dict)
    ):
        for out_var in out_vars:
            args = []
            if isinstance(system.variables[out_var].defuzzify,fuzzy.defuzzify.Dict.Dict):
                for adj in system.variables[out_var].adjectives:
                    d.create3DPlot_adjective(system, in_vars[0], in_vars[1], out_var, adj, {})
            else:
                d.create3DPlot(system, in_vars[0], in_vars[1], out_var, {})

SYSTEM = None
# pyfuzzy without fcl support (don't install antlr)
class RiskIndicator :
    def __init__(self) :
        #set_debug()
        global SYSTEM

        if SYSTEM == None :
            SYSTEM = create_system()
#            export_system( SYSTEM, "./output" )

    def with_apk(self, apk_file) :
        risks = { DANGEROUS_RISK    : 0.0,
                  MONEY_RISK        : 0.0,
                  PRIVACY_RISK      : 0.0,
                  INTERNET_RISK     : 0.0,
                  BINARY_RISK       : 0.0,
                }

        list_details_permissions = apk_file.get_details_permissions()
        for i in list_details_permissions :
            permission = i
            if permission.find(".") != -1 :
                permission = permission.split(".")[-1]
#            print permission, GENERAL_PERMISSIONS_RISK[ list_details_permissions[ i ][0] ]
          
            risk_type = GENERAL_PERMISSIONS_RISK[ list_details_permissions[ i ][0] ]

            risks[ DANGEROUS_RISK ] += RISK_VALUES [ risk_type ]

            try :
                for j in PERMISSIONS_RISK[ permission ] :
                    risks[ j ] += RISK_VALUES[ j ]
            except KeyError :
                pass

        list_details_files = apk_file.get_files_types()
        for i in list_details_files :
            if "ELF" in list_details_files[ i ] :
                # shared library
                if "shared" in list_details_files[ i ] :
                    risks[ BINARY_RISK ] += RISK_VALUES [ BINARY_RISK ]
                # binary 
                else :
                    risks[ BINARY_RISK ] += RISK_VALUES [ EXPLOIT_RISK ]


        output_values = {"output_malware_risk" : 0.0}
        input_val = {}
        input_val['input_Dangerous_Risk'] = risks[ DANGEROUS_RISK ]
        input_val['input_Money_Risk'] = risks[ MONEY_RISK ]
        input_val['input_Privacy_Risk'] = risks[ PRIVACY_RISK ]
        input_val['input_Binary_Risk'] = risks[ BINARY_RISK ]
        input_val['input_Internet_Risk'] = risks[ INTERNET_RISK ]

#        print input_val,

        SYSTEM.calculate(input=input_val, output = output_values)

        val = output_values[ "output_malware_risk" ]
        return val
