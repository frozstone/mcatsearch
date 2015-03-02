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

    def ask_solr_math_score(self, query, candidates):
        respmax = self.solr_conn_math.query(q = query, fields = ('gmid', 'score'))
        math_score = {}
        gpids = ' OR '.join(candidates)
        resp = self.solr_conn_math.query(q = query, fields = ('gmid', 'gpid', 'score'), fq = 'gpid:(%s)' % gpids)
        while True:
            for mt in resp.results:
                if mt['gpid'] not in math_score: math_score[mt['gpid']] = {}
                math_score[mt['gpid']][mt['gmid']] = mt['score']
            resp = resp.next_batch()
            if not resp: break
        return math_score, respmax.maxScore

    def ask_solr_doc_max_score(self, query):
        resp = self.solr_conn_doc.query(q = query, fields = ('gpid', 'score'))
        return resp.maxScore

    def ask_solr_doc(self, query, candidates):
        documents = OrderedDict() #{gpid:math_scores}
        gpids = ' OR '.join(candidates)
        resp = self.solr_conn_doc.query(q = query, fields = ('gpid', 'score'), fq = 'gpid:(%s)' % gpids)
        while True:
            for mt in resp.results:
                documents[mt['gpid']] = mt['score']
            resp = resp.next_batch()
            if not resp: break
        return documents

