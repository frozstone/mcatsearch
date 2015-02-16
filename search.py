import query_mathtext as qmt
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

def askSolr_mathtext((num, query)):
    print num
    docs_all = {}
    docs_rerank = {}
    q = qmt.Query(solrurlmath, solrurlpara, nrows)
    for me in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
        try:
            docs_all[me] = q.askSolr_all(query, me, 0.5)
            docs_rerank[me] = q.askSolr_rerank(query, me, 0.5, 0.5)
        except:
            print num + me + ' error'
    print num + ' finish'
    return num, docs_all, docs_rerank

def askSolrParallel_mathtext(qdic, cores):
    pool = Pool(processes=cores)
    scenario_all = {}
    scenario_rerank = {}
    for num, docs_all, docs_rerank in pool.map(askSolr_mathtext, qdic.items()):
        scenario_all[num] = docs_all
        scenario_rerank[num] = docs_rerank
    return scenario_all, scenario_rerank

if __name__ == '__main__':
    queryfl = 'NTCIR11-Math2-queries-participants.xml'
    judgefl = ''
    qdic = openQueryFile(queryfl)
#    askSolr_mathtext(('NTCIR11-Math-12', qdic['NTCIR11-Math-12']))
    docs_all, docs_rerank = askSolrParallel_mathtext(qdic, 25)
    f = open('math_text_dump_docs_all.dat', 'wb')
    dump(docs_all, f, -1)
    f.close()
    f = open('math_text_dump_docs_rerank.dat', 'wb')
    dump(docs_rerank, f, -1)
    f.close()
  
 
