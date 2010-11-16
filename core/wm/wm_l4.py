
def INIT() :
   return WM_L4

class WM_L4 :
   def __init__(self, vm, method, analysis) :
      x = analysis.get(method)


      self.set_context( { "op_bind" : { '&' : 500, '-' : 600, '+' : 700, '^' : 800 } } )

      print method.get_name(), x.get_ops()

   def get(self) :
      return [ 900090903, 980978789, 656767, 7667 ]
   
   def set_context(self, values) :
      pass

