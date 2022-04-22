import os
import numpy as np

def tcols():
    '''
    Utility function to get the width of the terminal
    '''
    return os.get_terminal_size().columns

def log_odds(model, only_significant=False):
    odds = model.conf_int()
    odds['Odds Ratio'] = model.params
    odds.columns = ['5%', '95%', 'Odds Ratio']
    odds = np.exp(odds)
    odds['Significant'] = model.pvalues < 0.05

    if only_significant:
        odds = odds[odds['Significant'] == True]

    return odds