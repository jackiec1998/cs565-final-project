import csv
from datetime import datetime
from glob import glob
from typing import List, Literal, TypedDict
from base64 import b64decode
from json import loads
from gzip import decompress
import os
import sys

DIR = os.path.dirname(os.path.realpath(__file__))


class VoteDict(TypedDict):
    VoteType: str
    Count: int


class EditDict(TypedDict):
    EditorId: int
    EditorRep: int
    EditorAge: int


class AnswerDict(TypedDict):
    AnswererId: int
    AnswererRep: int
    AnswererAge: int
    IsAcceptedAnswer: Literal[0] | Literal[1]
    Score: int


class TagDict:
    TagName: str
    Count: int


class PostDict(TypedDict, total=False):
    UserId: int
    PostId: int
    PostType: Literal["Answer"] | Literal["Question"]
    Body: str
    ViewCount: int
    Votes: List[VoteDict]
    Edits: List[EditDict]
    Answers: List[AnswerDict]
    Tags: List[TagDict]


class UserDict(TypedDict):
    UserId: int
    AccountCreationDate: datetime
    FirstPostDate: datetime
    NumFuturePosts: int
    Posts: List[PostDict]


def parse_row(row) -> UserDict:
    return {
        "UserId": int(row["UserId"]),
        "AccountCreationDate": datetime.fromisoformat(row["AccountCreationDate"]),
        "FirstPostDate": datetime.fromisoformat(row["FirstPostDate"]),
        "NumFuturePosts": int(row["NumFuturePosts"]),
        "Posts": loads(decompress(b64decode(row["PostsX"])))
    }


field_size_limit = sys.maxsize
while True:
    try:
        csv.field_size_limit(field_size_limit)
        break
    except OverflowError:
        field_size_limit //= 2


def load_data():
    user_ids = set()
    for filename in glob(os.path.join(DIR, 'raw_data/*')):
        with open(filename) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                user_id = row["UserId"]
                if user_id in user_ids:
                    continue

                user_ids.add(user_id)
                yield parse_row(row)
