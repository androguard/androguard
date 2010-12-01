# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.org>
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

import jvm

class JVMGenerate :
   def __init__(self, _vm, _analysis) :
      self.__vm = _vm
      self.__analysis = _analysis

   def create_affectation(self, method_name, desc) :
      l = []

      if desc[0] == 0 :  
         l.append( [ "aload_0" ] )
         l.append( [ "bipush", desc[2] ] )
         l.append( [ "putfield", desc[1].get_name(), desc[1].get_descriptor() ] )
         
      return l
