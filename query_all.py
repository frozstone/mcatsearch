import solr
import requests, json
import operator

class Query_All:
    solr_connection = ''
    n_row = 0

    def __init__(self, solrurl, nrow):
        self.solr_connection = solr.SolrConnection(solrurl)
        self.n_row = nrow

    def __ask_solr_math_max(self, response):
        maths_score = {}
        document_score = response.maxScore
        while True:
            for doc in response.results:
                gmid = doc['gmid']
                gpid = doc['gpid']
                maths_score[gmid] = doc['score']
            response = response.next_batch()
            if not response: break
        return maths_score, document_score

    def __ask_solr_math(self, query, candidates, op):
        maths = {}
        documents = {}
        for gpid in candidates:
            resp = self.solr_connection.query(q = query, fields = ('gmid, gpid, score'), fq = 'gpid:(%s)' % gpid)
            if op == 'max':
                maths_score, document_score = self.__ask_solr_math_max(resp)
                documents[gpid] = document_score
                maths.update(maths_score)
        return maths, documents

    def ask_solr_math_score(self, query, gmid):
        resp = self.solr_connection.query(q = query, fields = ('score'), fq = 'gmid:(%s)' % gmid)
        return resp.results[0]['score'] if len(resp.results) > 0 else 0.0

    def ask_solr_max_score(self, query):
        resp = self.solr_connection.query(q = query, fields = ('score'))
        return resp.maxScore

    def ask_solr_doc(self, query, candidates, op='max'):
        maths, documents = self.__ask_solr_math(query, candidates, op)
        documents = sorted(documents.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.n_row]
        return maths, documents
