import solr
import requests, json

s = solr.SolrConnection('http://localhost:8080/solr/mcd.20150129')
resp = s.query(q = '*:*', fq='gpid:(2/math0101249/math0101249_1_22.xhtml)', fields = ('gmid, gpid, score'))
while True:
    for hit in resp:
        print hit['gmid']
    if resp.next_batch():
        resp = resp.next_batch()
    else:
        break
