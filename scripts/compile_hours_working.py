"""This script calculates utilization, r&d, g&a, and time off for each
individual. Calculated one by one. See compile_hours for attempt at group
calculation. Note that Deltek may have a report better suited for this."""

import pygsheets
import pandas as pd
import numpy as np
from datetime import datetime as dt
import os
import sys
import json

start = dt.now()

# GLOBALS

# Download folder where hours report will be saved from Deltek
downloads = r'C:/Users/Erik/Downloads/'
# Name of the file, excluding any appended numeric distinguisher for repeats
util_file = 'Utilization Tabular'
projects_file = 'Projects Tabular'
employees_file = 'Employees'
# FUNCTIONS

def get_latest_file(downloads, file_name):
    # list all files in downloads
    all_files = [f for f in os.listdir(downloads) 
                 if f.startswith(file_name)]
    # get save times
    file_versions = [os.path.getmtime(os.path.join(downloads, f)) 
                     for f in all_files]
    # access file with most recent save time
    latest_file = [f for f in all_files 
                   if os.path.getmtime(os.path.join(downloads, f)) 
                   == max(file_versions)]
    
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
    :param sheet_title: sheet name
    :returns pandas dataframe
    """
    # load data from google sheet
    sh = client.open(spreadsheet)
    wks = sh.worksheet_by_title(sheet_title)
    data = wks.get_all_records(empty_value=None)  # get_as_df can't handle empty columns
    df = pd.DataFrame(data)
    df.dropna(axis=0, how='all', inplace=True)
    
    return df


def join_projects(hours_report, projects):
    print('Joining Projects')
    # projects = load_report(client, 'Utilization-Inputs', 'PROJECTS')
    pdf = projects.drop('Project Name', axis=1)
    
    ### ADD MISSING CODE FROM CHAD ###
    pdf = pdf.append(pd.DataFrame({'Project ID': ['2013.000.002.01'],
                                   'Charge Branch Description': ['OC WQIP TO5 PMs']}))
    ### ~~~ ###
    
    # merge projects to hours_report
    df = hours_report.merge(pdf, on='Project ID', how='inner')
    df.rename({'Charge Branch Description': 'Project',
               'Project ID': 'Task ID',
               'Project Name': 'Task Name'}, 
              axis=1, inplace=True)
    
    if len(hours_report) > len(df):
        print("!!! Tasks are missing project classifications. Run "
              "Projects Tabular from Cognos again and retry." + 
              f"Missing {len(hours_report) - len(df)}")
        filt = ~hours_report['Project ID'].isin(df['Task ID'])
        missing_df = hours_report[filt]
        print(missing_df)
        missing_df.to_csv('data/missing_projects.csv')
    
    return df


def all_hours(client):
    """Combine Replicon and Cognos hours reports
    :param client: client object for accessing google
    :returns: dataframe of hours x person x day
    """
    print('Loading utilization data from Utilization-Hours')
    # load 2019 hours
    df2019 = load_report(client, 'Utilization-Hours', 'hours-2019')
    
    # load 2020 apr - may hours
    df2020_1 = load_report(client, 'Utilization-Hours','apr-may-2020')

    # load jun 2020 + hours
    df2020_2 = load_report(client, 'Utilization-Hours','june-mar-2020')
    
    # union all 
    print('Combining and formatting data')
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
    filt = df['Task Name'].str.contains('Unbillable')
    df.loc[filt, 'Code'] = 'IRD'
    
    # reclass 'User Defined Code 3' to category
    codes_df = load_report(client, 'Utilization-Inputs', 'CODES')
    codes = dict(zip(codes_df['User Defined Code 3'], codes_df['Code']))
    df['Classification'] = df['Code'].replace(codes)
    
    return df


def get_emp_type(hours_report):
    """get employee type as standard or part time"""
    emp_type = set(zip(hours_report['User Name'], 
                       hours_report['Work Schedule Description']))
    emp_type = dict(emp_type)
    
    # return
    return emp_type


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
    # Subset by individual and drop any forward-booked holiday time
    print(f'Processing {name}')
    filt = ((hours_report['User Name']==name) &
            (hours_report['Hours Date'] <= dt.combine(
                dt.today().date(), dt.min.time()
                )
             ))
    df = hours_report.loc[filt, :]
    
    # get first day worked and last day worked
    first_day_worked = df['Hours Date'].min()
    last_day_worked = df['Hours Date'].max()
    first_last = (first_day_worked, last_day_worked)
    
    # Calculate monthly total hours
    individual_hours = (
        df.groupby(['Entry Month', 'Entry Year', 'Classification'])
        .sum()
        .reset_index()
        .set_index(['Entry Year', 'Entry Month'])
    )
    
    # pivot table
    idf = multiindex_pivot(individual_hours,
                           columns='Classification', 
                           values='Entered Hours')
    
    # fill na as 0
    idf.fillna(0, inplace=True)
    
    # calculate total hours
    idf['Total'] = idf.sum(axis=1, skipna=True)
    
    # sort by month
    idf.reset_index(inplace=True)
    idf['DT'] = pd.to_datetime(idf['Entry Year'].astype(str)
                               + idf['Entry Month'], 
                               format='%Y%b')
    idf.sort_values(by=['DT'], inplace=True)
    
    # add strategic year helper column
    def strategy_year(row):
        if row['DT'].month < pd.to_datetime('Apr', format='%b').month:
            return str(row['DT'].year - 1) + "-" + str(row['DT'].year)
        else:
            return str(row['DT'].year) + "-" + str(row['DT'].year + 1)
    
    
    idf['Strategy Year'] = idf.apply(strategy_year, axis=1)
    
    # add semester helper column
    def semester(row):
        if (row['DT'].month < pd.to_datetime('Nov', format='%b').month and
        row['DT'].month > pd.to_datetime('Mar', format='%b').month):
            return 'Sem 1'
        else: 
            return 'Sem 2'
    
    
    idf['Semester'] = 'None'
    for strategy_year in idf['Strategy Year'].unique():
        filt = idf['Strategy Year'] == strategy_year
        idf.loc[filt, 'Semester'] = idf.loc[filt, :].apply(semester, axis=1)
    
    # set index
    idf.set_index(['Entry Year', 'Entry Month'], inplace=True)

    # return    
    return idf, first_last


def load_dates(client):
    """load dates report for calculating MEH"""
    # load dates table
    dates = load_report(client, 'Utilization-Inputs', 'DATES')
    dates['Date'] = pd.to_datetime(dates['Date'])
    dates['Remaining'] = pd.to_numeric(dates['Remaining'])
    dates['Year'] = pd.DatetimeIndex(dates['Date']).strftime('%Y')
    dates['Year'] = pd.to_numeric(dates['Year'])
    dates['Month'] = pd.DatetimeIndex(dates['Date']).strftime('%b')
    
    # calculate MEH per month
    months = dates.groupby(['Year', 'Month']).max()
    months['MEH'] = months['Remaining'] * 8
    
    return dates, months

    
def add_meh(client, idf, first_last, dates, months):
    """add MEH, accounting for start date"""
    # join MEH to idf
    MEH_join = months.rename_axis(index={'Year': 'Entry Year',
                                         'Month': 'Entry Month'})
    idf = idf.join(MEH_join['MEH'])
        
    # correct for employees who start in middle of period
    first_month_worked = first_last[0].strftime('%b')
    first_year_worked = int(first_last[0].strftime('%Y'))    
    first_month_MEH = dates.loc[dates['Date']==first_last[0], 'Remaining'] * 8 
    idf.at[(first_year_worked, first_month_worked), 'MEH'] = first_month_MEH
    
    # get days remaining
    days_remaining = dates.loc[dates['Date']==first_last[1], 'Remaining'] - 1
    
    return idf, days_remaining


def calc_utilization(idf, first_last, idv_emp_type, days_remaining):
    """calculate utilization actuals and projections from idf"""
    # Calculate key variables
    last_day_worked = first_last[1]
    last_month_worked = last_day_worked.strftime('%b')
    last_year_worked = int(last_day_worked.strftime('%Y'))
    meh_hours = idf.loc[(last_year_worked, last_month_worked), 'MEH']    
    meh_hours_to_date = meh_hours - days_remaining * 8
    
    # Calculate actual utilization
    if 'Billable' not in idf.columns:  # some employees have no billable time
        idf['Utilization'] = 0
        current_billable = 0
        predicted_hours = 0
    else:
        idf['Utilization'] = idf['Billable']/idf['MEH']
        current_billable = idf.loc[(last_year_worked, last_month_worked), 
                                   'Billable']      
        predicted_hours = (current_billable/meh_hours_to_date) * meh_hours
    
    # Calculate utilization to date for this month
    idf['Util to Date'] = idf['Utilization']
    util_to_date = predicted_hours/meh_hours
    idf.at[(last_year_worked, last_month_worked), 'Util to Date'] = (
        util_to_date
        )

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
    idf.at[(last_year_worked, last_month_worked), 'FTE to Date'] = (
        fte_to_date
        )
    
    return idf


def update_employees(e_df):
    # create user name column
    e_df['First Name'] = e_df['First Name'].str.strip()  # remove whitespace before Replicon first names
    e_df['Last Name'] = e_df['Last Name'].str.strip()
    e_df['User Name'] = e_df[['Last Name', 'First Name']].apply(
        lambda x: ', '.join(x), axis=1)
    
    # drop inactive employees
    filt = e_df['Active Flag'] == 'Y'
    e_df = e_df.loc[filt, :].copy()
    
    # convert to dictionary
    usernames = e_df.set_index('E-mail Address')
    emp_dict = usernames['User Name'].to_dict()
    
    # save as json
    with open('components/usernames.json', 'w') as f:
        json.dump(emp_dict, f, indent=4)
        
    # associate all emails with password 'incentives'
    #TODO: allow for custom passwords
    usernames['password'] = 'incentives'
    pass_dict = usernames['password'].to_dict()
    
    # save as json to secrets
    with open('secrets/passwords.json', 'r+') as f:
        existing_emp = json.load(f)
        for key in pass_dict.keys():
            if not key in existing_emp:
                print(f'UPDATE ENV VAR: {key} IS NEW!')
        json.dump(pass_dict, f, indent=4)
    
    # return active employee names for processing
    return usernames['User Name'].values


def compile_hours():
    # Save employees login info
    employees_in = get_latest_file(downloads, employees_file)
    e_df = pd.read_csv(employees_in, sep='\t',
                       encoding='utf_16_le')
    names = update_employees(e_df)
    print (f"...saved to components/usernames.json")
    
    # Authorize google sheets
    client = auth_gspread()
    
    # read latest utilization report
    utilization_in = get_latest_file(downloads, util_file)
    in_df = pd.read_csv(utilization_in, sep='\t', 
                        encoding='utf_16_le')
    
    # read latest projects report
    projects_in = get_latest_file(downloads, projects_file)
    p_df = pd.read_csv(projects_in, sep='\t', 
                        encoding='utf_16_le')
    
    # join utilization to projects
    jun_mar_2021 = join_projects(in_df, p_df)
      
    # save report to 'june-mar-2020'
    sh = client.open('Utilization-Hours')
    wks = sh.worksheet_by_title('june-mar-2020')
    wks.set_dataframe(jun_mar_2021, 'A1', fit=True)
    print (f"...uploaded to june-mar-2020")
    
    # save projects to 'PROJECTS'
    sh = client.open('Utilization-Inputs')
    wks = sh.worksheet_by_title('PROJECTS')
    wks.set_dataframe(p_df, 'A1', fit=True)
    print (f"...uploaded to PROJECTS")
    
    # load all hours from Google Sheet
    hours_report = all_hours(client)
    
    # load dates
    dates, months = load_dates(client)
    
    # get employee type
    emp_type = get_emp_type(hours_report)
    
    # empty list for idfs
    idf_list = []
    
    # names from hours report
    names_list = hours_report['User Name'].unique()
    names_list.sort()
    
    # for each employee, build hours report (names from employees report)
    for name in names: 
        if name in names_list:
            # build monthly hours report
            idf, first_last = idv_monthly_hours(hours_report, name)

            # add MEH
            idf, days_remaining = add_meh(client, idf, first_last, dates, months)

            # calculate utilization
            idv_emp_type = emp_type.get(name)
            utilization = calc_utilization(idf, first_last, idv_emp_type, days_remaining)
            
            # add name and drop index
            utilization['User Name'] = name
            utilization.reset_index(inplace=True)
            
            # add to idf_list
            idf_list.append(utilization)
        else:
            print(f'{name} not present in hours report')
    
    # union all idfs
    df = pd.concat(idf_list)
    
    # fill na
    df.fillna(0, inplace=True)
    
    # save to disk
    df.to_csv('data/hours_report.csv', index=False)
    print (f"Hours Report saved in data/")
    
    # upload to Google Sheets
    sh = client.open('Utilization-Hours')
    wks = sh.worksheet_by_title('Utilization-Hours-2')
    wks.set_dataframe(df, 'A1', fit=True)
    print (f"Hours Report uploaded to Utilization-Hours-2")
    
    print(f'Runtime: {dt.now() - start}')

    
if __name__=='__main__':
    compile_hours()
    