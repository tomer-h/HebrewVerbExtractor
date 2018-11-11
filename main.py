import unicodecsv as csv
import argparse
import subprocess
import xml.etree.ElementTree as ET


EMPTY = 'empty_box'


def create_analysis_template(input_file, analysis_file):
    """
    Gets the CSV input and prepares the necessary XML for analysis
    :param input_file: input csv file
    :param analysis_file: created file for analysis
    :return: None
    """
    print 'Creating analysis template for input to Morphological Analyzer...'
    with open(input_file, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        paragraph_placeholder = ET.Element('paragraph')
        paragraph_placeholder.set('id', '1')
        sentence_counter = 1
        for row in csv_reader:
            analyze_list = row[1].split()

            if not analyze_list:
                analyze_list.append(EMPTY)
                continue

            sentence_placeholder = ET.SubElement(paragraph_placeholder, 'sentence')
            sentence_placeholder.set('id', str(sentence_counter))
            sentence_counter += 1
            word_counter = 1
            for word in analyze_list:
                word_element = ET.SubElement(sentence_placeholder, 'token')
                word_element.set('id', str(word_counter))
                word_element.set('surface', word)
                word_counter += 1

        ET.ElementTree(paragraph_placeholder).write(analysis_file, encoding='UTF-8')
    print 'Creating analysis template complete...'


def run_morphological_analysis(path, analysis_file, output_file):
    """
    Run the morphological analyzer java program in a subprocess, writing results to output file
    :param path: path to jar in filesystem
    :param analysis_file: xml input file, created by create_analysis_template
    :param output_file: xml output file for parsing
    :return: None
    """
    print 'Running Morphological analyzer...'
    subprocess.call(['java', '-jar', path, 'false', analysis_file, output_file])
    print 'Morphological analysis is complete'


def parse_output_file(output_file, output_csv):
    """
    MAIN IO LOOP
    Parse the output XML, recursively iterate through every sentence and build the necessary word analysis blocks
    Create verb and participle lists
    Writes everything to CSV file dynamically, avoiding pythonic data structures to preserve encoding
    Everything is UTF-8, but is a pain in the ass once placed in a list or dict
    :param output_file: xml output file created in run_morphological_analysis
    :param output_csv: csv file created, containing analysis, ready for upload to google sheets
    """
    print 'Parsing output XML file and writing to output CSV'
    parsed_output = ET.parse(output_file)
    iterable_parsed_output = parsed_output.getroot()
    with open(output_csv, 'a') as output_csv:
        verbwriter = csv.writer(output_csv, encoding='utf-8')
        for article in iterable_parsed_output:
            for paragraph in article.findall('paragraph'):
                for sentence in paragraph.findall('sentence'):
                    sentence_key = sentence.get('id')
                    full_sentence = []
                    analyzed_verbs = []
                    analyzed_participles = []
                    for word in sentence.findall('token'):
                        analyzed_word = word.get('surface')
                        full_sentence.append(analyzed_word)
                        for analyses in word.findall('analysis'):
                            analysis_id = analyses.get('id')
                            for base in analyses.findall('base'):
                                for verbs in base.findall('verb'):

                                    binyan = verbs.get('binyan')
                                    gender = verbs.get('gender')
                                    root = verbs.get('root')
                                    verb_string = '%s %s %s %s %s' % \
                                                (analysis_id, analyzed_word, root, binyan, gender)
                                    analyzed_verbs.append(verb_string)

                                for participles in base.findall('participle'):
                                    binyan = participles.get('binyan')
                                    gender = participles.get('gender')
                                    root = participles.get('root')
                                    participle_string = '%s %s %s %s %s' % \
                                                (analysis_id, analyzed_word, root, binyan, gender)
                                    analyzed_participles.append(participle_string)
                    verbwriter.writerow(['sentence_id', 'full_sentence'])
                    verbwriter.writerow([sentence_key, ' '.join(full_sentence)])
                    if analyzed_verbs or analyzed_participles:
                        verbwriter.writerow(['analysis_id', 'analyzed_word', 'root', 'binyan', 'gender'])
                    for verb in analyzed_verbs:
                        verbwriter.writerow(verb.split())
                    for participle in analyzed_participles:
                        verbwriter.writerow(participle.split())
    print 'OUTPUT CSV IS COMPLETE!...'


def main():
    """Get command line params if necessary, then run main loop"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", help='input csv file')
    parser.add_argument("-m", "--morph_path", help='path to morphological analyzer')
    parser.add_argument("-a", "--analysis_xml", help='morphological analyzer input xml filename')
    parser.add_argument("-o", "--output_xml", help='morphological analyzer output xml filename')
    parser.add_argument("-c", "--csv_output", help='final output csv filename')
    args = parser.parse_args()
    create_analysis_template(input_file=args.input_file, analysis_file=args.analysis_xml)
    run_morphological_analysis(path=args.morph_path, analysis_file=args.analysis_xml, output_file=args.output_xml)
    parse_output_file(output_file=args.output_xml, output_csv=args.csv_output)


if __name__ == '__main__':
    main()

