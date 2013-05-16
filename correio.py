import sys
import re
import urllib2
from bs4 import BeautifulSoup

def parse(page):
    page = page.replace('\n','').replace('\r','')
    doc = BeautifulSoup(re.match('.*entrega\.<p>(.+)<hr.*', page).group(1), from_encoding="ISO-8859-1")
    lines = list(reversed(doc.select('tr')))[:-1]
    history = []
    for line in lines:
        line_num = len(line.contents)
        entry = {}
        if line_num == 3:
            entry["datetime"] = line.contents[0].get_text().encode('latin-1')
            entry["local"] = line.contents[1].get_text().encode('latin-1')
            entry["activity"] = line.contents[2].get_text().encode('latin-1')
        elif line_num == 1:
            entry["datetime"] = history[-1]["datetime"]
            entry["local"] = history[-1]["local"]
            entry["activity"] = line.contents[0].get_text()
        history.append(entry)
    return history

if len(sys.argv) > 1:
    page = urllib2.urlopen("http://websro.correios.com.br/sro_bin/txect01$.QueryList?P_LINGUA=001&P_TIPO=001&P_COD_UNI="+sys.argv[1])
    for item in parse(page.read()):
        print item["datetime"]
        print item["local"],":",item["activity"]
