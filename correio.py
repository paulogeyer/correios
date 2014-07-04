import sys
import re
import urllib2
from bs4 import BeautifulSoup

def parse(page):
    history = []
    page = page.replace('\n','').replace('\r','')
    doc = BeautifulSoup(page, from_encoding="ISO-8859-1")
    lines = doc.select('table.listEvent.sro tr')
    for line in lines:
	entry = {}
	date, time, local, _ = ' '.join(line.contents[0].get_text().encode('latin-1').split()).split()
	entry["datetime"] = date+" "+time
	entry["local"] = local
	entry["activity"] = line.contents[1].get_text().encode('latin-1')
	history.append(entry)
    return history


	
