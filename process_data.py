from features import User, extract_tag_corpus
from loader import load_data
from lib.progress_counter import ProgressCounter, human_readable


def report(*args):
    print("\033c", end="")
    print("Loading data... (this will take a while!)")
    print(f"> Loaded {human_readable(num_users.count)} users")
    print(f"> Loaded {human_readable(num_posts.count)} initial posts")
    print(
        f"> Loaded {human_readable(num_answers.count)} answers to initial posts")


num_users = ProgressCounter(report)
num_posts = ProgressCounter(report)
num_answers = ProgressCounter(report)

users = []
for raw_data in load_data():
    u = User(raw_data)
    num_users.increment()
    num_posts.increment(u.NumInitialPosts)
    num_answers.increment(len(u.get_answers_by_others()))

    users.append(u)

report()
print("Done!")
print("")
print("Top 10 tags:")
for tag in extract_tag_corpus(users)[:10]:
    print(tag)
