from features import User, extract_tag_corpus
from loader import load_data
from lib.progress_counter import ProgressCounter, human_readable
from collections import defaultdict
import numpy as np
import pandas as pd
import researchpy as rp
import scipy.stats as stats
import plotly.graph_objects as go
import statsmodels.stats.multicomp as mc

users = []
# 30833 before merging, 29581, 7053
generic_tags = ['python', 'windows', 'latex', 'sql', 'c++', 'javascript', 'java', 'c#',
                'swift', 'php', 'ruby', 'powerpoint', 'selenium', 'lisp', 'haskell', 
                'perl', 'fortran', 'julia', 'matlab', 'rust', 'scheme', 'ocaml', 'curl',
                'wolfram', 'docker', 'bracket', 'tensorflow', 'keras', 'pandas', 'node.js',
                'html', 'css', 'google', 'apache', 'android', 'macos', 'json', 'facebook',
                'apple', 'django', 'flask', 'numpy', 'scipy', 'jupyter', 'scikit', 'excel',
                'ubuntu', 'github', 'git-', 'gitlab', 'powershell', 'amazon', 'photoshop', 'kotlin',
                'maven', 'adobe', 'azure', 'discord', 'xml', 'chromium', 'chrome', 'bootstrap',
                'twitter',
                # not sure about this one:
                'error', 'exception', 'spring', 'angular',
                'matplotlib', 'plotly', 'visual-studio', 'ios', 'gradle', 'mongo',
                'string', 'list'
               ]
# generic_tags = []
# each user should have a row for every tag, store user_id and num future posts in cols

data = []

for i, raw_data in enumerate(load_data()):
    user_tags = []
    u = User(raw_data)
    
    # For each tag on this user's posts, update variable
    # storing number of future posts
    for post in raw_data['Posts']:
        # Iterate over all tags
        for tag in post['Tags']:
            tag_name = tag['TagName'].lower()

            # Merge similar tags
            for opt in generic_tags:
                if opt in tag_name: 
                    tag_name = opt
                    break

            # If user data has already been recorded, skip
            if tag_name in user_tags: continue

            data.append([raw_data['UserId'], tag_name, u.NumFuturePosts])
            # Otherwise update data
            user_tags.append(tag_name)
    # if i > 500: break

df = pd.DataFrame(data, columns=['user_id', 'tag_name', 'num_future_posts'])

# Threshold for number of users that must use a tag for it to be considered
n = 10
top_tags = sorted(df['tag_name'].value_counts().head(n).index.tolist())
df = df.loc[df['tag_name'].isin(top_tags)]

summary = rp.summary_cont(df['num_future_posts'].groupby(df['tag_name'])).sort_values(by='tag_name', ascending=True).reset_index()


print(summary)
print('\n\n')

# make sure this gets ordered right
print('ANOVA results:')
tag_list = top_tags
print(stats.f_oneway(
               df['num_future_posts'][df['tag_name'] == tag_list[0]],
               df['num_future_posts'][df['tag_name'] == tag_list[1]],
               df['num_future_posts'][df['tag_name'] == tag_list[2]],
               df['num_future_posts'][df['tag_name'] == tag_list[3]],
               df['num_future_posts'][df['tag_name'] == tag_list[4]],
               df['num_future_posts'][df['tag_name'] == tag_list[5]],
               df['num_future_posts'][df['tag_name'] == tag_list[6]],
               df['num_future_posts'][df['tag_name'] == tag_list[7]],
               df['num_future_posts'][df['tag_name'] == tag_list[8]],
               df['num_future_posts'][df['tag_name'] == tag_list[9]]
            ))
print('\n\n')


summary = summary.loc[summary['tag_name'].isin(tag_list)]

# Figure might not make sense since tags are categorical
fig = go.Figure(data=go.Scatter(
        x=tag_list, #python javascript html
        y=summary['Mean'].tolist(),
        error_y=dict(
            type='data', # value of error bar given in data coordinates
            array=summary['95% Conf.'].tolist(),
            visible=True,
            # color='gray'
            )
    ))
fig.update_xaxes(type='category')
fig.update_layout(
    title='Interval Plot of Tag Name vs. Future Posts',
    xaxis_title='Tag',
    yaxis_title='Number of Future Posts',
)
fig.show()

# Filter out only relevant tags
df = df.loc[df['tag_name'].isin(tag_list)]
comp = mc.MultiComparison(df['num_future_posts'], df['tag_name'])
post_hoc_res = comp.tukeyhsd()
print(post_hoc_res.summary())

# Look for retention rate differences across tags
# - tag_counts = [2, 0, 1, ...] (be sure to apply regularization!)
#     - Train model to predict retention - compare w vs w/o tags
# - ANOVA: each tag is a different condition
#     - separate text by tag (dictionary {tag: [post, post, post]})
#     - find mean retention rates

# Post body
# - n-gram features associated with retention
#     - from both op and
#     - answerers
