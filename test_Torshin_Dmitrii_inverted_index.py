from argparse import Namespace

import pytest

from task_Torshin_Dmitrii_inverted_index import *


def test_process_queries(capsys):
    with open ("test_queries.txt") as fin:
        process_queries(
            inverted_index_filepath = DEFAULT_INVERTED_INDEX_STORE_PATH, 
            query_file = fin,
        )
        captured = capsys.readouterr()
        assert "load inverted index" not in captured.out
        assert "load inverted index" in captured.err
        assert "1894,6343,586,2162,4149,4702" in captured.out


def _test_callback_query():
    with open ("test_queries.txt") as fin:
        query_arguments = Namespace(
            inverted_index_filepath = DEFAULT_INVERTED_INDEX_STORE_PATH, 
            query_file = fin,
        )
        query_callback(query_arguments)
 

@pytest.mark.parametrize(
    "documents,expected",
    [(['1  a   b', '2 c    d a'], 
    {'a': [1, 2], 'b': [1], 'c': [2], 'd': [2]})],
)
def test_build_inverted_index(documents, expected):
    assert build_inverted_index(documents).inverted_index == expected


@pytest.mark.parametrize(
    "inverted_index_",
    [{'a': [1, 2], 'b': [1], 'c': [2], 'd': [2]},
    {'a': [1, 2, 4], 'b': [2], 'c': [3], 'd': [1]}],
)
def test_dump_load(inverted_index_):
    ii = InvertedIndex()
    ii.inverted_index = inverted_index_
    ii.dump('tmp', StoragePolicy)
    ii = InvertedIndex.load('tmp', StoragePolicy)
    assert inverted_index_ == ii.inverted_index


@pytest.mark.parametrize(
    "inverted_index_,query,answer",
    [({'a': [1, 2], 'b': [1], 'c': [2], 'd': [2]}, ['a', 'c'], [2]),
    ({'a': [1, 2, 4], 'b': [2], 'c': [3], 'd': [1]}, ['a', 'c'], [])],
)
def test_query(inverted_index_, query, answer):
    ii = InvertedIndex()
    ii.inverted_index = inverted_index_
    assert ii.query(query) == answer