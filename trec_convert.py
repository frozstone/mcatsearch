from pickle import load
from os import listdir, path

dump_location = 'dump'
trec_location = 'result_submit'
judge_location = 'result_judge/NTCIR11_Math-qrels.dat'

#to create condensed list
def open_judge_file(flpath):
    lns = open(flpath).readlines()
    query_judge_para = {}
    for ln in lns:
        cells = ln.strip().split()
        qname = cells[0]
        paraname = cells[2]
        if qname not in query_judge_para:
            query_judge_para[qname] = []
        query_judge_para[qname].append(paraname)
    return query_judge_para

def open_scenario_dict(flpath):
    f = open(flpath, 'rb')
    scenario = load(f)
    f.close()
    return scenario

def write_lines_to_files(lines, flpath):
    f = open(flpath, 'w')
    f.writelines(lines)
    f.close()

def trec_format(results, scenario_name, math_encode, judged_para):
    '''
        results: dictionary of query and retreived paragraphs
    '''
    lines = []
    for query, encodes in results.iteritems():
        for encode, paragraphs in encodes.iteritems():
            if encode != math_encode: continue
            rank = 0
            for paragraph in paragraphs:
                print paragraph
                paragraph_basename = paragraph[paragraph.rindex('/') + 1:]
                paragraph_basename = paragraph_basename.replace('.xhtml', '')
                if paragraph_basename not in judged_para[query]: continue
                lines.append('\t'.join([query, '1', paragraph_basename, str(rank + 1), str(1./(rank+1)), '%s_%s' % (scenario_name, math_encode)]) + '\n')
                rank += 1
    return lines

if __name__ == '__main__':
    judged_para = open_judge_file(judge_location)
    for scenario_fl in listdir(dump_location):
        scenario = open_scenario_dict(path.join(dump_location, scenario_fl))
        for math_encode in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
            lines = trec_format(scenario, scenario_fl, math_encode, judged_para)
            write_lines_to_files(lines, path.join(trec_location, '%s_%s' % (math_encode, scenario_fl)))
