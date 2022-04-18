from typing import List
from loader import AnswerDict, PostDict, TagDict, UserDict
import re
from nltk.corpus import stopwords


class User:
    def __init__(self, user_dict: UserDict):
        self.raw_data = user_dict

    @property
    def Posts(self):
        return [Post(p) for p in self.raw_data["Posts"]]

    ##################################
    ### BACKWARD-COMPATIBLE FIELDS ###
    ##################################

    @property
    def AvgEditorRep(self):
        return maybe_avg([edit["EditorRep"]
                          for edit in self.get_edits()])

    @property
    def AvgTopAnswererRep(self):
        return maybe_avg([answer["AnswererRep"]
                          for answer in self.get_top_answers()])

    @property
    def AvgEditorAge(self):
        return maybe_avg([edit["EditorAge"]
                          for edit in self.get_edits()])

    @property
    def AvgTopAnswererAge(self):
        return maybe_avg([answer["AnswererAge"]
                          for answer in self.get_top_answers()])

    @property
    def TotalUpVotes(self):
        return len([vote
                    for vote in self.get_votes()
                    if vote["VoteType"] == "UpMod"])

    @property
    def TotalDownVotes(self):
        return len([vote
                    for vote in self.get_votes()
                    if vote["VoteType"] == "DownMod"])

    @property
    def NumInitialPosts(self):
        return len(self.raw_data["Posts"])

    @property
    def NumQuestions(self):
        return len([post
                    for post in self.raw_data["Posts"]
                    if post["PostType"] == "Question"])

    @property
    def NumAnswers(self):
        return len([post
                    for post in self.raw_data["Posts"]
                    if post["PostType"] == "Answer"])

    @property
    def TotalAnswersAccepted(self):
        return len([post
                    for post in self.raw_data["Posts"]
                    if post["PostType"] == "Answer"
                    and has_vote(post, "AcceptedByOriginator")])

    @property
    def TotalBookmarked(self):
        return len([post
                    for post in self.raw_data["Posts"]
                    if has_vote(post, "Bookmark")])

    @property
    def TotalClosed(self):
        return len([post
                    for post in self.raw_data["Posts"]
                    if has_vote(post, "Close")])

    @property
    def TotalSuggestedEdits(self):
        return len(self.get_edits())

    @property
    def AvgNumAnswers(self):
        return maybe_avg([len(post["Answers"])
                          for post in self.raw_data["Posts"]
                          if post["PostType"] == "Question" and "Answers" in post])

    @property
    def AvgViewCount(self):
        return maybe_avg([post["ViewCount"]
                          for post in self.raw_data["Posts"]
                          if "ViewCount" in post])

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def get_edits(self):
        return [edit
                for post in self.raw_data["Posts"] if "Edits" in post
                for edit in post["Edits"]]

    def get_top_answers(self):
        return [max(post["Answers"], key=lambda a: (a["IsAcceptedAnswer"], a["Score"]))
                for post in self.raw_data["Posts"]
                if "Answers" in post]

    def get_answers_by_others(self):
        return [answer
                for post in self.raw_data["Posts"]
                if "Answers" in post
                for answer in post["Answers"]]

    def get_votes(self):
        return [vote
                for post in self.raw_data["Posts"] if "Votes" in post
                for vote in post["Votes"]]

    def get_tags(self):
        return merge_tag_counts([post["Tags"]
                                 for post in self.raw_data["Posts"]
                                 if "Tags" in post])


class Post:
    def __init__(self, post_dict: PostDict):
        self.raw_data = post_dict

    @property
    def Body(self):
        return self.raw_data["Body"]

    @property
    def Answers(self):
        if self.raw_data["PostType"] != "Question":
            return None

        if "Answers" not in self.raw_data:
            return []

        return [Answer(answer) for answer in self.raw_data["Answers"]]


class Answer:
    def __init__(self, answer_dict: AnswerDict):
        self.raw_data = answer_dict

    @property
    def Body(self):
        return self.raw_data["Body"]

#############################
### MORE HELPER FUNCTIONS ###
#############################


def maybe_avg(vals: List[float]):
    '''
    Tries to compute the average of vals. Return None if vals is empty
    '''
    return sum(vals) / len(vals) if len(vals) > 0 else None


def has_vote(post: PostDict, vote_type: str):
    if "Votes" not in post:
        return False

    for vote in post["Votes"]:
        if vote["VoteType"] == vote_type:
            return True

    return False


def merge_tag_counts(tag_counts: List[List[TagDict]]) -> List[TagDict]:
    counter = dict()
    for tags in tag_counts:
        for tag in tags:
            tagname = tag["TagName"]
            if tagname not in counter:
                counter[tagname] = 0
            counter[tagname] += tag["Count"]

    return [{"TagName": tagname, "Count": count}
            for tagname, count in counter.items()]


def extract_tag_corpus(users: List[User]):
    corpus = merge_tag_counts([user.get_tags() for user in users])
    corpus.sort(key=lambda x: x["Count"], reverse=True)
    return corpus


def tokenize_body(body: str, remove_stopwords=True, remove_smallwords=True):
    # Make everything lowercase
    body = body.lower()

    # Collapse links into single token
    body = re.sub(r'\<a.*?\>.*?\</a\>', '<a>', body, flags=re.DOTALL)

    # Collapse code blocks into single token
    body = re.sub(r'\<code\>.*?\</code\>', '<code>', body, flags=re.DOTALL)

    # Remove ending tags
    body = re.sub(r'\</.*?\>', ' ', body)

    # Remove any unkown tags
    known_tags = {'a', 'code'}
    body = re.sub(r'\<(.*?)\>', lambda m: m.group(0)
                  if m.group(1) in known_tags else ' ', body)

    # Replace numbers with special token
    body = re.sub(r'[,.]?[0-9][0-9,.]*', '<num>', body)

    # Put space around special tokens
    body = re.sub(r'\<.*?\>', r' \g<0> ', body)

    # Remove escape sequences
    body = re.sub(r'&[a-z]+;', '', body)

    # Remove punctuation
    body = re.sub(r'[\'`"’‘]', '', body)

    # Remove remaining non-alphabetic chars
    body = re.sub(r'[^a-z\s<>]', ' ', body)

    tokens = body.split()

    if remove_stopwords:
        _stopwords = stopwords.words('english')
        tokens = [token for token in tokens if token not in _stopwords]

    if remove_smallwords:
        tokens = [token for token in tokens if len(token) >= 3]

    # Collapse identical consecutive tokens
    for i in range(1, len(tokens))[::-1]:
        if re.match(r'\<.*\>', tokens[i]) and tokens[i] == tokens[i - 1]:
            del tokens[i]

    return tokens
