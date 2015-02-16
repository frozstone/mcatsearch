from query_all import Query_All
from query_rerank import Query_Rerank
import solr
import requests, json

class Query_Wilkinson:
    solr_conn_doc = ''
    solr_conn_math = ''
    n_row = 0

    def __init__(self, solrdocurl, solrmathurl, nrow):
        self.solr_conn_doc = solr.SolrConnection(solrdocurl)
        self.solr_conn_math = solr.SolrConnection(solrmathurl)
        self.n_row = nrow

    def __normalize_document_score(self, documents, max_E1=1., max_E5=1.):
        for gpid, scores in documents.iteritems():
            scores[0] /= max_E1
            scores[1] /= max_E5

    def __ask_solr_math_sum(self, gpid):
        resp = self.solr_conn_math.query(q = '*:*', fields = ('score'), fq = 'gpid:(%s)' % gpid)
        rank = 1
        summation = 0.0
        while True:
            for math in resp.results:
                summation += (0.5 ** (rank - 1)) * math['score']
                rank += 1
                resp = resp.next_batch()
                if not resp: break
        return summation

    def ask_solr_doc(self, query):
        resp = self.solr_conn_doc.query(q = query, fields = ('gpid', 'score'))
        documents = {} #{gpid: (norm of E1, norm of E5)}
        max_E5 = 0.0
        while True:
            for doc in resp.results:
                gpid = doc['gpid']
                E5 = self.__ask_solr_math_sum(gpid)
                if E5 > max_E5: max_E5 = E5
                documents[gpid] = [doc['score'] / resp.maxScore, E5]
            resp = resp.next_batch()
            if len(documents) >= self.n_row or not resp: break
        self.__normalize_document_score(documents, 1., max_E5)
        return documents
