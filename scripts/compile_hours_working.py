"""This script calculates utilization, r&d, g&a, and time off for each
individual. Calculated one by one. See compile_hours for attempt at group
calculation. Note that Deltek may have a report better suited for this."""

import pygsheets
import pandas as pd
import numpy as np
import datetime
import os
import sys

start = datetime.datetime.now()

# GLOBALS

# Download folder where hours report will be saved from Deltek
downloads = r'C:/Users/Erik/Downloads/'
# Name of the file, excluding any appended numeric distinguisher for repeats
file_name = 'Utilization Tabular'

# strategic year starts in April, semester 2 starts in November
sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']
year_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 
               'Oct', 'Nov', 'Dec']
semester1 = sem_months[:7]
semester2 = sem_months[7:]
month_index = np.arange(0,12)
sem_dict = dict(zip(sem_months, month_index))
month_dict = dict(zip(year_months, month_index))


# FUNCTIONS

def get_utilization_file(downloads, file_name):
    # list all files in downloads
    all_files = [f for f in os.listdir(downloads) if f.startswith(file_name)]
    # get save times
    file_versions = [os.path.getmtime(os.path.join(downloads, f)) for f in all_files]
    # access file with most recent save time
    latest_file = [f for f in all_files if os.path.getmtime(os.path.join(downloads, f)) == max(file_versions)]
    
    latest_file = os.path.join(downloads, latest_file[0])
    print(latest_file)
    
    return latest_file

        
# Authorize Google to access Utilization Project @
# https://drive.google.com/drive/folders/10J1e92bNZ-KF-X2CjedCleQf_dUWccJH?usp=sharing
# see here for instructions on setting up a Project 
# https://eanderson-ei.github.io/ei-dev/deployment/google-api/
def auth_gspread():
    """Authorize Google to access the Utilization Project"""
    # creds for local development
    try:
        client = pygsheets.authorize(
            service_file='secrets/gs_credentials.json'
            )
    # creds for heroku deployment
    except:
        client = pygsheets.authorize(
            service_account_env_var='GOOGLE_SHEETS_CREDS_JSON'
        )
        
    return client


def load_report(client, spreadsheet, sheet_title):
    """Load data (must be in tidy format) from sheet.
    Empty rows are dropped.
    :param client: client object for accessing google
    :param sheet: 0-indexed sheet number or sheet name
    :returns pandas dataframe
    """
    # load data from google sheet
    sh = client.open(spreadsheet)
    wks = sh.worksheet_by_title(sheet_title)
    data = wks.get_all_records(empty_value=None)  # get_as_df can't handle empty columns
    df = pd.DataFrame(data)
    df.dropna(axis=0, how='all', inplace=True)
    
    return df


def all_hours(client):
    """Combine Replicon and Cognos hours reports
    :param client: client object for accessing google
    :returns: dataframe of hours x person x day
    """
    # load 2019 hours
    df2019 = load_report(client, 'Utilization-Hours', 'hours-2019')
    
    # load 2020 apr - may hours
    df2020_1 = load_report(client, 'Utilization-Hours','apr-may-2020')

    # load jun 2020 + hours
    df2020_2 = load_report(client, 'Utilization-Hours','june-mar-2020')
    
    # union all 
    df = pd.concat([df2019, df2020_1, df2020_2])
    
    # create month and year convenience columns
    df['Entry Month'] = pd.DatetimeIndex(df['Hours Date']).strftime('%b')
    df['Entry Year'] = pd.DatetimeIndex(df['Hours Date']).strftime('%Y')
    
    # set dtypes
    df['Hours Date'] = pd.to_datetime(df['Hours Date'])
    df['Entered Hours'] = pd.to_numeric(df['Entered Hours'])
    df['Approved Hours'] = pd.to_numeric(df['Approved Hours'])
    df['Entry Year'] = pd.to_numeric(df['Entry Year'])
    
    # create user name column
    df['First Name'] = df['First Name'].str.strip()  # remove whitespace before Replicon first names
    df['Last Name'] = df['Last Name'].str.strip()
    df['User Name'] = df[['Last Name', 'First Name']].apply(
        lambda x: ', '.join(x), axis=1)
    
    # reclass unbillable to R&D
    df['Code'] = df['User Defined Code 3']
    filt = df['Project Name'].str.contains('Unbillable')
    df.loc[filt, 'Code'] = 'IRD'
    
    # reclass 'User Defined Code 3' to category
    codes_df = load_report(client, 'Utilization-Inputs', 'CODES')
    codes = dict(zip(codes_df['User Defined Code 3'], codes_df['Code']))
    df['Classification'] = df['Code'].replace(codes)
    
    # get employee work as dictionary
    emp_type = set(zip(df['User Name'], df['Work Schedule Description']))
    emp_type = dict(emp_type)
    
    # return
    return df, emp_type


def multiindex_pivot(df, columns=None, values=None):
    """https://github.com/pandas-dev/pandas/issues/23955"""
    names = list(df.index.names)
    df = df.reset_index()
    list_index = df[names].values
    tuples_index = [tuple(i) for i in list_index] # hashable
    df = df.assign(tuples_index=tuples_index)
    df = df.pivot(index="tuples_index", columns=columns, values=values)
    tuples_index = df.index  # reduced
    index = pd.MultiIndex.from_tuples(tuples_index, names=names)
    df.index = index
    return df


def idv_monthly_hours(hours_report, name):
    """aggregate hours per month for a single individual by Category"""
    # Subset by individual
    print(f'Processing {name}')
    df = hours_report.loc[hours_report['User Name']==name]
    if df.empty:
        print (f'Employee {name} not found')
        pass
    
    # get first day worked and last day worked
    first_day_worked = df['Hours Date'].min()
    # # account for forward-booking holidays
    # last_day_worked = df.loc[~df['Classification'].isin(['Time Off']), 
    #                          'Hours Date'].max()
    # last_day_holiday = df.loc[df['Classification'].isin(['Time Off']), 
    #                          'Hours Date'].max()
    last_day_worked = df['Hours Date'].max()
    if last_day_worked > datetime.datetime.today():
        last_day_worked = datetime.datetime.today().date()
    first_last = (first_day_worked, last_day_worked)
    
    # Calculate monthly total hours
    individual_hours = (
        df.groupby(['Entry Month', 'Entry Year', 'Classification'])
        .sum()
        .reset_index()
        .set_index(['Entry Year', 'Entry Month'])
    )
    
    idf = multiindex_pivot(individual_hours,
                           columns='Classification', 
                           values='Entered Hours')
    
    # fill na as 0
    idf.fillna(0, inplace=True)
    
    # # zero fill hours for remaining months
    # all_months = zip(idf['Entry Year'].unique(), sem_months))
    # print(df.index)
    # for month_idx in all_months:
    #     if month_idx not in idf.index:
    #         new_row = pd.Series([0]*len(year_df.columns), 
    #                             columns=idf.columns,
    #                             index=month_idx)
    #         print(new_row)
    #         idf = idf.append(new_row)
    
    # idf.reset_index(inplace=True)
    # # subset by year
    # for year in idf['Entry Year'].unique():
    #     filt = idf['Entry Year'] == year
    #     year_df = idf.loc[filt, :]
    #     # add row for month if missing
    #     existing_months = year_df['Entry Month'].to_list()
    #     for month in year_months:
    #         if month not in existing_months:
    #             new_row = pd.Series([year] + [month] 
    #                                 + [0]*(len(year_df.columns) - 2),
    #                                 idf.columns)
    #             idf = idf.append(new_row, ignore_index=True)
    
    # # TODO: make this more robust, hack knowing Jan, Feb, Mar are not in 2019 data
    # filt = (idf['Entry Year'] == 2019) & (idf['Entry Month'].isin(['Jan', 'Feb', 'Mar']))
    # idf.loc[filt, 'Entry Year'] = 2021
    
    # sort by month
    idf.reset_index(inplace=True)
    idf['month_id'] = idf['Entry Month'].replace(month_dict)
    idf.sort_values(by=['Entry Year', 'month_id'], inplace=True)
    idf.drop('month_id', axis=1, inplace=True)
    # idf['DT'] = pd.to_datetime(df['Entry Year'].astype(str)
    #                            + df['Entry Month'], 
    #                            format='%Y%b')
    # idf.sort_values(by=['DT'], inplace=True)
    
    # add strategic year helper column
    # idf['Strategy Year'] = [str(x) + "-" + str(x+1)[-2] if idf['DT'] >= pd.to_datetime('') for x in idf['Entry Year']]
    
    # set index
    idf.set_index(['Entry Year', 'Entry Month'], inplace=True)
    
    # calculate total hours
    idf['Total'] = idf.sum(axis=1, skipna=True)
    
    # return    
    return idf, first_last


def add_meh(client, idf, first_last):
    """add MEH, accounting for start date"""
    # load dates table
    dates = load_report(client, 'Utilization-Inputs', 'DATES')
    dates['Date'] = pd.to_datetime(dates['Date'])
    dates['Remaining'] = pd.to_numeric(dates['Remaining'])
    dates['Year'] = pd.DatetimeIndex(dates['Date']).strftime('%Y')
    dates['Year'] = pd.to_numeric(dates['Year'])
    dates['Month'] = pd.DatetimeIndex(dates['Date']).strftime('%b')
    
    # get days_remaining in month
    days_remaining = dates.loc[dates['Date']==first_last[1], 'Remaining'] - 1
    
    # calculate MEH per month
    months = dates.groupby(['Year', 'Month']).max()
    months['MEH'] = months['Remaining'] * 8
    months.reset_index(inplace=True)
    months.set_index(['Year', 'Month'], inplace=True)
    
    # join MEH to idf
    MEH_join = months.rename_axis(index={'Year': 'Entry Year',
                                         'Month': 'Entry Month'})
    idf = idf.join(MEH_join['MEH'])
        
    # correct for employees who start in middle of period
    first_month_worked = first_last[0].strftime('%b')
    first_year_worked = int(first_last[0].strftime('%Y'))
    # last_month_worked = first_last[1].strftime('%b')
    # last_year_worked = int(first_last[1].strftime('%Y'))
    
    # for month in sem_months[0:sem_months.index(first_month_worked)]:
    #     print(f'Correcting month {month}')
    #     idf.at[(first_year_worked, month), 'MEH'] = 0
    
    first_month_MEH = dates.loc[dates['Date']==first_last[0], 'Remaining'] * 8 
    idf.at[(first_year_worked, first_month_worked), 'MEH'] = first_month_MEH
    # last_month_MEH = dates.loc[dates['Date']==first_last[0], 'Remaining'] * 8 
    # idf.at[(last_year_worked, last_month_worked), 'MEH'] = last_month_MEH
    
    return idf, dates


def calc_utilization(idf, dates, first_last, idv_emp_type):
    """calculate utilization actuals and projections from idf"""
    # Calculate key variables
    last_day_worked = first_last[1]
    last_month_worked = last_day_worked.strftime('%b')
    last_year_worked = int(last_day_worked.strftime('%Y'))
    meh_hours = idf.loc[(last_year_worked, last_month_worked), 'MEH']
    #TODO: Geeta is getting an empty series 
    # for current_billable so value is not pulled, try at?
    if isinstance(meh_hours, pd.Series) and meh_hours.empty:
        meh_hours = 1
    days_remaining = dates.loc[dates['Date']==last_day_worked, 'Remaining'] - 1
    meh_hours_to_date = meh_hours - days_remaining * 8
    
    # Calculate actual utilization
    if 'Billable' not in idf.columns:
        idf['Utilization'] = 0
        current_billable = 0
        predicted_hours = 0
    else:
        idf['Utilization'] = idf['Billable']/idf['MEH']
        current_billable = idf.loc[(last_year_worked, last_month_worked), 
                            'Billable']
        # TODO: better address edge cases
        if isinstance(current_billable, pd.Series) and current_billable.empty:
            predicted_hours = 0
        else:        
            predicted_hours = (current_billable/meh_hours_to_date) * meh_hours
    
    print(predicted_hours)
    # Calculate utilization to date for this month
    idf['Util to Date'] = idf['Utilization']
    util_to_date = predicted_hours/meh_hours
    try:
        idf.at[(last_year_worked, last_month_worked), 'Util to Date'] = (
            util_to_date
            )
    except:
        pass

    # Calculate FTE
    if idv_emp_type == 'Standard':
        pass
    elif '80' in idv_emp_type:
        idf['MEH'] = idf['MEH'] * 0.80
    elif '75' in idv_emp_type:
        idf['MEH'] = idf['MEH'] * 0.75 
        
    idf['MEH'] = idf['MEH']
    idf['FTE'] = idf['Total'] / idf['MEH']
    current_total = idf.loc[(last_year_worked, last_month_worked), 
                            'Total']
    predicted_total = (current_total/meh_hours_to_date) * meh_hours
    idf['FTE to Date'] = idf['FTE']
    fte_to_date = predicted_total/meh_hours
    try:
        idf.at[(last_year_worked, last_month_worked), 'FTE to Date'] = (
            fte_to_date
            )
    except:
        pass
    
    return idf


def compile_hours(upload=True):
    # Authorize google sheets
    client = auth_gspread()
    
    utilization_in = get_utilization_file(downloads, file_name)
    in_df = pd.read_csv(utilization_in, sep='\t', encoding='utf_16_le')
    sh = client.open('Utilization-Hours')
    wks = sh.worksheet_by_title('june-mar-2020')
    wks.set_dataframe(in_df, 'A1', fit=True)
    print (f"...uploaded to june-mar-2020")
    
    # load all hours from Google Sheet
    hours_report, emp_type = all_hours(client)
    
    # empty list for idfs
    idf_list = []
    names_list = hours_report['User Name'].unique()
    # for each employee, build hours report
    for name in names_list:
        # build monthly hours report
        idf, first_last = idv_monthly_hours(hours_report, name)

        # add MEH
        idf, dates = add_meh(client, idf, first_last)

        # calculate utilization
        idv_emp_type = emp_type.get(name)
        utilization = calc_utilization(idf, dates, first_last, idv_emp_type)
        
        # add name and drop index
        utilization['User Name'] = name
        utilization.reset_index(inplace=True)
        
        # add to idf_list
        idf_list.append(utilization)
    
    # union all idfs
    df = pd.concat(idf_list)
    
    # fill na
    df.fillna(0, inplace=True)
    
    # save to disk
    df.to_csv('data/hours_report.csv', index=False)
    print (f"Hours Report saved in data/")
    
    # upload to Google Sheets
    if upload:
        sh = client.open('Utilization-Hours')
        wks = sh.worksheet_by_title('Utilization-Hours-2')
        wks.set_dataframe(df, 'A1', fit=True)
        print (f"Hours Report uploaded to Utilization-Hours-2")
    
    print(f'Runtime: {datetime.datetime.now() - start}')

    
if __name__=='__main__':
    compile_hours(upload=True)
    