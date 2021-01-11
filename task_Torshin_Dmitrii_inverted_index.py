#!usr/bin/env python3

from collections import defaultdict
# from storage_policy import JsonStoragePolicy, PickleStoragePolicy, ZlibStoragePolicy
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType
from io import TextIOWrapper
import sys
from argparse import ArgumentTypeError
import struct

DEFAULT_DATASET_PATH = '../resourses/wikipedia.sample'
DEFAULT_INVERTED_INDEX_STORE_PATH = 'inverted.index'
SPLIT = chr(500000).encode('utf-8')


class StoragePolicy:
    @staticmethod
    def dump(word_to_docs_mapping, filepath: str):
        print(f'dump dataset to {filepath}', file=sys.stderr)
        with open(filepath, 'wb') as f:
            for key in word_to_docs_mapping.keys():
                f.write(key.encode('utf-8') + SPLIT)
                for val in word_to_docs_mapping[key]:
                    f.write(struct.pack('H', val))
                f.write(SPLIT)

    @staticmethod
    def load(filepath: str):
        data = defaultdict(list)
        print(f'load dataset from {filepath}', file=sys.stderr)
        with open(filepath, 'rb') as f:
            s = f.read()
            for index, v in enumerate(s.split(SPLIT)):
                if index % 2 == 0:
                    key = v.decode('utf-8')
                else:
                    value = struct.unpack('H'*(len(v)//2), v)
                    data[key] = list(value)
        return data


class EncodedFileType(FileType):
    def __call__(self, string):
        # the special argument "-" means sys.std{in,out}
        if string == '-':
            if 'r' in self._mode:
                stdin = TextIOWrapper(sys.stdin.buffer, encoding = self._encoding)
                return stdin
            elif 'w' in self._mode:
                stdout = TextIOWrapper(sys.stdout.buffer, encoding = self._encoding)
                return stdout
            else:
                msg = 'argument "-" with mode %r' % self._mode
                raise ArgumentTypeError(msg)

        # all other arguments are used as file names
        try:
            return open(string, self._mode, self._bufsize, self._encoding,
                        self._errors)
        except OSError as e:
            message = "can't open '%s': %s"
            raise ArgumentTypeError(message % (string, e))


class InvertedIndex:
    def __init__(self):
        """Конструктор"""
        self.inverted_index = defaultdict(list)

    def query(self, words: list) -> list:
        """Return the list of relevant documents for the given query"""
        print(f'run query', file=sys.stderr)
        return list(set.intersection(*[set(self.inverted_index[word]) for word in words.split()]))

    def dump(self, filepath: str, storage_policy):
        storage_policy.dump(self.inverted_index, filepath)

    @classmethod
    def load(cls, filepath: str, storage_policy):
        inverted_index = cls()
        inverted_index.inverted_index = storage_policy.load(filepath)
        return inverted_index


def load_documents(filepath: str):
    with open(filepath, 'r') as f:
        return f.readlines()


def build_inverted_index(documents):  
    inverted_index = InvertedIndex()
    for document in documents:
        words = document.split()
        index = int(words[0])
        words = words[1:]
        for word in words:
            if ((len(inverted_index.inverted_index[word]) == 0) or (
                inverted_index.inverted_index[word][-1] != index)):
                inverted_index.inverted_index[word].append(index)
    return inverted_index


def setup_parser(parser):
    subparsers = parser.add_subparsers(help='choose command')

    build_parser = subparsers.add_parser(
        "build", help="build inverted index in binary forman into hard drive",
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    build_parser.add_argument(
        "-d", "--dataset", default = DEFAULT_DATASET_PATH,
        dest = 'dataset_filepath',
        help = 'path to datased to load, default path is %(default)s',
    )
    build_parser.add_argument(
        "-o", "--output", default = DEFAULT_INVERTED_INDEX_STORE_PATH,
        dest = 'inverted_index_filepath',
        help = 'path to store index in binary format',
    )
    build_parser.set_defaults(callback = build_callback)

    query_parser = subparsers.add_parser(
        "query", help = 'query inverted index',
        formatter_class = ArgumentDefaultsHelpFormatter,
    )
    query_parser.add_argument(
        '-i', '--index', default = DEFAULT_INVERTED_INDEX_STORE_PATH,
        dest = "inverted_index_filepath",
        help = 'path to read index in binary format',
    )
    query_file_group = query_parser.add_mutually_exclusive_group(required=True)
    query_file_group.add_argument(
        '-q', '--query',
        dest = 'query_file',
        nargs = "+",
        metavar = 'WORD',
        help = 'query to run against inverted index',
    )
    query_file_group.add_argument(
        '--query-file-utf8',
        dest = 'query_file',
        default = TextIOWrapper(sys.stdin.buffer, encoding = "utf-8"),
        type = EncodedFileType("r", encoding = 'utf-8'),
        help = 'query file to get queries to run against inverted index',
    )
    query_file_group.add_argument(
        '--query-file-cp1251',
        dest = 'query_file',
        default = TextIOWrapper(sys.stdin.buffer, encoding = "cp1251"),
        type = EncodedFileType("r", encoding = 'cp1251'),
        help = 'query file to get queries to run against inverted index',
    )
    query_parser.set_defaults(callback = query_callback)


def build_callback(arguments):
    return process_build(arguments.dataset_filepath,
        arguments.inverted_index_filepath)


def process_build(dataset, output):
    documents = load_documents(dataset)
    inverted_index = build_inverted_index(documents)
    inverted_index.dump(filepath = output, 
                        storage_policy = StoragePolicy)


def query_callback(arguments):
    return process_queries(arguments.inverted_index_filepath,
        arguments.query_file)

def process_queries(inverted_index_filepath, query_file):
    print(f"load inverted index from : {inverted_index_filepath}", 
        file = sys.stderr)
    inverted_index = InvertedIndex().load(
        inverted_index_filepath, StoragePolicy)
    print(f"read queries from: {query_file}", file = sys.stderr)
    for query in query_file: 
        query = query.strip()
        document_ids = inverted_index.query(query)
        document_ids = list(map(str, document_ids))
        print(",".join(document_ids))


def main():   
    parser = ArgumentParser(
        prog='inverted-index',
        description="tool to biuld, dump, load and query inverted index",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    setup_parser(parser)
    arguments = parser.parse_args()
    arguments.callback(arguments)


if __name__ == "__main__":
    main()