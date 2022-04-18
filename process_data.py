from features import User, extract_tag_corpus
from loader import load_data
from lib.progress_counter import ProgressCounter, human_readable


# def report(*args):
#     print("\033c", end="")
#     print("Loading data... (this will take a while!)")
#     print(f"> Loaded {human_readable(num_users.count)} users")
#     print(f"> Loaded {human_readable(num_posts.count)} initial posts")


# num_users = ProgressCounter(report)
# num_posts = ProgressCounter(report)
# num_answers = ProgressCounter(report)

# users = []
# for raw_data in load_data():
#     u = User(raw_data)

#     num_users.increment()
#     num_posts.increment(u.NumInitialPosts)

#     users.append(u)

# report()
# print("Done!")
# print("")
# print("Top 10 tags:")
# for tag in extract_tag_corpus(users)[:10]:
#     print(tag)

users = []
for i, raw_data in enumerate(load_data()):
    u = User(raw_data)
    if u.AvgEditorRep != None:
        print(i, u.AvgEditorRep)
        break
    # users.append(User(raw_data))
    # if i > 10000:
    #     break

# for tag in extract_tag_corpus(users)[:10]:
    # print(tag)


# Look for retention rate differences across tags
# - tag_counts = [2, 0, 1, ...] (be sure to apply regularization!)
#     - Train model to predict retention - compare w vs w/o tags
# - ANOVA: each tag is a different condition

# Post body
# - n-gram features associated with retention
#     - from both op and
#     - answerers
