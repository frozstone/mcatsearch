from query_mathtext import Query 
from lxml import etree, objectify
from os import path
from pickle import dump
from multiprocessing import Pool

solrurlmath = 'http://localhost:9000/solr/mcd.20150129'
solrurlpara = 'http://localhost:9000/solr/mcd.20150203.p'
nrows = 50

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

def askSolr((num, query)):
    print num
    docs_all = {}
    docs_rerank = {}
    q = Query(solrurlmath, solrurlpara, nrows)
    for me in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
        docs_all[me] = q.askSolr_all(query, me, 0.2)
        docs_rerank[me] = q.askSolr_rerank(query, me, 0.2)
    print num + ' finish'
    return num, docs_all, docs_rerank

def askSolrParallel(qdic, cores):
    pool = Pool(processes=cores)
    scenario_all = {}
    scenario_rerank = {}
    for num, docs_all, docs_rerank in pool.map(askSolr, qdic.items()):
        scenario_all[num] = docs_all
        scenario_rerank[num] = docs_rerank
    return scenario_all, scenario_rerank

if __name__ == '__main__':
    queryfl = 'NTCIR11-Math2-queries-participants.xml'
    judgefl = ''
    qdic = openQueryFile(queryfl)
#    askSolr(('NTCIR11-Math-50', qdic['NTCIR11-Math-50']))
    docs_all, docs_rerank = askSolrParallel(qdic, 4)
    f = open('dump_docs_all.dat', 'wb')
    dump(docs_all, f, -1)
    f.close()
    f = open('dump_docs_rerank.dat', 'wb')
    dump(docs_rerank, f, -1)
    f.close()

