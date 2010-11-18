import misc

import hashlib

def INIT() :
   return WM_L1

def levenshtein(a,b):
    "Calculates the Levenshtein distance between a and b."
    n, m = len(a), len(b)
    if n > m:
        # Make sure n <= m, to use O(min(n,m)) space
        a,b = b,a
        n,m = m,n
        
    current = range(n+1)
    for i in range(1,m+1):
        previous, current = current, [i]+[0]*n
        for j in range(1,n+1):
            add, delete = previous[j]+1, current[j-1]+1
            change = previous[j-1]
            if a[j-1] != b[i-1]:
                change = change + 1
            current[j] = min(add, delete, change)
            
    return current[n]

class WM_L1 :
   def __init__(self, vm, method, analysis) :
      self.__vm = vm
      self.__method = method
      self.__analysis = analysis

      self.__context = {
                           "L_X" : [],
                           "STRING" : "",
                       }

   def run(self) :
      x = self.__analysis.get(self.__method)

      self.__context[ "STRING" ] = x.get_ts()

      self.__context[ "L_X" ].append( 
                                       misc.str2long( hashlib.md5( self.__context[ "STRING" ] ).hexdigest() ) 
                                    )

   def challenge(self, external_wm) :
      distance = levenshtein( self.__context["STRING"], external_wm.get_context()["STRING"] )

#      print distance

      if distance <= 2 :
         return self.__context[ "L_X" ]

      return []

   def get(self) :
      return self.__context[ "L_X" ]

   def set_context(self, values) :
      for x in values :
         self.__context[ x ] = values[ x ]

   def get_context(self) :
      return self.__context

   def get_export_context(self) :
      return self.__context

   def get_import_context(self) :
      return {}
