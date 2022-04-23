'''
# SUMMARY

## Variables

CVs: Any features about the user or their posts

>    Why? We want to isolate the effects of community 
>    response on retention. We're NOT trying to answer
>    "how should newcomers post", were trying to answer
>    "how should the community react".

IVs: Any features derived from community response

 DV: Retention

## Model

2-class logistic regression with balanced class weights (i.e., we
place a higher cost on incorrectly predicting a newcomer is 
NOT retained)
'''


import os
import re
from typing import Sequence
import numpy as np
import pandas as pd
from features import User
from loader import UserDict, load_data
from lib.progress_counter import ProgressCounter, human_readable
from lib.utils import tcols, log_odds
from statsmodels.api import Logit, add_constant


def user_to_vec(user_dict: UserDict):
    '''
    Converts user data into a vector for analysis. Some 
    features may be None if that feature does not apply 
    to this user
    '''

    user = User(user_dict)

    return {
        #######
        # CVs #
        #######

        "age_at_first_post": user.f_age_at_first_post,
        "num_init_posts": user.f_num_init_posts,
        "prop_qs": user.f_prop_qs,
        "avg_init_post_len": user.f_avg_init_post_len,
        # avg. readability?
        # other text features?

        #######
        # IVs #
        #######

        "prop_edited": user.f_prop_edited,
        "avg_rep_editors": user.f_avg_rep_editors,
        "avg_age_editors": user.f_avg_age_editors,

        "prop_answered": user.f_prop_answered,
        "avg_rep_top_answerers": user.f_avg_rep_top_answerers,
        "avg_age_top_answerers": user.f_avg_age_top_answerers,

        "prop_upvoted": user.f_prop_upvoted,
        "prop_downvoted": user.f_prop_downvotes,

        "prop_accepted": user.f_prop_accepted,

        ######
        # DV #
        ######

        "retention": user.f_retention,
    }


def vectorize(user_data: Sequence[UserDict], verbose=True):
    '''
    Convert the user data into an array, with each row representing
    the feature vector for a single user, replacing any columns that 
    are not applicable/invalid for that user with nan
    '''

    if verbose:
        print('Vectorizing data...')
        pc = ProgressCounter(lambda i: print(
            f'> Vectorized {human_readable(i)} data points so far'.ljust(tcols()), end='\r'))

        data = []
        for u in user_data:
            data.append(user_to_vec(u))
            pc.increment()

        print(f'> Done! Vectorized {pc.count} data points!'.ljust(tcols()))
    else:
        data = [user_to_vec(u) for u in user_data]

    return pd.DataFrame(data, dtype=float)


def prepare_dataset(filename="cache/vectorized_dataset2.csv", force_recompute=False, verbose=True) -> pd.DataFrame:
    '''
    Loads vectorized dataset from specified file (if exists), or
    computes the dataset and writes it to the specified file
    '''

    if os.path.exists(filename) and not force_recompute:
        if verbose:
            print(f'Loading dataset from {filename}...')

        dataset = pd.read_csv(filename)

        if verbose:
            print(f'> Done! Loaded {dataset.shape[0]} data points!')
    else:
        dataset = vectorize(load_data(), verbose=verbose)

        if verbose:
            print(f'Saving vectorized dataset to {filename}...')

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        dataset.to_csv(filename, index=False)

        if verbose:
            print(f'> Done!')

    return dataset


def select_columns(data: pd.DataFrame, columns: Sequence[str]):
    '''
    Selects only the specified columns from the array and omits
    any rows with invalid (nan) values
    '''

    return data[list(columns)].dropna()


def union_cols(*cols_seq: Sequence[tuple[str]]) -> tuple[str]:
    ''' 
    Utility function for combining sets of columns (see usage below)
    '''
    return tuple(sorted(set(col for cols in cols_seq for col in cols), key=lambda col: F_ALL.index(col)))


F_ALL = (
    "age_at_first_post",
    "num_init_posts",
    "prop_qs",
    "avg_init_post_len",

    "prop_edited",
    "avg_rep_editors",
    "avg_age_editors",
    "prop_answered",
    "avg_rep_top_answerers",
    "avg_age_top_answerers",
    "prop_upvoted",
    "prop_downvoted",
    "prop_accepted",

    "retention",
)
'''
All feature names
'''


F_BASIC = (
    "age_at_first_post",
    "num_init_posts",
    "prop_qs",
    "avg_init_post_len",

    "prop_edited",
    "prop_upvoted",
    "prop_downvoted",

    "retention",
)
'''
Names of basic input features gauranteed to be 
applicable to all users 
'''


F_EDITED = union_cols(F_BASIC, (
    "avg_rep_editors",
    "avg_age_editors",
))
'''
Names of features that are guaranteed to be 
applicable to all users that have received at least 
one edit
'''


F_ASKER = union_cols(F_BASIC, ("prop_answered",))
'''
Names of features that care guaranteed to be 
applicable to all users that have posted at least 
one question
'''


F_ANSWERED = union_cols(F_ASKER, (
    "avg_rep_top_answerers",
    "avg_age_top_answerers"
))
'''
Names of features that care guaranteed to be present
on all users that have posted at least one question and 
received at least one answer
'''


F_ANSWERER = union_cols(F_BASIC, ("prop_accepted",))
'''
Names of features that are guaranteed to be present
on all users that have posted at least one answer
'''


def analyze_subset(dataset: np.ndarray, cols: tuple[int]):
    sub = select_columns(dataset, cols)

    # Step 1: Balance classes
    m = min((sub["retention"] == 0).sum(), (sub["retention"] == 1).sum())
    c0 = sub.loc[sub['retention'] == 0].sample(m)
    c1 = sub.loc[sub['retention'] == 1].sample(m)
    sample = pd.concat([c0, c1])

    # Step 2: Prepare x and y
    X = sample.drop(columns=["retention"])
    y = sample[["retention"]]

    # Step 3: Create logistic regression model
    model = Logit(y, add_constant(X)).fit(disp=False)

    # Step 4: Report
    summary = str(model.summary())
    summary = to_csv(summary)
    summary = '\n'.join(summary.split('\n')[2:])
    print(summary)

    # print("\n" + " "*30 + "Log Odds")
    summary2 = str(log_odds(model))
    print(to_csv(summary2))


def to_csv(summary):
    summary = re.sub(r",", "\,", summary)
    summary = re.sub(r"  +", ",", summary)
    summary = re.sub(r"(^|[^\\],)(.*?\\,.*?[^\\])(,|$)",
                     "\g<1>\"\g<2>\"\g<3>", summary)
    summary = re.sub(r"\\,", ",", summary)
    summary = re.sub(r"==+|--+\n|:", "", summary)
    return summary


def analyze_all():
    dataset = prepare_dataset(verbose=True)

    # Step 1: Normalize all columns by mean/stddev
    normed_dataset = (dataset - dataset.mean(skipna=True)) / dataset.std()

    # Restore retention values to 0, 1
    normed_dataset[["retention"]] = dataset[["retention"]]

    # Step 2: Analyze subsets of features
    print('BASIC\n')
    analyze_subset(normed_dataset, F_BASIC)
    print('\nEDITED\n')
    analyze_subset(normed_dataset, F_EDITED)
    print('\nASKER\n')
    analyze_subset(normed_dataset, F_ASKER)
    print('\nANSWERED\n')
    analyze_subset(normed_dataset, F_ANSWERED)
    print('\nANSWERER\n')
    analyze_subset(normed_dataset, F_ANSWERER)

    print()
    print('MEAN\n')
    print(to_csv(str(dataset.mean())))
    print('\nSTD\n')
    print(to_csv(str(dataset.std())))


if __name__ == "__main__":
    analyze_all()
