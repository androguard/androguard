#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Tal Melamed <androguard at appsec.it>, Anthony Desnos <desnos at t0t0.fr>
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

import sys, os, time, imp, re
import httplib, hashlib
try:
    import requests
except:
    pass

from optparse import OptionParser
from androguard.core.bytecodes import apk
from androguard.core import androconf

option_0 = { 'name' : ('-i', '--input'), 'help' : 'filename input (dex, apk)', 'nargs' : 1 }
option_1 = { 'name' : ('-v', '--verbose'), 'help' : 'verbosity level (1-3), default=1', 'nargs' : 1 }
options = [option_0, option_1]



# prints results from virustotal.com according to verbosity level selected
def print_vt_results( result, verbosity ) :
    if verbosity > 0 :
        # printing antivirus results
        # requires verbosity level 1 (default)
        data = result
        print "\n\033[0;36mAntivirus results"
        print "------------------\033[0;0m" 
        index_start = data.find('class="ltr"')
        check = data.find("ltr text-red")
        if (check == -1):
            print "\033[0;32mAPK has been found CLEAN by all AVs\033[0m"
            exit(0)
        while (index_start != -1 and check != -1):
            tmp = data[index_start:]
            index_end = tmp.find("</td>")
            brand = tmp[25:index_end-11]
            data = tmp[index_end:]
            index_start = data.find("ltr text-red")
            tmp = data[index_start:]
            index_end = tmp.find("</td>")
            trojan = tmp[59:index_end-39]
            print brand + ": ",
            print '\033[93m' + trojan + '\033[0m'
            data = tmp[index_end+50:]
            check = data.find("ltr text-red")
            index_start = data.find('class="ltr"')

        # printing Risk Summary
        # requires verbosity level 1 (default)
        title = "Risk summary"
        title_location = result.find(title)
        if ( title_location != -1) :
            data = result[title_location:] 
            prefix = '<div class="enum">\n\s+<i class="icon-flag"></i>\n\s+'
            regex = '[A-Z][A-Za-z\s]*'
            postfix = '\n</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing sent SMS (number> msg)
        # requires verbosity level 1 (default)
        title = "SMS sent"
        title_location = result.find(title)
        if ( title_location != -1 ) :
            data = result[title_location:]
            prefix = '<strong>Destination number: '
            regex = '[0-9]+</strong><br/>\n.+'
            postfix = '\n</div>'
            remove = ['</strong><br/', '\n']
            print_info( data, title, prefix, regex, postfix, remove )

    # print the following in case verbosity level is at least 2 
    if verbosity > 1 :
        # printing code related observation
        # requires verbosity level 2
        title = "Code-related observations"
        title_location = result.find(title)
        if (title_location != -1) :   
            data = result[title_location:] 
            prefix = '<div class="enum">'
            regex = '[A-Z][a-z\s]*'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )


        # printing Required permissions
        # requires verbosity level 2
        title = "Required permissions"
        title_location = result.find(title)
        if (title_location != -1) :   
            data = result[title_location:] 
            prefix = ''
            regex = 'android\.permission\.[A-Z_]+\s\(<em>.*</em>\)'
            postfix = ''
            remove = ["<em>", "</em>"]
            print_info( data, title, prefix, regex, postfix, remove )
    

        # printing urls in which the applicaiton contacted
        # requires verbosity level 2    
        title = "Contacted URIs"
        title_location = result.find(title)
        if (title_location != -1) :   
            data = result[title_location:] 
            prefix = '<strong>'
            regex ='http.*'
            postfix = '</strong>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing uri used by the applicaions
        # requires verbosity level 2
        title = "Accessed URIs"
        title_location = result.find(title)
        if (title_location != -1) :   
            data = result[title_location:] 
            prefix = '<div class="enum">'
            regex ='[a-z]\w+:.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

    # print the following in case verbosity level is 3
    if verbosity > 2 :
        # printing services started by the applicaiton
        # requires verbosity level 3
        title = "Started activities"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing services by the applicaions
        # requires verbosity level 3
        title = "Started services"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing services by the applicaions
        # requires verbosity level 3
        title = "Started receivers"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing files accessed by the applicaions
        # requires verbosity level 3
        title = "Accessed files"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing files opened by the applicaions
        # requires verbosity level 3
        title = "Opened files"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

        # printing classes loaded dynamically opened by the applicaions
        # requires verbosity level 3
        title = "Dynamically loaded classes"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )
        
        # printing classes loaded dynamically opened by the applicaions
        # requires verbosity level 3
        title = "External programs launched"
        title_location = result.find(title)
        if (title_location != -1) :  
            data = result[title_location:] 
            chunk_end = re.search('</div>\n\n</div>', data)
            end_position = chunk_end.start()
            data = data[:end_position+15]
            prefix = '<div class="enum">'
            regex ='.+'
            postfix = '</div>'
            remove = []
            print_info( data, title, prefix, regex, postfix, remove )

    sys.exit(1)


# make prints more generic - next version
def print_info( data, title, prefix, regex, postfix, remove) :
    # printing title
    print '\n'
    print "\033[0;36m" + title
    underline = ""
    for i in range(0,len(title)) :
        underline = underline + "-"
    print underline + "\033[0;0m"

    pre_f = re.search(prefix, data)
    prefix_length = len(pre_f.group())
    post_f = re.search(postfix, data)
    postfix_length = len(post_f.group())
    #printing results
    flag = prefix + regex + postfix
    for risk in re.findall(flag, data) :
        if ( len(remove) > 0 ):
            for x in remove:
                risk = risk.replace(x, "") 
        print "\033[0;36m+\033[0;0m " + risk[ prefix_length:len(risk)-postfix_length ]


# Uploads file to Virustotal.com, in case it could not be found in their DB  
def upload_apk_to_vt(result, file, url, v) :
    vt = "www.virustotal.com"
    upload_url = re.search('"upload_url": "http.+", "remote_addr"', result)
    upload_url = upload_url.group().replace('"upload_url": "','')
    upload_url = upload_url.replace('", "remote_addr"','')
    files = {'file': open(file, 'rb')}
    req = requests.post(upload_url, files=files)
    print "Done. File was uploaded successfully!"
    signs = ['|', '/', '-', '\\']
    counter = 0
    isComplete = 0
    trigger_1 = "Your file is being analysed"
    trigger_2 = "File not found"
    conn = httplib.HTTPSConnection(vt)
    conn.request("GET", url)
    req = conn.getresponse()
    res = req.read()
    conn.close()
    last_analysis_url = re.search('"last_analysis_url": ".*/analysis/', res)
    last_analysis_url = last_analysis_url.group().replace('"last_analysis_url": "', '')
    headers = {"Accept-Language": "en-US"}
    while isComplete != 1:
        sign = signs[counter % len(signs)]
        sys.stdout.write( "Please wait for scan results... [%s]  (press Ctrl-C to exit)\r" % sign )
        sys.stdout.flush()
        time.sleep(0.5)
        if counter < 999:
            counter = counter + 1
        else:
            counter = 0

        if (counter % 15 == 0 ) :
            conn = httplib.HTTPSConnection(vt)
            conn.request('GET', last_analysis_url, headers=headers)
            req = conn.getresponse()
            conn.close()
            res = req.read()
            if (req.status != 200 and req.status != 302) :
                print "Connection lost. Please try again later..."
                exit(0)
            else:
                if ( req.status != 302 and res.find(trigger_1) == -1 and res.find(trigger_2) == -1) :
                    isComplete = 1
    
    conn = httplib.HTTPSConnection(vt)
    conn.request('GET', last_analysis_url, headers=headers)
    req = conn.getresponse()
    res = req.read()
    conn.close()
    print_vt_results( res, v )


# main function to determine how to deal with input file
def viruscan( apk , verbosity) :
    apk_path = apk
    apk_name = os.path.basename(apk)
    sig = hashlib.sha256(apk).hexdigest()

    vt = "www.virustotal.com"
    uri = "/en/file/upload/?sha256=" + sig + "&_=1"
    url = vt + uri
    try:
        conn = httplib.HTTPSConnection(vt)
        conn.request("GET", url)
        req = conn.getresponse()
        if (req.status != 200):
            print "Server did not accept request, try again or contanct us... "
            exit(0)
        else:
            res = req.read()
            # check if signature already exists in DB
            if ('"file_exists": true,' in res):
            	print "Found file, printing results..."
            	uri = "/en/file/" + sig + "/analysis/"
                url = vt + uri
            	headers = {"Accept-Language": "en-US"}
            	conn.request("GET", url, headers=headers)
            	req = conn.getresponse()
            	if (req.status != 200):
    	    	    print "Server did not accept request, try again or contanct us..."
                    exit(0)
                else:
                    res = req.read()
                    print_vt_results(res, verbosity)

            #results were NOT found, upload process        
            else:
                try:
                    imp.find_module('requests')
                except ImportError:
                    print "Uploading a file requires the module: \033[31mrequests\033[0m; you can install it by running: \033[34mpip install requests\033[0m."
                    sys.exit(1)

                print "Uploading file for scan, might take a few minutes..."
                conn.close()
                upload_apk_to_vt(res, apk_path, url, verbosity)
                    

    except KeyboardInterrupt:
        sys.stdout.flush()
        print "\nYou can run \033[36mandrototal.py\033[0m again to see the results..."
        sys.exit(1)

    except Exception, e:
	   print e
	   print "Could not connect to server, please check your conneciton and try again..."


# select verbosity level from argument (-v/ --verbose)
# must be between 1(min) to 3(max) [default=1]
def select_verbosity_level(v) :
    VERBOSE_MIN = 1
    VERBOSE_MAX = 3
    verbosity = VERBOSE_MIN
    if v != None :
        try:
            received_verbosity = int(v)
            if ( received_verbosity > VERBOSE_MIN and received_verbosity < VERBOSE_MAX+1 ) :
             verbosity = received_verbosity

        except ValueError:
            received_verbosity = None

    return verbosity



def main(options, arguments) :
    if options.input != None :
        ret_type = androconf.is_android( options.input )
        if ret_type == "APK" or ret_type == "DEX"  :
            print "Verifying file against VirusTotal, please hold!"
            verbosity = select_verbosity_level( options.verbose )
            viruscan( options.input, verbosity )
        else:
            print "input file should be apk/dex..."
            return 0


if __name__ == "__main__" :
   parser = OptionParser()
   for option in options :
      param = option['name']
      del option['name']
      parser.add_option(*param, **option)

      
   options, arguments = parser.parse_args()
   sys.argv[:] = arguments
   main(options, arguments) 
