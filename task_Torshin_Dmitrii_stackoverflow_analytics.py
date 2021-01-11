#!/usr/bin/env python3
"""tool to get stackoverflow analytics"""
import sys
import logging
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType, ArgumentTypeError
from io import TextIOWrapper
from logging.config import dictConfig
from collections import defaultdict, Counter
import re
import csv
import json

import yaml
from lxml import etree

DEFAULT_DATASET_PATH = "stackoverflow_small_set.xml"
DEFAULT_STOP_WORDS_PATH = "stop_words_en.txt"
LOG_CONFIG_PATH = "log_config.yml"


class EncodedFileType(FileType):
    """Fix encoding for argument parser"""
    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding = self._encoding)
                return stdin
            if 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding = self._encoding)
                return stdout
            msg = 'argument "-" with mode %r' % self._mode
            raise ArgumentTypeError(msg)
        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as err:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (string, err))


def setup_parser(parser):
    """Parse parameters from terminal"""
    parser.add_argument(
        "--questions",
        required = True,
        default = DEFAULT_DATASET_PATH,
        type = EncodedFileType("r", encoding = "utf-8"),
        metavar = "FILE",
        dest = 'dataset_file',
        help = 'path to dataset to load, default path is %(default)s',
    )
    parser.add_argument(
        '--stop-words',
        required = True,
        dest = 'stop_words_file',
        default = DEFAULT_STOP_WORDS_PATH,
        type = EncodedFileType("r", encoding = "koi8-r"),
        metavar = "FILE",
        help = 'filepath to stop words',
    )
    parser.add_argument(
        '--queries',
        required = True,
        dest = 'query_file',
        metavar = "FILE",
        help = 'query to run against stackoverflow questions',
    )
    parser.set_defaults(callback = parser_callback)


def parser_callback(arguments):
    """get correct list of arguments"""
    return process_queries(arguments.dataset_file, arguments.stop_words_file, arguments.query_file)


def make_scorer(data_file):
    """count score for word in stackoverflow file"""
    scorer = defaultdict(lambda: defaultdict(int))
    for xml in data_file:
        xml = etree.fromstring(xml)
        if xml.get('PostTypeId') == '1':
            words = set(re.findall(r"\w+", xml.get('Title').lower()))
            year = int(xml.get('CreationDate')[:4])
            score = int(xml.get('Score'))
            for word in words:
                scorer[year][word] += score
    return scorer


def fix_scorer(scorer, stop_words_file):
    """remove stop words"""
    for line in stop_words_file:
        word = line.strip()
        for year in scorer:
            scorer[year].pop(word, None)
    return scorer


def get_top(year_start, year_end, scorer):
    """convert scorer into final for each year_start year_end"""
    res = Counter()
    for year in range(year_start, year_end + 1):
        res += Counter(scorer[int(year)])
    res = Counter(dict(sorted(res.items(), key=lambda kv: kv[0])))
    return res


def range_scorer(scorer):
    """iterate over years to create final scorer"""
    res = {}
    min_year = int(min(scorer.keys()))
    max_year = int(max(scorer.keys()))
    for year_start in range(min_year, max_year + 1):
        for year_end in range(year_start, max_year + 1):
            res[(year_start, year_end)] = get_top(year_start, year_end, scorer)
    return res, min_year, max_year


def process_query(query, scorer, min_year, max_year):
    """get result for single query"""
    min_year = max(int(query['start_year']), min_year)
    max_year = min(int(query['end_year']), max_year)
    if max_year < min_year:
        return []
    res = scorer[min_year, max_year].most_common(int(query['top_N']))
    return res


def convert_to_json(line, result):
    """convert result to json"""
    res = {
        'start': int(line['start_year']),
        'end': int(line['end_year']),
        'top': list(map(list, result))
    }
    res = json.dumps(res)
    return res


def process_queries(dataset_file, stop_words_file, query_file):
    """load data, process and show result"""
    logger = setup_logger()
    scorer = make_scorer(dataset_file)
    scorer = fix_scorer(scorer, stop_words_file)
    top_words, min_year, max_year = range_scorer(scorer)
    logger.info("process XML dataset, ready to serve queries")
    results = []
    with open(query_file, 'r') as query:
        reader = csv.reader(query, delimiter=',')
        for line in reader:
            new_line = {'start_year': line[0], 'end_year': line[1], 'top_N': line[2]}
            line = new_line
            logger.debug('got query "{},{},{}"'.format(line['start_year'],
                                                       line['end_year'], line['top_N']))
            result = process_query(line, top_words, min_year, max_year)
            if len(result) < int(line['top_N']):
                logger.warning('not enough data to answer, found {} words out '
                               'of {} for period "{},{}"'.format(
                    len(result), line['top_N'], line['start_year'], line['end_year']))
            results.append(convert_to_json(line, result))
    logger.info("finish processing queries")
    return results


def setup_logger():
    """read logger from config"""
    with open(LOG_CONFIG_PATH, 'r') as cfg:
        config = yaml.safe_load(cfg)
    dictConfig(config)
    return logging.getLogger("application_logger")


def main():
    """main - get list of arguments"""
    parser = ArgumentParser(
        formatter_class = ArgumentDefaultsHelpFormatter,
        description = "get most popular topics from stackoverflow",
        prog = "stackoverflow_analytics",
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    results = arguments.callback(arguments)
    for res in results:
        print(res)


if __name__ == "__main__":
    main()
