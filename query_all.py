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
        document_score = {}
        while True:
            for doc in response.results:
                gmid = doc['gmid']
                gpid = doc['gpid']
                score = doc['score']
                maths_score[gmid] = score
                if (gpid not in document_score) or (gpid in document_score and score > document_score[gpid]):
                    document_score[gpid] = score
            response = response.next_batch()
            if not response: break
        return maths_score, document_score

    def __ask_solr_math_sum(self, response):
        maths_score = {}
        document_score = {}
        while True:
            for doc in response.results:
                gmid = doc['gmid']
                gpid = doc['gpid']
                score = doc['score']
                maths_score[gmid] = score
                if (gpid not in document_score): document_score[gpid] = score
                else: document_score[gpid] += score
            response = response.next_batch()
            if not response: break
        return maths_score, document_score
    
    def __ask_solr_math(self, query, candidates, op):
        gpids = ' OR '.join(candidates)
        resp = self.solr_connection.query(q = query, fields = ('gmid, gpid, score'), fq = 'gpid:(%s)' % gpids)
        if op == 'max':
            return self.__ask_solr_math_max(resp)
        elif op == 'sum':
            return  self.__ask_solr_math_sum(resp)

    def ask_solr_math_score(self, query, gmid):
        resp = self.solr_connection.query(q = query, fields = ('score'), fq = 'gmid:(%s)' % gmid)
        return resp.results[0]['score'] if len(resp.results) > 0 else 0.0

    def ask_solr_max_score(self, query):
        resp = self.solr_connection.query(q = query, fields = ('score'))
        return resp.maxScore

    def ask_solr_doc(self, query, candidates, op):
        maths, documents = self.__ask_solr_math(query, candidates, op)
        documents = sorted(documents.iteritems(), key=operator.itemgetter(1), reverse=True)[:self.n_row]
        return maths, documents
