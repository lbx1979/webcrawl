# -*- coding: utf-8 -*-#

import pymssql
import codecs
#----------------------------------------------------------------------
def  readfile(filename):
    """read file to list"""
    with codecs.open(filename, 'r', encoding="utf-8") as output:
        txt = output.readlines()
        return [tuple(x.split('\t')) for x in txt]

#----------------------------------------------------------------------
def  writebidinfo(datalist):
    """write data to ms sql server"""
    conn=pymssql.connect("10.24.13.178",'lc00019999','aaaaaa','cwbase0001',charset='utf8')
    cur = conn.cursor()
    cur.executemany(u"""INSERT INTO PMCJBIDINFO(XMBH,XMMC,SSDQ,SSDQBH,JSDW,JZMJ,ZBLX,ZBFW,HTGSJ,GGFBSJ,URL) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", datalist)
    conn.commit()
    cur.close()
    conn.close()
    
def writebidresult(datalist):

    with pymssql.connect("10.24.13.178",'lc00019999','aaaaaa','cwbase0001',charset='utf8') as conn:
        with conn.cursor() as cur :
            for r in datalist:
                try:             
                    cur.execute(u"""INSERT INTO PMCJBIDRESULT(XMBH,XMMC,SSDQ,SSDQBH,JSDW,ZBFS,JZMJ,ZBLX,ZBDW,ZBJG,ZBSJ,URL) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", r)
                except pymssql.ProgrammingError:
                    print r
            conn.commit()
    
if __name__ == '__main__':
    rows = readfile("beijing_bid.txt")
    writebidinfo(rows)       
    
    print "%s rows write to PMCJBIDINFO" % len(rows)
    
    rows = readfile("beijing_bid_result.txt")
    writebidresult(rows)    
     
    print "%s rows write to PMCJBIDRESULT" % len(rows)