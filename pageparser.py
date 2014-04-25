# -*- coding: utf-8 -*-

import sys
import os.path
import time
import types
import re
import json
import logging
import importlib
import requests
from bs4 import BeautifulSoup
import params
import universaltask

#----------------------------------------------------------------------
########################################################################
class commonPageTask():
    """paginating & detail info """

    #----------------------------------------------------------------------
    def __init__(self, configfile=""):
        """Constructor"""
        if len(sys.argv) > 1:
            arg = sys.argv[1]
        elif configfile.strip() != "":
            arg = configfile
        else:
            print "please input a config file name"
            sys.exit(1)

        self.configfile = arg
        self.config = universaltask.getconfig(arg+".json")
        self.location = self.config ["location"] #identify data for the config and output file
        self.urls = self.config ["urls"] #array list about url to handle
        self.detailurl  = self.config ["detailurl"]  #detail page url
        logging.basicConfig(filename = os.path.join(os.getcwd(), self.configfile+'_log.txt'),level = logging.DEBUG, format = '%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger()
    #----------------------------------------------------------------------
    def paginateinfo(self):
        """get urls from first and paged web"""
        urllist = list()
        i=0
        for url in self.urls:
            try:
                i+=1
                #get more page
                htmls = self.paginate(url, i)
                for html in htmls:
                    foo = self.geturl(html,i)
                    foo = [{'href':x, "key":"url"+str(i)} for x in foo]                    
                    urllist.extend(foo)

                #sleep some seconds
                time.sleep(params.intervaltime)
            except requests.exceptions.ConnectionError:
                continue
        return urllist

    def paginate(self, url, index):
        """get detail urls"""
        
        key = "url%spaginate" % index
        paginateconfig = None
        if key in self.config:
            paginateconfig = self.config[key]
        elif "urlpaginate" in self.config:
            paginateconfig = self.config["urlpaginate"]
        
        if paginateconfig:
            httpmethod = paginateconfig["method"]
            replacekey = paginateconfig["replacekey"]
            replaceexpress = paginateconfig["replaceexpress"] #constant variable #number#
            initexpress = paginateconfig["initexpress"]
            
            if httpmethod == "get":
                initurl = url.replace(replacekey, replaceexpress.replace("#number#",initexpress))
                r = requests.get(initurl) #get first page content
                soup = BeautifulSoup(r.text)
            elif httpmethod == "post":
                r = requests.get(url) #get first page content
                soup = BeautifulSoup(r.text)
                postdata = paginateconfig["postdata"]
                formdata = dict()
                for (k,v) in postdata.items():
                    formdata[k] = universaltask.gettagtext(soup, v)
                
            yield r.text

            #search paginated info          
            maxpagetag = paginateconfig["maxpagetag"]
            totalPage = universaltask.gettagtext(soup, maxpagetag)
            if len(totalPage) == 0:
                print 'totalpage tag cannot be found'
                sys.exit(1)            
                    
            totalPage = int(totalPage)

            if "maxpagecount" in paginateconfig:
                maxcount = int(paginateconfig["maxpagecount"])
            else:
                maxcount = totalPage

            try:
                initexpress = int(initexpress)
            except:
                initexpress = 0

            nextIndex = initexpress+1
            while nextIndex <= totalPage and nextIndex <= maxcount:
                if httpmethod == "get":
                    nexturl = url.replace(replacekey, replaceexpress.replace("#number#",str(nextIndex)))
                    r = requests.get(nexturl)
                else:
                    #submit control about paginate
                    formdata[replacekey] = nextIndex
                    r = requests.post(url, data=formdata)
                sourcehtml = r.text
                yield sourcehtml
                nextIndex += 1
                time.sleep(params.intervaltime)

        else:
            r = requests.get(url) #get first page content
            yield r.text

    def geturl(self, html, i):
        """search url from html code"""

        urlset = set()
        soup = BeautifulSoup(html)
        #get list url markup info from config
        listurlconfig = None
        key = "url%slist" % i        
        if key in self.config:
            listurlconfig = self.config[key]
        elif "urllist" in self.config:
            listurlconfig = self.config["urllist"]
        
        if listurlconfig:    
            containertag = listurlconfig ["containertag"]
            
            #replace mode if replacekey exist
            replacemode = False
            if "replacekey" in listurlconfig:
                replacekey = listurlconfig["replacekey"]
                replaceexpress = listurlconfig["replaceexpress"] #must be a regex
                replacemode = True
                
            #urls = container.findAll(targettag, targetattr)    
            urls = universaltask.find_all_tags(soup, containertag)
            for href in urls:                
                #href = a[valuesttr]
                if replacemode:
                    href = "".join(re.findall(replaceexpress, href)[0])
                    urlset.add(self.detailurl.replace(replacekey, href))
                else:
                    urlset.add(self.detailurl + href)                
        return list(urlset)

    def getdetail(self, urllist):
        """ get necessary info from page by config """
        datalist = list()
        methods = dict()
        errcount = 0
        parsers =[x[:-6] for x in self.config if x.find('parser')>0 and x.find('url')==-1]
        
        for url in urllist:
            requestcfgkey = "%srequest" %url["key"]
            try:
                if requestcfgkey in  self.config: #ssl need this config section
                    verify = self.config[requestcfgkey]["verify"]
                    headers = self.config[requestcfgkey]["headers"]
                    r = requests.get(url["href"], headers=headers, verify=verify)
                else:
                    r = requests.get(url["href"])
            except requests.exceptions.ConnectionError:
                if errcount == 5:
                    self.logger.error("ConnectionError %s" % r)
                    sys.exit(1)
                else:
                    time.sleep(params.singlepage)
                    errcount += 1
            
            #some site cannot identify source encoding
            encode = universaltask.get_encoding(r.content)
            unihtml = r.content.decode(encode)
            

            parserid = "%sparser" %url["key"]
            if parserid not in self.config: #url config maybe wwww.domain.comparser
                for x in parsers:
                    if url["href"].find(x)>=0:
                        parserid = "%sparser" % x
                        break
                
            hanlderconfig = "%shandler" % url["key"]

            #check if exist any customized handler configuration in config file
            if hanlderconfig in  self.config:
                m = self.config[hanlderconfig]
                #"url1handler":{"module":"tianjin","method":"getbiddetail"},
                try:
                    k = "%s.%s" % (m["module"], m["method"])
                    if k in methods:
                        handlerMethod = methods[k]
                    else:
                        exmodule = importlib.import_module(m["module"])
                        handlerMethod = getattr(exmodule, m["method"])
                        methods[k] = handlerMethod

                    row = handlerMethod(unihtml, self.config[parserid]) + url["href"]
                except ImportError:
                    print "%s module not found!"%m["module"]
                    sys.exit(1)
            elif parserid in self.config:
                row = self.pageparser(unihtml, self.config[parserid]) + url["href"]
            else:
                print "%s cannot be found in %s.json" % (parserid, self.configfile)
                sys.exit(1)
            datalist.append(row)
            time.sleep(params.singlepage)
        return datalist

    def pageparser(self, html, parserconfig):
        text = universaltask.pageparserExEx(html, parserconfig)
        return text

    def output(self, detaillist):
        """get output config, may generate file,save into db and so on..."""
        if "output" in self.config:
            cfg = self.config["output"]
            if cfg["type"] == "file":
                universaltask.writefile(detaillist, cfg["file"])


if __name__ == '__main__':
    b = commonPageTask('config_jiangsu_bid')
    urls = b.paginateinfo()
    for url in urls:
        print url["href"]
    #list = b.getdetail(urls)
    #b.output(list)
    #print '%s rows have been written to the file' % len(list)
