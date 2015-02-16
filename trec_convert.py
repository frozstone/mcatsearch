from pickle import load
from os import listdir, path

dump_location = 'dump_scenario3'
trec_location = 'result_submit'

def open_scenario_dict(flpath):
    f = open(flpath, 'rb')
    scenario = load(f)
    f.close()
    return scenario

def write_lines_to_files(lines, flpath):
    f = open(flpath, 'w')
    f.writelines(lines)
    f.close()

def trec_format(results, scenario_name, math_encode):
    '''
        results: dictionary of query and retreived paragraphs
    '''
    lines = []
    for query, encodes in results.iteritems():
        for encode, paragraphs in encodes.iteritems():
            if encode != math_encode: continue
            for rank, paragraph in enumerate(paragraphs):
                print paragraph
                paragraph_basename = paragraph[paragraph.rindex('/') + 1:]
                paragraph_basename = paragraph_basename.replace('.xhtml', '')
                lines.append('\t'.join([query, '1', paragraph_basename, str(rank + 1), str(1./(rank+1)), '%s_%s' % (scenario_name, math_encode)]) + '\n')
    return lines

if __name__ == '__main__':
    for scenario_fl in listdir(dump_location):
        scenario = open_scenario_dict(path.join(dump_location, scenario_fl))
        for math_encode in ['pathpres', 'pathcont', 'hashpres', 'hashcont']:
            lines = trec_format(scenario, scenario_fl, math_encode)
            write_lines_to_files(lines, path.join(trec_location, '%s_%s' % (math_encode, scenario_fl)))
