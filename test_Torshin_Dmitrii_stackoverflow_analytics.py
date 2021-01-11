"""tests"""
import pytest
from task_Torshin_Dmitrii_stackoverflow_analytics import *
import json


SMALL_STACKOVERFLOW_DATA = 'stackoverflow_10_posts.xml'
TEST_QUERY = 'test_query.csv'


def test_setup_logger():
    """test for logger"""
    try:
        logger = setup_logger()
    except Exception as e:
        pytest.fail("Something from with log config")


def test_make_scorer():
    """test scorer"""
    with open(SMALL_STACKOVERFLOW_DATA, 'r', encoding = 'utf-8') as fin:
        scorer = make_scorer(fin)
        assert 2008 in scorer.keys()
        assert 'setting' in scorer[2008]
        assert 'and' in scorer[2008]


def test_fix_scorer():
    """remove stop words"""
    with open(SMALL_STACKOVERFLOW_DATA, 'r', encoding = 'utf-8') as fin:
        with open(DEFAULT_STOP_WORDS_PATH, 'r', encoding = 'koi8-r') as stop_words:
            scorer = make_scorer(fin)
            scorer = fix_scorer(scorer, stop_words)
            assert 'setting' in scorer[2008]
            assert 'and' not in scorer[2008]


def test_get_top():
    """test get top"""
    with open(SMALL_STACKOVERFLOW_DATA, 'r', encoding = 'utf-8') as fin:
        with open(DEFAULT_STOP_WORDS_PATH, 'r', encoding = 'koi8-r') as stop_words:
            scorer = make_scorer(fin)
            scorer = fix_scorer(scorer, stop_words)
            assert get_top(2008, 2008, scorer)['style'] == 5
            assert len(get_top(2009, 2009, scorer)) == 0


def test_range_scorer():
    """test range scorer"""
    with open(SMALL_STACKOVERFLOW_DATA, 'r', encoding = 'utf-8') as fin:
        with open(DEFAULT_STOP_WORDS_PATH, 'r', encoding = 'koi8-r') as stop_words:
            scorer = make_scorer(fin)
            scorer = fix_scorer(scorer, stop_words)
            assert range_scorer(scorer)[0][(2008, 2008)]['style'] == 5


def test_process_query():
    """test simgle query"""
    with open(SMALL_STACKOVERFLOW_DATA, 'r', encoding = 'utf-8') as fin:
        with open(DEFAULT_STOP_WORDS_PATH, 'r', encoding = 'koi8-r') as stop_words:
            scorer = make_scorer(fin)
            scorer = fix_scorer(scorer, stop_words)
            query = {
                'start_year': 2008,
                'end_year': 2009,
                'top_N': 1
            }
            a, b, c = range_scorer(scorer)
            assert 'setting' == process_query(query, a, b, c)[0][0]


def test_convert_to_json():
    line = {
        'start_year': '2008',
        'end_year': '2008',
        'top_N': '1'
    }
    result = [('a', 2), ('b', 1)]
    assert json.loads(convert_to_json(line, result))['top'][0][0] == 'a'


def test_process_queries():
    with open(DEFAULT_DATASET_PATH, 'r', encoding = 'utf-8') as fin:
        with open(DEFAULT_STOP_WORDS_PATH, 'r', encoding = 'koi8-r') as stop_words:
            res = [
                '{"start": 2007, "end": 2007, "top": []}',
                '{"start": 2008, "end": 2008, "top": [["file", 177]]}',
                '{"start": 2008, "end": 2008, "top": [["file", 177], ["batch", 164], ["create", 164], '
                '["text", 164], ["c", 74]]}',
                '{"start": 2009, "end": 2010, "top": []}',
                '{"start": 2008, "end": 2010,'
                ' "top": [["file", 177], ["batch", 164], ["create", 164], ["text", 164], ["c", 74]]}',
                '{"start": 2009, "end": 2009, "top": []}',
            ]
            assert res == process_queries(fin, stop_words, TEST_QUERY)
