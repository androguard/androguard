#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2015, Tal Melamed <androguard at appsec.it>
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
#
# VT SCAN EULA
# ------------
# By scanning new file , you consent to virustotal
# Terms of Service (https://www.virustotal.com/en/about/terms-of-service/)
# and allow VirusTotal to share this file with the security community. 
# See virustotal Privacy Policy (https://www.virustotal.com/en/about/privacy/) for details.
#

import sys, os
import hashlib, urllib, urllib2, json
try:
    import requests
except:
    print '[Warning] request module is missing. requests module is required in order to upload new files for scan.\nYou can install it by running: pip install requests.'

from optparse import OptionParser
from androguard.core import androconf

option_0 = { 'name' : ('-f', '--file'), 'help' : 'retreiving file scan report', 'nargs' : 1 }
option_1 = { 'name' : ('-x', '--hash'), 'help' : 'retreiving file scan report by hash [md5/sha1/sha256]', 'nargs' : 1 }
option_2 = { 'name' : ('-s', '--scan'), 'help' : 'sending a file for scan', 'nargs' : 1 }
option_3 = { 'name' : ('-c', '--comment'), 'help' : 'make comments on a file (file/hash, comment)', 'nargs' : 2 }
option_4 = { 'name' : ('-r', '--rescan'), 'help' : 'rescanning already submitted files by hash [md5/sha1/sha256]', 'nargs' : 1  }

options = [option_0, option_1, option_2, option_3, option_4]

api_key = '438aa3dbbcc4b451ac75c5bdf71f750bda86ae141ef948a4260ac1e462a71709'
api_url = 'https://www.virustotal.com/vtapi/v2/'
errmsg = 'Something went wrong. Please try again later, or contact us.'
reportfile = "scanreport.html"

# handles http error codes from vt
def handleHTTPErros( code ):
    if code == 404:
        print self.errmsg + '\n[Error 404].'
        return 0
    elif code == 403:
        print 'You do not have permissions to make that call.\nThat should not have happened, please contact us.\n[Error 403].'
        return 0
    elif code == 204:
        print 'The quota limit has exceeded, please wait and try again soon.\nIf this problem continues, please contact us.\n[Error 204].'
        return 0
    else:
        print self.errmsg + '\n[Error '+str(code)+']'
        return 0
    
def getSelected( options ):
    # -f / --file
    if options.file != None:
        if os.path.isfile(options.file):
            ret_type = androconf.is_android( options.file )
            if ret_type == "APK" or ret_type == "DEX" :
                return ["file/report", options.file]
            else:
                print "input file should be apk/dex..."
                return None
        else:
            print "Could not find file..."
            return None

    # -x / --hash
    elif options.hash != None:
        return ["file/report", options.hash]
    
    # -s / --scan                
    elif options.scan != None:
        if os.path.isfile(options.scan):
            ret_type = androconf.is_android( options.scan )
            if ret_type == "APK" or ret_type == "DEX"  :
                return ["file/scan", options.scan]
            else:
                print "input file should be apk/dex..."
                return None
        else:
            print "Could not find file..."
            return None

    # -c / --comment
    elif options.comment != None:
        return ["comments/put", options.comment]

    # -r / --rescan
    elif options.rescan != None:
        return ["file/rescan", options.rescan]

    else:
        return None

# scan files
def doScan( method ):
    url = api_url + method[0]
    files = {'file': open(method[1], 'rb')}
    headers = {"apikey": api_key}
    try:
        response = requests.post( url, files=files, data=headers )
        xjson = response.json()
        response_code = xjson ['response_code']
        verbose_msg = xjson ['verbose_msg']
        if response_code == 1:
            print verbose_msg
            return xjson
        else:
            print verbose_msg

    except urllib2.HTTPError, e:
        handleHTTPErros(e.code)
    except urllib2.URLError, e:
        print 'URLError: ' + str(e.reason)
    except Exception:
        import traceback
        print 'generic exception: ' + traceback.format_exc()

# get report, comment and rescan
def doElse( method ):
    url = api_url + method[0]
    if method[0] == "comments/put":
        parameters = {"resource": method[1][0], "comment": method[1][1], "apikey": api_key}
    else:
        if os.path.isfile(method[1]):
            f = open(method[1], 'rb').read()
            method[1] = hashlib.sha256(f).hexdigest()    
        parameters = {"resource": method[1], "apikey": api_key}

    data = urllib.urlencode(parameters)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        xjson = response.read()
        getResponse(xjson, method[0])
        
    except urllib2.HTTPError, e:
        handleHTTPErros(e.code)
    except urllib2.URLError, e:
        print 'URLError: ' + str(e.reason)
    except Exception:
        import traceback
        print 'generic exception: ' + traceback.format_exc()

# prints response message according to method
def getResponse( xjson, method ):
    response_code = json.loads(xjson).get('response_code')
    verbose_msg = json.loads(xjson).get('verbose_msg')
    if method == "comments/put":
        print verbose_msg

    elif method == "file/report":
        if response_code == 1:
            printScanResults(xjson)
        else:
            print verbose_msg

    else: # method == "file/rescan"
        if response_code == 1:
            print "Resource is now queued for rescan"
        else:
            print "Could not find resrouce"

# prints resouce scan results
def printScanResults( xjson ):
    avlist = []
    xjson = json.loads(xjson)
    scan_date = xjson.get('scan_date')
    total = xjson.get('total')
    positive = xjson.get('positives')
    print "\n------------------------------"
    print 'Scan date: ' + scan_date
    print 'Detection ratio: ' + str(positive) + "/" + str(total)
    print "------------------------------" 
    scans = xjson.get('scans')
    for av in scans.iterkeys():
        res = scans.get(av)
        if res.get('detected') == True:
            print '+ ' + av + ':  ' + res.get('result') + " {" + res.get('version') + "}"
    print "------------------------------"
    createHTMLReport(xjson)     

# downloads full report to reportfile (default: scanreport.html)
def createHTMLReport( xjson ):
    url = xjson.get('permalink')
    try:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        res = opener.open(url).read()
        html = res.replace('<div class="frame" style="margin:20px 0">', '<a href="https://github.com/nu11p0inter/virustotal"> Exceuted by Tal Melamed [virustotal@appsec.it]</a> <div class="frame" style="margin:20px 0">')
        f = open(reportfile, "w")
        f.write(html)
        f.close()
        print "For full scan report, open: " + reportfile
    except:
        pass


def main( options, arguments ) :
    method = getSelected(options)
    if method == None:
        print "Use --help for help."
        return 0
     # filescan   
    elif method[0] == "file/scan":
        doScan(method)
    else:
        doElse(method)
            
if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
      param = option['name']
      del option['name']
      parser.add_option(*param, **option)

   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments)

