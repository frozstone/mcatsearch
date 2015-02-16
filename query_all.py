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
        maths = {}
        documents = {}
        while True:
            for doc in response.results:
                gmid = doc['gmid']
                gpid = doc['gpid']
                maths[gmid] = doc['score']
                if gpid not in documents:
                    documents[gpid] = doc['score']
            response = response.next_batch()
            if len(documents) >= self.n_row or not response: break
        return maths, documents

    def __ask_solr_math(self, query, op):
        resp = self.solr_connection.query(q = query, fields = ('gmid, gpid, score'))
        if op == 'max':
            return self.__ask_solr_math_max(resp)

    def ask_solr_math_score(self, query, gmid):
        resp = self.solr_connection.query(q = query, fields = ('score'), fq = 'gmid:(%s)' % gmid)
        return resp.results[0]['score'] if len(resp.results) > 0 else 0.0

    def ask_solr_doc(self, query, op='max'):
        maths, documents = self.__ask_solr_math(query, op)
        maths = sorted(maths.iteritems(), key=operator.itemgetter(1), reverse = True)
        documents = sorted(documents.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.n_row]
        return maths, documents
