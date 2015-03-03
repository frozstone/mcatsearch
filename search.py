import query_mathtext as qmt
import query_math as qm
from lxml import etree, objectify
from os import path
from pickle import dump
from multiprocessing import Pool
from sys import argv

solrurlmath = 'http://localhost:9000/solr/mcd.201500203'
solrurlpara = 'http://localhost:9000/solr/mcd.20150220.p'
nrows = 50

usectx = None
usedesc = None
scorecomb = None

def getCleanTopics(qfl):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(qfl, parser)
    root = tree.getroot()
    for elem in root.getiterator():
        if not hasattr(elem.tag, 'find'): continue
        i = elem.tag.find('}')
        if i >= 0:
            elem.tag = elem.tag[i+1:]
    objectify.deannotate(root, cleanup_namespaces=True)
    return root

def openQueryFile(qfl):
    qdic = {} #{qnum:{math:[string1, string2], keyword:[string1, string2]}}
    qxml = getCleanTopics(qfl)
    for qtopic in qxml.findall('.//topic'):
        num = qtopic.find('num').text
        qdic[num] = {'math': [], 'keyword': []}
        qquery = qtopic.find('query')
        for qformula in qquery.findall('formula'):
            qdic[num]['math'].append(etree.tostring(qformula[0], encoding='utf-8'))
        for qkeyword in qquery.findall('keyword'):
            qdic[num]['keyword'].append(qkeyword.text)
    return qdic

def askSolr_mathtext((num, query)):
    print num
    docs_all = {}
    docs_rerank = {}
    docs_all_singleton = {}
    docs_rerank_singleton = {}
    q = qmt.Query(solrurlmath, solrurlpara, nrows, usectx, usedesc, scorecomb)
    for me in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
        try:
            docs_all[me] = q.askSolr_all(query, me, 0.5)
            docs_rerank[me] = q.askSolr_rerank(query, me, 0.5, 0.5)
            docs_all_singleton[me] = q.askSolr_all_singleton(query, me)
            docs_rerank_singleton[me] = q.askSolr_rerank_singleton(query, me, 0.5, 0.5)
        except:
            print num + me + ' error'
    print num + ' finish'
    return num, docs_all, docs_rerank, docs_all_singleton, docs_rerank_singleton

def askSolrParallel_mathtext(qdic, cores):
    pool = Pool(processes=cores)
    scenario_all = {}
    scenario_rerank = {}
    scenario_all_singleton = {}
    scenario_rerank_singleton = {}
    for num, docs_all, docs_rerank, docs_all_singleton, docs_rerank_singleton in pool.map(askSolr_mathtext, qdic.items()):
        scenario_all[num] = docs_all
        scenario_rerank[num] = docs_rerank
        scenario_all_singleton[num] = docs_all_singleton
        scenario_rerank_singleton[num] = docs_rerank_singleton
    return scenario_all, scenario_rerank, scenario_all_singleton, scenario_rerank_singleton

def askSolr_math((num, query)):
    print num
    docs_all = {}
    docs_rerank = {}
    q = qm.Query(solrurlmath, solrurlpara, nrows)
    for me in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
        try:
            docs_all[me] = q.askSolr_all(query, me)
            docs_rerank[me] = q.askSolr_rerank(query, me, 0.5)
        except:
            print num + me + ' error'
    print num + ' finish'
    return num, docs_all, docs_rerank

def askSolrParallel_math(qdic, cores):
    pool = Pool(processes=cores)
    scenario_all = {}
    scenario_rerank = {}
    for num, docs_all, docs_rerank in pool.map(askSolr_math, qdic.items()):
        scenario_all[num] = docs_all
        scenario_rerank[num] = docs_rerank
    return scenario_all, scenario_rerank

def parseTextType(texttype):
    usectx = None
    usedesc = None
    if 'ctx' in texttype:
        if 'ctxdep' in texttype: usectx = True
        else: usectx = False
    if 'desc' in texttype:
        if 'descdep' in texttype: usedesc = True
        else: usedesc = False
    return usectx, usedesc

if __name__ == '__main__':
    queryfl = 'NTCIR11-Math2-queries-participants.xml'
    judgefl = ''
    dumpdir = argv[1]
    texttype = argv[2] #ctxnodep, ctxdep, descnoep, descdep
    scorecomb = argv[3] #max, sum

    qdic = openQueryFile(queryfl)
    usectx, usedesc = parseTextType(texttype)
#    askSolr_mathtext(('NTCIR11-Math-12', qdic['NTCIR11-Math-12']))

    docs_all, docs_rerank, docs_all_singleton, docs_rerank_singleton = askSolrParallel_mathtext(qdic, 50)
    f = open(path.join(dumpdir, 'math_text_dump_docs_all.dat'), 'wb')
    dump(docs_all, f, -1)
    f.close()
    f = open(path.join(dumpdir, 'math_text_dump_docs_rerank.dat'), 'wb')
    dump(docs_rerank, f, -1)
    f.close()
    f = open(path.join(dumpdir, 'math_text_dump_docs_all_singleton.dat'), 'wb')
    dump(docs_all_singleton, f, -1)
    f.close()
    f = open(path.join(dumpdir, 'math_text_dump_docs_rerank_singleton.dat'), 'wb')
    dump(docs_rerank_singleton, f, -1)
    f.close()
  
    docs_all, docs_rerank = askSolrParallel_math(qdic, 50)
    f = open(path.join(dumpdir, 'math_dump_docs_all.dat'), 'wb')
    dump(docs_all, f, -1)
    f.close()
    f = open(path.join(dumpdir, 'math_dump_docs_rerank.dat'), 'wb')
    dump(docs_rerank, f, -1)
#    f.close()
 
