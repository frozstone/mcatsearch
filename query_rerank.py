import solr
import requests, json
import functools
import operator
from collections import OrderedDict

class Query_Rerank:
    solr_conn_doc = ''
    solr_conn_math = ''
    n_row = 0

    def __init__(self, solrdocurl, solrmathurl, nrow):
        self.solr_conn_doc = solr.SolrConnection(solrdocurl)
        self.solr_conn_math = solr.SolrConnection(solrmathurl)
        self.n_row = nrow

    def __ask_solr_math_geometric_mean(self, response, gpid):
        summation = 1.0
        length = 0.0
        while True:
            summation *= functools.reduce(operator.mul, [math['score'] for math in response])
            length += len(response)
            response = response.next_batch()
            if not response: break
        return summation ** (1./length)

    def __ask_solr_math_mean(self, response, gpid):
        summation = 0.0
        length = 0.0
        while True:
            summation += sum([math['score'] for math in response])
            length += len(response)
            response = response.next_batch()
            if not response: break
        return summation/length

    def __ask_solr_math_max(self, response):
        return response.maxScore

    def __ask_solr_math(self, gpid, op):
        resp = self.solr_conn_math.query(q = '*:*', fields = ('score'), fq = 'gpid:(%s)' % gpid)
        if op == 'geomMean': 
            return self.__ask_solr_math_geometric_mean(resp, gpid)
        elif op == 'mean': 
            return self.__ask_solr_math_mean(resp, gpid)
        else: 
            return self.__ask_solr_math_max(resp)

    def ask_solr_math_score(self, query, gpid):
        resp = self.solr_conn_math.query(q = query, fields = ('gmid', 'score'), fq = 'gpid:(%s)' % gpid)
        math_score = {}
        for mt in resp.results:
            math_score[mt['gmid']] = mt['score']
        return math_score, resp.maxScore

    def ask_solr_doc(self, query, op='max'):
        resp = self.solr_conn_doc.query(q = query, fields = ('gpid', 'score'))
        documents = OrderedDict() #{gpid:math_scores}
        while True:
            for doc in resp.results:
                gpid = doc['gpid']
                documents[gpid] = None #self.__ask_solr_math(gpid, op)
            resp = resp.next_batch()
            if len(documents) >= self.n_row or not resp: break
        return documents.items()[:self.n_row]

