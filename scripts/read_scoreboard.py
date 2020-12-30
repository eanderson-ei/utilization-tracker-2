"""for one-time use to read in 2020 Scoreboard through Sept"""
"""column  names may not have periods in them"""

import pandas as pd

# path to workbook
f = 'data/2020 EI Monthly Scoreboard.xls'

# create dict of tab names and months
tabs = {'Jan 2020': ['Jan', '2020'],
        'Feb 2020': ['Feb', '2020'],
        'Mar 2020': ['Mar', '2020'],
        'April 2020': ['Apr', '2020'],
        'May 2020': ['May', '2020'],
        'June 2020': ['Jun', '2020'],
        'July 2020': ['Jul', '2020'],
        'Aug 2020': ['Aug', '2020'],
        'Sep 2020': ['Sep', '2020'],
        'October 2020': ['Oct', '2020'],
        'Nov 2020': ['Nov', '2020'],
        'Dec 2020': ['Dec', '2020']
        }

dfs = []
#TODO: deal with duplicate entries as columns
for tab in tabs:
    print('Processing: ' + tab)
    # read tab
    df = pd.read_excel(f, tab, header=18, usecols="B, G:AV")
    df.dropna(subset=['User Name'], inplace=True)
    df.dropna(how='all')
    
    # pivot
    df = pd.melt(df, id_vars=['User Name'],
                  var_name='Project', value_name='Hours')
    
    # drop empty hours
    df.dropna(subset=['Hours'], inplace=True)
    
    # correct for column duplicates
    df['Project'] = df['Project'].str.split('.').str[0]
    
    # drop unnamed columns
    filt = df['Project'].str.startswith('Unnamed')
    df = df.loc[~filt, :]
    
    # add month and year
    df['Entry Month'] = tabs.get(tab)[0]
    df['Entry Year'] = tabs.get(tab)[1]
    
    # sum duplicates
    df = df.groupby(['User Name',
                     'Entry Year',
                     'Entry Month',                     
                     'Project']).sum()                    
    
    # append to df list
    dfs.append(df)
    

# concat all tables
df = pd.concat(dfs)

# save output
df.to_csv('data/scoreboard.csv', index=True)