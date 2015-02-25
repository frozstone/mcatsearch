import query_mathtext as qmt
#import query_math as qm
from lxml import etree, objectify
from os import path
from pickle import dump, load
from multiprocessing import Pool
from sys import argv

solrurlmath = 'http://localhost:9000/solr/mcd.20150129'
solrurlpara = 'http://localhost:9000/solr/mcd.20150220.p'
nrows = 50

jdic = {}
usectx = None
usedesc = None

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

def openJudgmentFile(jfl, xhtmldictfl):
    f = open(xhtmldictfl, 'rb')
    fullpath = load(f)
    f.close()

    jdic = {}
    lines = open(jfl).readlines()
    for ln in lines:
        cells = ln.split()
        num = cells[0]
        paraid = cells[2]
        if num in jdic:
            jdic[num].append('%s/%s'% (fullpath[paraid[:paraid.index('_')]], paraid + '.xhtml'))
        else:
            jdic[num] = []
    return jdic

def askSolr_mathtext((num, query)):
    print num
    docs_all = {}
    docs_rerank = {}
    docs_all_singleton = {}
    docs_rerank_singleton = {}
    q = qmt.Query(solrurlmath, solrurlpara, nrows, usectx, usedesc)
    for me in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
#        try:
            docs_all[me] = q.askSolr_all(query, jdic[num], me, 0.5)
            docs_rerank[me] = q.askSolr_rerank(query, jdic[num], me, 0.5, 0.5)
            docs_all_singleton[me] = q.askSolr_all_singleton(query, jdic[num], me)
            docs_rerank_singleton[me] = q.askSolr_rerank_singleton(query, jdic[num], me, 0.5, 0.5)
 #       except:
  #          print num + me + ' error'
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
    judgefl = 'NTCIR11_Math-qrels.dat'
    xhtmldict = 'xhtmldict'
    dumpdir = argv[1]
    texttype = argv[2] #choices: ctxnodep, ctx, descnodep, descdep

    qdic = openQueryFile(queryfl)
    jdic = openJudgmentFile(judgefl, xhtmldict)

    usectx, usedesc = parseTextType(texttype)
#    askSolr_mathtext(('NTCIR11-Math-12', qdic['NTCIR11-Math-12']))

    docs_all, docs_rerank, docs_all_singleton, docs_rerank_singleton = askSolrParallel_mathtext(qdic, 25)
    f = open(path.join('math_text_dump_docs_all.dat'), 'wb')
    dump(docs_all, f, -1)
    f.close()
    f = open(path.join('math_text_dump_docs_rerank.dat'), 'wb')
    dump(docs_rerank, f, -1)
    f.close()
    f = open(path.join('math_text_dump_docs_all_singleton.dat'), 'wb')
    dump(docs_all_singleton, f, -1)
    f.close()
    f = open(path.join('math_text_dump_docs_rerank_singleton.dat'), 'wb')
    dump(docs_rerank_singleton, f, -1)
    f.close()
  
#    docs_all, docs_rerank = askSolrParallel_math(qdic, 25)
#    f = open('math_dump_docs_all.dat', 'wb')
#    dump(docs_all, f, -1)
#    f.close()
#    f = open('math_dump_docs_rerank.dat', 'wb')
#    dump(docs_rerank, f, -1)
#    f.close()
 
