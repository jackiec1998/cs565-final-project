from itertools import islice
from features import Answer, User, tokenize_body
from loader import load_data
from nltk import ngrams, FreqDist

answers = (Answer(answer)
           for raw_data in load_data()
           for answer in User(raw_data).get_answers_by_others())

ngram_samples = [ngram for answer in islice(answers, 10000) for ngram in ngrams(
    tokenize_body(answer.Body), 3)]

fd = FreqDist(ngram_samples)
for ng, f in fd.most_common(10):
    print(f, ng)
