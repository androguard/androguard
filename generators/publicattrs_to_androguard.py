import requests
from lxml import etree
from collections import defaultdict
import json
import os

# At this URL, there should be the public.xml file
url = "https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/master/core/res/res/values/public.xml"

r = requests.get(url)

if r.status_code == 200:
    res = defaultdict(dict)
    tree = etree.fromstring(r.text.encode("UTF-8"))

    for m in tree.xpath('public'):
        t = m.attrib['type']
        name = m.attrib['name']
        i = int(m.attrib['id'], 16)

        res[t][name] = i

    with open(os.path.join("androguard", "core", "resources", "public.json"), "w") as fp:
        json.dump(res, fp, indent="    ")
