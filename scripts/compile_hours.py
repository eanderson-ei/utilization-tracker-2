"""converts hours entries to monthly, compiling from 2019 onward from
Replicon and Deltek"""

import pygsheets
import pandas as pd
import numpy as np
import datetime

import time

start = datetime.datetime.now()
# TODO: handle instance when employee changes work description type

# GLOBALS

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


def get_dates(client):
    # load dates table
    dates = load_report(client, 'Utilization-Inputs', 'DATES')
    dates['Date'] = pd.to_datetime(dates['Date'])
    dates['Remaining'] = pd.to_numeric(dates['Remaining'])
    dates['Year'] = pd.DatetimeIndex(dates['Date']).strftime('%Y')
    dates['Year'] = pd.to_numeric(dates['Year'])
    dates['Month'] = pd.DatetimeIndex(dates['Date']).strftime('%b')
    
    return dates


def get_hours_report(client):
    """Combine Replicon and Cognos hours reports
    :param client: client object for accessing google
    :returns: dataframe of hours x person x day
    """
    print("building hours report")
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
    df['User Name'] = df[['Last Name', 'First Name']].apply(
        lambda x: ','.join(x), axis=1)
    
    # reclass unbillable to R&D
    df['Code'] = df['User Defined Code 3']
    filt = df['Project Name'].str.contains('Unbillable')
    df.loc[filt, 'Code'] = 'IRD'
    
    # reclass 'User Defined Code 3' to category
    codes_df = load_report(client, 'Utilization-Inputs', 'CODES')
    codes = dict(zip(codes_df['User Defined Code 3'], codes_df['Code']))
    df['Classification'] = df['Code'].replace(codes)
    
    return df


def get_employee_types(hours_report):
    # TODO: consider adding employee report to time report for these data
    # get employee work as dictionary, note only last valid type is returned
    emp_type = set(zip(hours_report['User Name'], 
                       hours_report['Work Schedule Description']))
    emp_type = dict(emp_type)
    
    # return
    return emp_type


def get_first_last(hours_report, name):
    # Subset by individual
    idf = hours_report.loc[hours_report['User Name']==name]
    if idf.empty:
        print (f'Employee {name} not found')
        pass
        
    # get first day worked and last day worked
    first_day_worked = idf['Hours Date'].min()
    last_day_worked = idf.loc[~idf['Classification'].isin(['Time Off']), 
                             'Hours Date'].max()
    if last_day_worked > datetime.datetime.today():
        last_day_worked = datetime.datetime.today().date()
    first_last = (first_day_worked, last_day_worked)
    
    return first_last


def multiindex_pivot(df, columns=None, values=None):
    #https://github.com/pandas-dev/pandas/issues/23955
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


def get_monthly_hours(hours_report):
    print("building monthly report")
    monthly_hours = (
        hours_report.groupby(['User Name', 'Entry Month', 'Entry Year', 'Classification'])
        .sum()
        .reset_index()
        .set_index(['User Name', 'Entry Year', 'Entry Month'])
    )
    
    df = multiindex_pivot(monthly_hours,
                          columns='Classification',
                          values='Entered Hours')
                                                                                                                                                                                              
    df.reset_index(inplace=True)
    
    df['month_id'] = df['Entry Month'].replace(month_dict)
    df.sort_values(by=['User Name', 'Entry Year', 'month_id'], inplace=True)
    df.drop('month_id', axis=1, inplace=True)
    
    df.set_index(['User Name', 'Entry Year', 'Entry Month'], inplace=True)
    
    df['Total'] = df.sum(axis=1, skipna=True)
    
    df.fillna(0, inplace=True)
    
    return df


def add_meh(monthly_hours, dates):
    # calculate MEH per month
    months = dates.groupby(['Year', 'Month']).max()
    months['MEH'] = months['Remaining'] * 8
    # months.reset_index(inplace=True)
    # months.set_index(['Year', 'Month'], inplace=True)
    
    # reset index of hours_report
    monthly_hours.reset_index(inplace=True)
    monthly_hours.set_index(['Entry Year', 'Entry Month'], inplace=True)
    
    # join MEH to idf
    MEH_join = months.rename_axis(index={'Year': 'Entry Year',
                                         'Month': 'Entry Month'})
    monthly_hours = monthly_hours.join(MEH_join['MEH'])
    
    monthly_hours.reset_index(inplace=True)
    monthly_hours.set_index(['User Name', 'Entry Year', 'Entry Month'],
                            inplace=True)
    
    return monthly_hours
 
 
def correct_for_start_date(monthly_hours, dates, first_last, name):
    # correct for employees who start in middle of period
    first_month_worked = first_last[0].strftime('%b')
    first_year_worked = int(first_last[0].strftime('%Y'))
    first_month_MEH = dates.loc[dates['Date']==first_last[0], 'Remaining'] * 8 
    monthly_hours.at[
        (name, first_year_worked, first_month_worked), 'MEH'] = first_month_MEH
    
    return monthly_hours


def calc_utilization(monthly_hours, dates, first_last, name):
    """calculate utilization actuals and projections from idf"""
    # TODO: meh_hours coming back as df with len 108, should be single value
    # Calculate key variables
    last_day_worked = first_last[1]
    last_month_worked = last_day_worked.strftime('%b')
    last_year_worked = int(last_day_worked.strftime('%Y'))
    meh_hours = monthly_hours.loc[(name, last_year_worked, last_month_worked), 'MEH']
    print(f'MEH HOURS: {meh_hours}')
    days_remaining = dates.loc[dates['Date']==last_day_worked, 'Remaining'] - 1
    print(f'DAYS REMAINING: {days_remaining}')
    meh_hours_to_date = meh_hours - days_remaining * 8
    print('1')
    
    monthly_hours['Utilization'] = monthly_hours['Billable']/monthly_hours['MEH']
    current_billable = monthly_hours.loc[(name, last_year_worked, last_month_worked), 
                        'Billable']        
    predicted_hours = (current_billable/meh_hours_to_date) * meh_hours
    print('2')
    
    # Calculate utilization to date for this month
    monthly_hours['Util to Date'] = monthly_hours['Utilization']
    util_to_date = predicted_hours/meh_hours
    monthly_hours.at[(name, last_year_worked, last_month_worked), 'Util to Date'] = (
        util_to_date
        )
    print('3')
    
    return monthly_hours


def calc_meh(monthly_hours, dates, first_last, name, emp_type):
    # Calculate key variables
    last_day_worked = first_last[1]
    last_month_worked = last_day_worked.strftime('%b')
    last_year_worked = int(last_day_worked.strftime('%Y'))
    meh_hours = monthly_hours.loc[(name, last_year_worked, last_month_worked), 'MEH']
    days_remaining = dates.loc[dates['Date']==last_day_worked, 'Remaining'] - 1
    meh_hours_to_date = meh_hours - days_remaining * 8
    
    # Calculate FTE
    if idv_emp_type == 'Standard':
        pass
    elif '80' in idv_emp_type:
        monthly_hours['MEH'] = monthly_hours['MEH'] * 0.80
    elif '75' in idv_emp_type:
        monthly_hours['MEH'] = monthly_hours['MEH'] * 0.75 

    monthly_hours['FTE'] = monthly_hours['Total'] / monthly_hours['MEH']
    current_total = monthly_hours.loc[(name, last_year_worked, last_month_worked), 
                            'Total']
    predicted_total = (current_total/meh_hours_to_date) * meh_hours
    monthly_hours['FTE to Date'] = monthly_hours['FTE']
    fte_to_date = predicted_total/meh_hours
    monthly_hours.at[(name, last_year_worked, last_month_worked), 'FTE to Date'] = (
        fte_to_date
        )

    return monthly_hours


if __name__=='__main__':
    client = auth_gspread()
    
    hours_report = get_hours_report(client)
    dates = get_dates(client)
    
    emp_types = get_employee_types(hours_report)
    
    employees = hours_report['User Name'].unique()
    
    emp_first_last = {}
    for employee in employees:   
        first_last = get_first_last(hours_report, employee)
        emp_first_last.update({employee: first_last})
    
    monthly_hours = get_monthly_hours(hours_report)
    
    monthly_hours = add_meh(hours_report, dates)
    
    for employee in employees:
        print(f'Processing {employee}')
        first_last = emp_first_last.get(employee)
        monthly_hours = correct_for_start_date(monthly_hours, dates, first_last, employee)
        monthly_hours = calc_utilization(monthly_hours, dates, first_last, employee)
        monthly_hours = calc_meh(monthly_hours, dates, first_last, employee)
    
    print(monthly_hours)

    print(datetime.datetime.now() - start)


