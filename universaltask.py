# -*- coding: utf-8 -*-#

import types
import re
import json
from bs4 import BeautifulSoup
import collections
import types
import codecs
#----------------------------------------------------------------------
def getconfig(filename):
    """get specified config json"""

    __cfgFile = open(filename,'r');
    __cfgData = __cfgFile.read();
    jsonCfg = json.loads(__cfgData, object_pairs_hook=collections.OrderedDict);
    return jsonCfg

def get_encoding(s):
    if isinstance(s,unicode):
        return "unicode"
    try:
        r = unicode(s)
        return "ASCII"
    except:
        try:
            r = s.decode("utf8")
            return "utf8"
        except:
            try:
                r = s.decode("gbk")
                return "gbk"
            except:
                try:
                    r = s.decode("latin-1")
                    return "latin-1"
                except:
                    pass


#----------------------------------------------------------------------
def pageparserExEx(page, parser):
    """get needed info from page"""

    if type(page) is types.UnicodeType or type(page) is types.StringType:
        page = BeautifulSoup(page)
    row = ""
    #XMBH
    for (k,v) in parser.items():
        text = gettagtext(page, v)
        if type(text) is types.NoneType:
            text = ""
        else:
            text = text.strip()
        if "format" in v:
            if v["format"] == "tenthousand":
                try:
                    text = str(float(text) / 10000)
                except ValueError:
                    text = ''

            elif "left" in v["format"]:
                left = int(v["format"]["left"])
                if len(text) >= 2:
                    text = text[:left]
        row += text+"\t"
    return row

#----------------------------------------------------------------------
def gettagtext(soup, conf):
    """get element text from soup tree"""

    v = conf
    text = ""
    tag = None
    if "default" in v:
        text = v["default"]

    if "name" in v:
        tag = soup.find(v["name"], v["attrs"])

    elif "searchtext" in v:
        tag = soup.find(text=re.compile(v["searchtext"]))
        try:
            tag = tag.parent
        except:
            tag = None

    #get child tag
    if tag:
        while "subtag" in v:
            v = v["subtag"]
            #find children tag if existing config
            func = getattr(tag, v["func"])
            if "name" in v:
                if "attrs" in v:
                    tag = func(v["name"], v["attrs"])
                else:
                    tag = func(v["name"])
            else:
                tag = func()

            if "index" in v:
                tag = tag[v["index"]]

    if tag:
        if "valueattr" in v:
            text = tag[v["valueattr"]]
        else:
            text = tag.text
        plaintxt = text
    else:
        plaintxt = soup.text
        
    if "reg" in v:
            result = re.findall(v["reg"], plaintxt);
            if len(result)>0:
                text = "".join(result[0])

    return text

#----------------------------------------------------------------------
def find_tag(soup, conf):
    """get element from soup tree"""

    v = conf
    tag = None
    if "name" in v:
        tag = soup.find(v["name"], v["attrs"])

    elif "searchtext" in v:
        tag = soup.find(text=v["searchtext"])
        try:
            tag = tag.parent
        except:
            tag = None

    #get child tag
    if tag:
        while "subtag" in v:
            v = v["subtag"]
            #find children tag if existing config
            func = getattr(tag, v["func"])
            if "name" in v:
                if "attrs" in v:
                    tag = func(v["name"], v["attrs"])
                else:
                    tag = func(v["name"])
            else:
                tag = func()

            if "index" in v:
                tag = tag[v["index"]]
    
    return tag

def find_all_tags(soup, conf):
    """get element from soup tree"""

    v = conf
    tags = None
    result = None
    if "name" in v:
        tags = soup.find_all(v["name"], v["attrs"])

    elif "searchtext" in v:
        tags = soup.find_all(text=v["searchtext"])       
    
    if len(tags) == 0:
        return tags
    
    #get child tag
    subtags = set()
    children = set()
    while "subtag" in v:                
        v = v["subtag"]
        if len(subtags) ==0:
            subtags = set(tags)
        elif len(children)>0:
            subtags = children
        else:
            break
        
        children = set()
        for tag in subtags:
            #find children tag if existing config
            func = getattr(tag, v["func"])
            if "name" in v:
                if "attrs" in v:
                    tag = func(v["name"], v["attrs"])
                else:
                    tag = func(v["name"])
            else:
                tag = func()

            if "index" in v:
                tag = tag[v["index"]]
            
            if tag:
                if isinstance(tag, list):
                    children.update(tag)
                else:
                    children.add(tag)
                
    if "subtag" in conf:
        result = list(children)
    else:
        result = tags
        
    if "valueattr" in v:
        result = [x[v["valueattr"]] for x in result]
    return result    

def writefile(strlist, filename):
    _list = [line+u'\n' for line in strlist]
    with codecs.open(filename, 'w', encoding="utf-8") as output:
        output.writelines(_list)
