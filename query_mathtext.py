from mathml_presentation_query import MathMLPresentation
from mathml_content_query import MathMLContent
from query_all import Query_All
from query_rerank import Query_Rerank
import modular, sigure, subtree
from collections import OrderedDict
import functools
import operator
import re

re_escape = r'([+&|!(){}[\]"~*?:\\^-])'
re_qvar = r'\bqvar\b'

class Query:
    solr_url_math = ''
    solr_url_para = ''
    n_row = 0

    def __init__(self, solrurlmath, solrurlpara, nrow):
        self.solr_url_math = solrurlmath
        self.solr_url_para = solrurlpara
        self.n_row = nrow

    def __escape(self, string):
        return re.sub(re_qvar, '', re.sub(re_escape, r'\\\1', string))

    def __getUnicodeText(self, string):
        if type(string) is str:
            return string.decode('utf-8')
        else:
            return string

    def __encodeMaths_path_pres(self, mts_string):
        procPres = MathMLPresentation('http://localhost:9000/upconvert')
        semantics, mathml_string, mathml_presentation = procPres.get_doc_with_orig(mts_string)
        opaths = []
        upaths = []
        sisters = []
        if semantics is not None:
            opaths, sisters = procPres.get_ordered_paths_and_sisters(semantics, False)
            upaths = map(lambda paths: ' '.join(map(self.__getUnicodeText, paths)), procPres.get_unordered_paths(opaths))
            opaths = map(lambda paths: ' '.join(map(self.__getUnicodeText, paths)), opaths)
        return opaths, upaths, sisters

    def __encodeMaths_hash_pres(self, mts_string):
        procPres = MathMLPresentation('http://localhost:9000/upconvert')
        semantics, mathml_string, mathml_presentation = procPres.get_doc_with_orig(mts_string)
        psubhash = []
        psighash = []
        pmodhash = []
        if semantics is not None:
            psubhash = subtree.hash_string(mathml_presentation)
            psighash = sigure.hash_string(mathml_presentation)
            pmodhash = modular.hash_string_generator(2 ** 32)(mathml_presentation)
        return psubhash, psighash, pmodhash 

    def __encodeMaths_path_cont(self, mts_string):
        procCont = MathMLContent()
        oopers = []
        oargs = []
        uopers = []
        uargs = []
        trees, cmathmls_str = procCont.encode_mathml_as_tree(mts_string)
        for tree in trees:
            ooper, oarg = procCont.encode_paths(tree)
            uoper = procCont.get_unordered_paths(ooper)
            uarg = procCont.get_unordered_paths(oarg)
            oopers.extend(map(self.__getUnicodeText, ooper))
            uopers.extend(map(self.__getUnicodeText, uoper))
            oargs.extend(map(self.__getUnicodeText, oarg))
            uargs.extend(map(self.__getUnicodeText, uarg))
        return oopers[-1], oargs[-1], uopers[-1], uargs[-1]

    def __encodeMaths_hash_cont(self, mts_string):
        procCont = MathMLContent()
        trees, cmathmls_str = procCont.encode_mathml_as_tree(mts_string)
        csubhash = []
        csighash = []
        cmodhash = []
        for cmathml_str in cmathmls_str:
            csubhash.extend(subtree.hash_string(cmathml_str))
            csighash.extend(sigure.hash_string(cmathml_str))
            cmodhash.extend(modular.hash_string_generator(2 ** 32)(cmathml_str))
        return csubhash, csighash, cmodhash

    def __constructSolrQuery_words(self, query_element):
        #construct keyword query
        terms_word = []
        for qkeyword in query_element['keyword']:
            terms_word.extend(qkeyword.strip().split(' '))
        terms_word = ' OR '.join(terms_word)
        context_en_query = 'context_en:(%s)' % terms_word
        description_en_query = 'description_en:(%s)' % terms_word
        context_ch_query = 'context_children:(%s)' % terms_word
        description_ch_query = 'description_children:(%s)' % terms_word
        return ' '.join([context_en_query, context_ch_query, description_en_query, description_ch_query])

    def __constructSolrQuery_para_words(self, query_element):
        #construct keyword query
        terms_word = []
        for qkeyword in query_element['keyword']:
            terms_word.extend(qkeyword.strip().split(' '))
        terms_word = ' OR '.join(terms_word)
        context_en_query = 'context_en:(%s)' % terms_word
        description_en_query = 'description_en:(%s)' % terms_word
        context_ch_query = 'context_children:(%s)' % terms_word
        description_ch_query = 'description_children:(%s)' % terms_word
        body = 'body:(%s)' % terms_word
        return ' '.join([context_en_query, context_ch_query, description_en_query, description_ch_query, body])

    def __constructSolrQuery_math_path_pres(self, qmath):
        opath, upath, sister = self.__encodeMaths_path_pres(qmath)
        opath_query = "opaths:('%s')" % self.__escape(' '.join(opath))
        upath_query = "upaths:('%s')" % self.__escape(' '.join(upath))
        sister_query = ' '.join(map(lambda family: "sisters:('%s')" % self.__escape(' '.join(family)), sister))
        return opath_query, upath_query, sister_query

    def __constructSolrQuery_math_path_cont(self, qmath):
        ooper, oarg, uoper, uarg = self.__encodeMaths_path_cont(qmath)
        ooper_query = "ooper:('%s')" % self.__escape(' '.join(ooper))
        oarg_query = "oarg:('%s')" % self.__escape(' '.join(oarg))
        uoper_query = "uoper:('%s')" % self.__escape(' '.join(uoper))
        uarg_query = "uarg:('%s')" % self.__escape(' '.join(uarg)) 
        return ooper_query, oarg_query, uoper_query, uarg_query

    def __constructSolrQuery_math_hash_pres(self, qmath):
        psubhash, psighash, pmodhash = self.__encodeMaths_hash_pres(qmath)
        psubhash_query = "subtree_presentation:(%s)" % (' '.join([str(val) for val in psubhash]).replace('-', '\-') if len(psubhash) > 0 else '*')
        psighash_query = "sigure_presentation:(%s)" % (' '.join([str(val) for val in psighash]).replace('-', '\-') if len(psighash) > 0 else '*')
        pmodhash_query = "modular_presentation:(%s)" % (' '.join([str(val) for val in pmodhash]).replace('-', '\-') if len(pmodhash) > 0 else '*')
        return psubhash_query, psighash_query, pmodhash_query
    
    def __constructSolrQuery_math_hash_cont(self, qmath):
        csubhash, csighash, cmodhash = self.__encodeMaths_hash_cont(qmath)
        csubhash_query = "subtree_content:(%s)" % (' '.join([str(val) for val in csubhash]).replace('-', '\-') if len(csubhash) > 0 else '*')
        csighash_query = "sigure_content:(%s)" % (' '.join([str(val) for val in csighash]).replace('-', '\-') if len(csighash) > 0 else '*')
        cmodhash_query = "modular_content:(%s)" % (' '.join([str(val) for val in cmodhash]).replace('-', '\-') if len(cmodhash) > 0 else '*')
        return csubhash_query, csighash_query, cmodhash_query
        

    def __constructSolrQuery_math(self, query_element, mathencode):
        #construct math query
        query = []
        for qmath in query_element['math']:
            opath_query, upath_query, sister_query = self.__constructSolrQuery_math_path_pres(qmath)
            ooper_query, oarg_query, uoper_query, uarg_query = self.__constructSolrQuery_math_path_cont(qmath)
            psubhash_query, psighash_query, pmodhash_query = self.__constructSolrQuery_math_hash_pres(qmath)
            csubhash_query, csighash_query, cmodhash_query = self.__constructSolrQuery_math_hash_cont(qmath)
            
#            print ' '.join([opath_query, upath_query, sister_query,ooper_query, oarg_query, uoper_query, uarg_query,psubhash_query, psighash_query, pmodhash_query,csubhash_query, csighash_query, cmodhash_query])
            whole_query = ''
            #comb:path pres
            if mathencode == 'pathpres': 
                whole_query = ' '.join([opath_query, upath_query, sister_query])
            #comb2: path content
            elif mathencode == 'pathcont':
                whole_query = ' '.join([ooper_query, oarg_query, uoper_query, uarg_query])
            #comb3: hash pres
            elif mathencode == 'hashpres':
                whole_query = ' '.join([psubhash_query, psighash_query, pmodhash_query])
            #comb4: hash content
            elif mathencode == 'hashcont':
                whole_query = ' '.join([csubhash_query, csighash_query, cmodhash_query])

            query.append(whole_query)
        return query

    def __summarize_score_geometric_mean(self, all_maths):
        scores = [score for score in all_maths.itervalues() if score > 0.]
        return functools.reduce(operator.mul, scores) ** (1./len(scores))

    def __summarize_score_mean(self, all_maths):
        return sum(all_maths.values())/len(scores)

    def __summarize_score_max(self, all_maths):
        return max(all_maths.values()) 

    def __combine_textscore_mathscore(self, qtext_maths, qmath_maths, qtext_maxscore, qmath_maxscore, alpha):
        all_maths = dict.fromkeys(qtext_maths.keys() + qmath_maths.keys())
        for mt in all_maths.keys():
            text_score = qtext_maths[mt] if mt in qtext_maths else 0
            math_score = qmath_maths[mt] if mt in qmath_maths else 0
            all_maths[mt] = alpha * text_score + (1-alpha) * math_score
        return all_maths

    def askSolr_all(self, query, mathencode, alpha):
        '''
            alpha: weight for text-related fields
        '''
        qall = Query_All(self.solr_url_math, self.n_row)
        qtext = self.__constructSolrQuery_words(query)
        qmath = self.__constructSolrQuery_math(query, mathencode)[0]
        qtext_maths, qtext_docs = qall.ask_solr_doc(qtext)
        qmath_maths, qmath_docs = qall.ask_solr_doc(qmath)
        qtext_maths = dict(qtext_maths)
        qmath_maths = dict(qmath_maths)
        all_maths = OrderedDict.fromkeys(qtext_maths.keys() + qmath_maths.keys())
        for gmid in all_maths.keys():
            qtext_score = qtext_maths[gmid] if gmid in qtext_maths else qall.ask_solr_math_score(qtext, gmid)
            qmath_score = qmath_maths[gmid] if gmid in qmath_maths else qall.ask_solr_math_score(qmath, gmid)
            all_maths[gmid] = alpha * qtext_score + (1-alpha) * qmath_score
        all_docs = OrderedDict()
        for gmid, score in sorted(all_maths.iteritems(), key=operator.itemgetter(1), reverse=True):
            gpid = gmid[:gmid.index('#')]
            all_docs[gpid] = None
            if len(all_docs) >= self.n_row: break
        return all_docs.keys()

    def askSolr_rerank(self, query, mathencode, alpha, beta, op='max'):
        '''
            alpha: weight of text
            beta: weight of doc/para
        '''
        qrerank = Query_Rerank(self.solr_url_para, self.solr_url_math, self.n_row)
        qtext = self.__constructSolrQuery_para_words(query)
        qtext_for_math = self.__constructSolrQuery_words(query)
        qmath = self.__constructSolrQuery_math(query, mathencode)[0]
        qtext_docs = qrerank.ask_solr_doc(qtext)
        qmath_docs = qrerank.ask_solr_doc(qmath)
        qtext_docs = dict(qtext_docs)
        qmath_docs = dict(qmath_docs)
        all_docs = OrderedDict.fromkeys(qtext_docs.keys() + qmath_docs.keys())
        #iterate to insert text score
        for gpid in all_docs.keys():
            qtext_doc_score = qtext_docs[gpid] if gpid in qtext_docs else qrerank.ask_solr_doc_score(qtext, gpid)
            qmath_doc_score = qmath_docs[gpid] if gpid in qmath_docs else qrerank.ask_solr_doc_score(qmath, gpid)
            qdoc_score = alpha * qtext_doc_score + (1-alpha) * qmath_doc_score

            qtext_maths, qtext_maxscore = qrerank.ask_solr_math_score(qtext_for_math, gpid)
            qmath_maths, qmath_maxscore = qrerank.ask_solr_math_score(qmath, gpid)
            all_maths = self.__combine_textscore_mathscore(qtext_maths, qmath_maths, qtext_maxscore, qmath_maxscore, alpha)
            qmath_score = 0.
            if op == 'max': qmath_score = self.__summarize_score_max(all_maths)
            elif op == 'geomMean': qmath_score = self.__summarize_score_geometric_mean(all_maths)
            elif op == 'mean': qmath_score = self.__summarize_score_mean(all_maths)
            all_docs[gpid] = beta * qdoc_score + (1-beta) * qmath_score
        return OrderedDict(sorted(all_docs.iteritems(), key = operator.itemgetter(1), reverse=True)).keys()
