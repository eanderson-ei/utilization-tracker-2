import pygsheets
import pandas as pd
import numpy as np
from datetime import datetime as dt
import os
import sys
import json


### FILE LOCATIONS ###

# Download folder where hours report will be saved from Deltek
downloads = r'C:/Users/Erik/Downloads/'
# Name of the file, excluding any appended numeric distinguisher for repeats
# and name of sheets
tess_file = 'Time and Employee WS'
hours_entries_sheet = 'Hours Entries'
employees_sheet = 'Employee WS'

funded_actuals_file = 'Projects and Budgets'
projects_sheet = 'Activities'
funded_sheet = 'Funded'
actuals_sheet = 'Actuals'

# Google sheets at deltek-server
funded_actuals_sh = 'funded-actuals'
funded_wks = 'funded'
actuals_wks = 'actuals'

deltek_info_sh = 'deltek-info'
employee_work_sched_wks = 'employee-ws'
codes_wks = 'codes'
projects_wks = 'projects'

hours_entries_sh = 'hours-entries'
all_hours_wks = 'all-hours'
all_tables_wks = 'all-tables'
years = [2019, 2020, 2021]
hours_sheets = [str(year) + "-hours" for year in years]
table_sheets = [str(year) + "-table" for year in years]

current_hours_wks = hours_sheets[-1]
current_table_wks = table_sheets[-1]

### FUNCTIONS ###

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


def process_work_schedule(row):
    if pd.isnull(row['Work Schedule']):
        return np.nan
    try:
        return int(row['Work Schedule']) / 100
    except ValueError:
        return 1.0


def first_last_to_username(df):
    # create user name column
    df['First Name'] = df['First Name'].str.strip()  # remove whitespace before Replicon first names
    df['Last Name'] = df['Last Name'].str.strip()
    df['User Name'] = df[['Last Name', 'First Name']].apply(
        lambda x: ', '.join(x), axis=1)
    
    df = df.drop(['First Name', 'Last Name'], axis=1)
    
    return df


def save_to_gs(df, client, worksheet, sheet_name):
    sh = client.open(worksheet)
    wks = sh.worksheet_by_title(sheet_name)
    wks.set_dataframe(df, 'A1', fit = True)
    print (f'{sheet_name} uploaded to {worksheet}')
    

def update_logins(e_df):    
    # convert to dictionary
    usernames = e_df.set_index('E-mail Address')
    emp_dict = usernames['User Name'].to_dict()
    
    # save as json to allow lookup of report based on email address
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
            if key and not key in existing_emp and key != np.nan:
                print(f'UPDATE ENV VAR: {key} IS NEW!')
        f.seek(0)
        json.dump(pass_dict, f, indent=4)
        f.truncate()
    
    print('login information updated')


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


def get_idv_hours_entries(hours_entries, name):
    # drop hours entered after today (common with vacation, time off)
    filt = (
                (hours_entries['User Name']==name) 
                & (hours_entries['Hours Date'] <= dt.today())
                )
    idf = hours_entries.loc[filt, :]
    
    return idf


def get_first_last(idf):
    # get first day worked and last day worked
    first_day_worked = idf['Hours Date'].min()
    last_day_worked = idf['Hours Date'].max()
    first_last = (first_day_worked, last_day_worked)

    return first_last


def pivot_idf(idf):
    idf_sum = (
        idf.groupby(['Entry Month', 'Entry Year', 'Classification'])['Entered Hours']
        .sum()
        .reset_index()
        .set_index(['Entry Year', 'Entry Month'])
    )
    
    # pivot table
    idf_pivot = multiindex_pivot(idf_sum,
                                 columns='Classification', 
                                 values='Entered Hours')

    # fill na as 0
    idf_pivot.fillna(0, inplace=True)

    # calculate total hours
    idf_pivot['Total'] = idf_pivot.sum(axis=1, skipna=True)

    # sort by month
    idf_pivot.reset_index(inplace=True)
    idf_pivot['DT'] = pd.to_datetime(idf_pivot['Entry Year'].astype(str)
                            + idf_pivot['Entry Month'], 
                            format='%Y%b')
    idf_pivot.sort_values(by=['DT'], inplace=True)

    # add strategic year helper column
    def strategy_year(row):
        if row['DT'].month < pd.to_datetime('Apr', format='%b').month:
            return str(row['DT'].year - 1) + "-" + str(row['DT'].year)
        else:
            return str(row['DT'].year) + "-" + str(row['DT'].year + 1)


    idf_pivot['Strategy Year'] = idf_pivot.apply(strategy_year, axis=1)

    # add semester helper column
    def semester(row):
        if (row['DT'].month < pd.to_datetime('Nov', format='%b').month and
        row['DT'].month > pd.to_datetime('Mar', format='%b').month):
            return 'Sem 1'
        else: 
            return 'Sem 2'


    idf_pivot['Semester'] = 'None'

    for strategy_year in idf_pivot['Strategy Year'].unique():
        filt = idf_pivot['Strategy Year'] == strategy_year
        idf_pivot.loc[filt, 'Semester'] = idf_pivot.loc[filt, :].apply(semester, axis=1)

    # set index
    idf_pivot.set_index(['Entry Year', 'Entry Month'], inplace=True)

    return idf_pivot


def add_meh(idf_pivot, first_last):
    idf_pivot['MEH'] = idf_pivot['DT'].apply(
        lambda x: 8 * len(pd.bdate_range(x, x + pd.offsets.MonthEnd(0)))
    )

    # correct for employees who start in middle of the period
    first_month_worked = first_last[0].strftime('%b')
    first_year_worked = first_last[0].strftime('%Y')

    first_month_MEH = 8 * len(pd.bdate_range(first_last[0], first_last[0] + pd.offsets.MonthEnd(0)))

    idf_pivot.at[(first_year_worked, first_month_worked), 'MEH'] = first_month_MEH
    
    return idf_pivot


def calc_utilization(idf_pivot, first_last):
    # Calculate meh_hours_to_date
    fte_remaining = 8 * len(pd.bdate_range(
        first_last[1] + pd.offsets.Day(1), first_last[1] + pd.offsets.MonthEnd(0)))
    last_month_worked = first_last[1].strftime('%b')
    last_year_worked = first_last[1].strftime('%Y')
    meh_hours = idf_pivot.loc[(last_year_worked, last_month_worked), 'MEH']
    meh_hours_to_date = meh_hours - fte_remaining
    
    # Calculate predicted billable hours for the current month
    if 'Billable' in idf_pivot.columns:  
        current_billable = idf_pivot.loc[(last_year_worked, last_month_worked), 
                                'Billable']      
        predicted_hours = (current_billable / meh_hours_to_date) * meh_hours
    # for employees with no billable time, billable and predicted hours are 0
    else:  
        idf_pivot['Billable'] = predicted_hours = 0
        

    # Calculate actual utilization for all months
    idf_pivot['Utilization'] = idf_pivot['Billable'] / idf_pivot['MEH']

    # Calculate utilization to date for this month
    idf_pivot['Util to Date'] = idf_pivot['Utilization']
    util_to_date = predicted_hours/meh_hours
    idf_pivot.at[(last_year_worked, last_month_worked), 'Util to Date'] = (
        util_to_date
        )

    # Calculate actual FTE for all months
    idf_pivot['FTE'] = idf_pivot['Total'] / idf_pivot['MEH']

    # Calculate FTE to date for this month
    current_total = idf_pivot.loc[(last_year_worked, last_month_worked), 
                            'Total']
    predicted_total = (current_total / meh_hours_to_date) * meh_hours
    idf_pivot['FTE to Date'] = idf_pivot['FTE']
    fte_to_date = predicted_total / meh_hours
    idf_pivot.at[(last_year_worked, last_month_worked), 'FTE to Date'] = (
        fte_to_date
        )
    
    return idf_pivot


### EXECUTE ###
if __name__ == '__main__':
    
    start = dt.now()

    # load data
    client = auth_gspread()

    # locate Cognos report from TESS
    tess_fn = get_latest_file(downloads, tess_file)

    # read employees to dataframe
    employeeWS_df = pd.read_excel(tess_fn, employees_sheet, engine='openpyxl')

    # filter out Employee IDs < 100000
    filt = employeeWS_df['Employee ID'] > 100000
    employeeWS_df = employeeWS_df.loc[filt]

    # convert Work Schedule column to percent
    employeeWS_df['Work Schedule'] = employeeWS_df.apply(process_work_schedule, axis=1)

    # create user name column
    employeeWS_df = first_last_to_username(employeeWS_df)

    # add organization
    employeeWS_df['Organization'] = 'Environmental Incentives'

    # save employee ws to deltek-info
    save_to_gs(employeeWS_df, client, deltek_info_sh, employee_work_sched_wks)

    # drop duplicate employee entries
    e_df = employeeWS_df[[
        'Employee ID', 'User Name', 'E-mail Address', 'Active Flag'
        ]].copy()

    e_df = e_df.drop_duplicates()

    # drop inactive employees
    filt = e_df['Active Flag'] == 'Y'
    e_df = e_df.loc[filt, :].copy()

    # update login information (replace with individual login system)
    update_logins(e_df)

    # Read hours entries
    hours_entries = pd.read_excel(tess_fn, hours_entries_sheet, engine='openpyxl')

    # Read hours entries
    # Deltek adds rows for long comments and merges cells (why are they like this?)
    # remove null rows (i.e., the added row)
    hours_entries = hours_entries.dropna(how='all')

    # create month and year convenience columns
    hours_entries['Entry Month'] = pd.DatetimeIndex(hours_entries['Hours Date']).strftime('%b')
    hours_entries['Entry Year'] = pd.DatetimeIndex(hours_entries['Hours Date']).strftime('%Y')

    # create user name column
    hours_entries = first_last_to_username(hours_entries)

    # rename columns
    hours_entries = hours_entries.rename(
                        {'Project ID': 'Task ID', 'Project Name': 'Task Name'}, 
                    axis=1)

    # Code hours entries
    # read in codes 
    codes_df = load_report(client, deltek_info_sh, codes_wks)

    # convert to dictionary
    codes_df = codes_df.set_index('User Defined Code 3')
    codes_dict = codes_df['Code'].to_dict()

    # locate Cognos report from TESS
    projects_fn = get_latest_file(downloads, funded_actuals_file)

    # read employees to dataframe
    projects_df = pd.read_excel(projects_fn, projects_sheet, engine='openpyxl')
    
    # replace User defined codes with Codes
    account_group_df = projects_df[['Project ID', 'Account Group']].set_index('Project ID')
    account_dict = account_group_df['Account Group'].to_dict()
    hours_entries['Account Group'] = hours_entries['Task ID'].replace(account_dict)
    hours_entries['Classification'] = hours_entries['Account Group'].replace(codes_dict)
    
    hours_entries = hours_entries.drop('Account Group', axis=1)

    # remove whitespace
    projects_df['Project Name'] = projects_df['Project Name'].str.strip()
    projects_df['Organization Name'] = projects_df['Organization Name'].str.strip()
    
    # filter projects to Level 1 only
    filt = (projects_df['Level Number'] == 1) | (projects_df['Level Number'] == str(1))
    level_one_df = projects_df.loc[filt, ['Project ID', 'Project Name']].copy()

    # check for uniqueness of project id
    print(len(level_one_df), len(level_one_df['Project ID'].unique()))
    assert len(level_one_df) == len(level_one_df['Project ID'].unique()), "Check for duplicate project IDs at Level 1"

    # convert to dictionary with keys as strings
    level_one_df = level_one_df.set_index('Project ID')
    project_dict = level_one_df['Project Name'].to_dict()
    project_dict = {str(key): str(value) for key, value in project_dict.items()}

    # add project column to project_df
    projects_df['Project'] = projects_df['Project ID'].str[:4].replace(project_dict)
    
    # Save projects to Google Sheets
    save_to_gs(projects_df, client, deltek_info_sh, projects_wks)
    
    # Join projects to hours_entries
    hours_entries['Project'] = hours_entries['Task ID'].str[:4].replace(project_dict)

    # update 'Indirect' Projects to Classification
    filt = hours_entries['Project'] == 'Indirect'
    hours_entries.loc[filt, 'Project'] = hours_entries.loc[filt, 'Classification']

    # update 'Unbillable'
    filt = hours_entries['Task Name'].str.contains('Unbillable', na=False)
    hours_entries.loc[filt, 'Classification'] = 'Unbillable'

    # obscure time off type and comments
    filt = hours_entries['Classification'] == 'Time Off'
    hours_entries.loc[filt, 'Task Name'] = 'Time Off'
    hours_entries.loc[filt, 'Comments'] = ''
    
    # categorize null Classifications (when an old timecode is removed from the system)
    hours_entries['Classification'] = hours_entries['Classification'].fillna('None')

    # save hours entries to google sheets
    save_to_gs(hours_entries, client, hours_entries_sh, current_hours_wks)

    timetable_list = []

    for name in hours_entries['User Name'].unique():
        print(f'Processing {name}')
        # Build timetable for each employee
        idf = get_idv_hours_entries(hours_entries, name)
        
        if not idf.empty:
        
            # get first and last day worked
            first_last = get_first_last(idf)
            
            # pivot individual hours
            idf_pivot = pivot_idf(idf)

            # add meh
            idf_pivot = add_meh(idf_pivot, first_last)
            
            # calc utilization
            idf_pivot = calc_utilization(idf_pivot, first_last)
            
            # associate name with record
            idf_pivot['User Name'] = name
            idf_pivot = idf_pivot.reset_index()
            
            timetable_list.append(idf_pivot)
        
    # concat all timetables
    timetables = pd.concat(timetable_list)

    # upload timetables to google sheets
    save_to_gs(timetables, client, hours_entries_sh, current_table_wks)


    ### CHECKS ###

    # # check for 40 hours per week
    # hours_entries_week = hours_entries.copy()
    # hours_entries_week['week'] = hours_entries_week['Hours Date'].dt.isocalendar().week
    # filt = hours_entries_week['Classification'] == 'Billable'
    # weekly_hours = hours_entries_week.loc[filt].groupby(['User Name','Entry Year', 'Entry Month', 'week'])['Entered Hours'].sum()
    # filt = weekly_hours > 40

    # print('The following employees have worked more than 40 billable hours in a week:\n')
    # for idx, row in weekly_hours.loc[filt].iteritems():
    #     print(idx, row)
        
    print(f'Runtime: {dt.now() - start}')
