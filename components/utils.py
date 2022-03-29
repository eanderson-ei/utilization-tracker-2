"""functions required to run utilization report"""

import pygsheets
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np

sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']
# cutoff = 7
year_helper = [0] * 9 + [1] * 3


# def get_month_fte(month, year):
#     """returns fte hours given any month ('MMM') and year ('YYYY')"""
#     year_months = sem_months[9:] + sem_months[:9]
#     month_idx = year_months.index(month) + 1  # date is 1 indexed
#     start_date = date(year, month_idx, 1)
#     if month_idx == 12:
#         end_month = 1
#         end_year = year + 1
#     else:
#         end_month = month_idx + 1
#         end_year = year
#     end_date = date(end_year, end_month, 1)
#     days = np.busday_count(start_date, end_date)
#     hours = days * 8
#     return hours


# def get_sem_fte(sem, year):
#     """returns semester fte for any semester ('Sem X') and year ('XXXX-XXXX')"""
#     base_year = int(year[:4])
#     sem_years = [base_year + helper for helper in year_helper]
#     if sem == 'Sem 1':
#         months = sem_months[:cutoff]
#         years = sem_years[:cutoff]
#     elif sem == 'Sem 2':
#         months = sem_months[cutoff:]
#         years = sem_years[cutoff:]
#     else:
#         print('Incorrect input string to functions.get_sem_fte')
#     sem_fte = 0
#     for month, year in zip(months, years):
#         month_fte = get_month_fte(month, year)
#         sem_fte += month_fte
#     return sem_fte
    


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


def predict_utilization(idf, predict_input):
    # calculated predicted values
    filt = idf['DT'] == idf['DT'].max()
    predicted_utilization = idf.loc[filt, 'Util to Date'].values[0]
    predicted_fte = idf.loc[filt, 'FTE to Date'].values[0]
    
    # update with predicted input
    if predict_input and predict_input > 0:
        predicted_utilization = predict_input/100
    
    # create prediction space
    max_DT = idf['DT'].max()
    max_month_index = sem_months.index(max_DT.strftime('%b')) + 1
    prediction_months = sem_months[max_month_index:] 
    prediction_years = [helper + idf['Entry Year'].max() 
                        for helper in year_helper[max_month_index:]]
    pdf = pd.DataFrame({'Entry Year': prediction_years, 
                        'Entry Month': prediction_months})
    pdf['DT'] = pd.to_datetime(pdf['Entry Year'].astype(str)
                               + pdf['Entry Month'], 
                               format='%Y%b')
    pdf['MEH'] = pdf['DT'].apply(
        lambda x: 8 * len(pd.bdate_range(x, x + pd.offsets.MonthEnd(0)))
    )
    # pdf['MEH'] = 8 * np.busday_count(
    #     pdf['DT'].dt.date, pdf['DT'].dt.date + relativedelta(months=1)
    #     )
    
    
    # add predicted values 
    if not pdf.empty:
        pdf['Predicted Billable'] = pdf['MEH'] * predicted_utilization
        pdf['Predicted Total'] = pdf['MEH'] * predicted_fte
    else:
        pdf['Predicted Billable'] = pd.Series([])
        pdf['Predicted Total'] = pd.Series([])
    
    print(pdf)
    
    # append to idf
    idf = idf.append(pdf, ignore_index=True)
    idf.fillna(0, inplace=True)
    
    # add strategic year helper column
    def strategy_year(row):
        if row['DT'].month < pd.to_datetime('Apr', format='%b').month:
            return str(row['DT'].year - 1) + "-" + str(row['DT'].year)
        else:
            return str(row['DT'].year) + "-" + str(row['DT'].year + 1)
    
    
    idf['Strategy Year'] = idf.apply(strategy_year, axis=1)
    
    # populate predicted columns
    filt = idf['DT'] >= pd.to_datetime(pd.to_datetime('2019' + 'Apr',  #TODO 
                                                      format='%Y%b'))
    idf.loc[filt, 'Predicted Billable'] = (idf.loc[filt, 'Predicted Billable'] 
                                           + idf.loc[filt, 'Billable'])
    idf.loc[filt, 'Predicted Total'] = (idf.loc[filt, 'Predicted Total'] 
                                        + idf.loc[filt, 'Total'])
    
    
    # update predicted for this month
    filt = idf['DT'] == max_DT
    this_month_meh = idf.loc[filt, 'MEH'].values[0]
    idf.at[filt, 'Predicted Billable'] = predicted_utilization * this_month_meh
    idf.at[filt, 'Predicted Total'] = predicted_fte * this_month_meh
    
    # calculate averages
    for sy in idf['Strategy Year'].unique():
        filt = idf['Strategy Year'] == sy
        idf.loc[filt, 'Avg Utilization'] = (idf.loc[filt, 'Predicted Billable'].cumsum()
                                    / idf.loc[filt, 'MEH'].cumsum())
        idf.loc[filt, 'Avg FTE'] = (idf.loc[filt, 'Predicted Total'].cumsum()
                                    / idf.loc[filt, 'MEH'].cumsum())
    
    idf.sort_values('DT', inplace=True)
    
    return idf, max_DT


### Utilities for Projects ###

def get_project_totals(idf, start_date, end_date):
    filt = (idf['Hours Date'] >= start_date) & (idf['Hours Date'] <= end_date) 
    entries_by_date = idf.loc[filt, :]
    project_totals = entries_by_date.groupby('Project')['Entered Hours'].sum()
    project_totals.sort_values(inplace=True)
    
    return project_totals


def get_task_totals(idf, start_date, end_date, project):
    filt = ((idf['Hours Date'] >= start_date) & (idf['Hours Date'] <= end_date)
            & (idf['Project'] == project))
    entries_by_date = idf.loc[filt, :]
    task_totals = entries_by_date.groupby('Task Name')['Entered Hours'].sum()
    task_totals.sort_values(inplace=True)
    
    return task_totals


def get_meh_from_entries(idf, start_date, end_date):
    filt = (idf['Hours Date'] >= start_date) & (idf['Hours Date'] <= end_date) 
    idf = idf.loc[filt, :]
    max_date = idf['Hours Date'].max().date()
    min_date = idf['Hours Date'].min().date()
    days = np.busday_count(min_date, max_date + timedelta(days=1))
    hours = days * 8
    return hours

### Utilities for Teams ###

def get_user_totals(pdf, start_date, end_date):
    filt = (pdf['Hours Date'] >= start_date) & (pdf['Hours Date'] <= end_date)
    entries_by_date = pdf.loc[filt, :]
    user_totals = entries_by_date.groupby('User Name')['Entered Hours'].sum()
    user_totals.sort_values(inplace=True)
    
    return user_totals


def get_user_task_totals(pdf, start_date, end_date, user):
    filt = ((pdf['Hours Date'] >= start_date) & (pdf['Hours Date'] <= end_date)
            & (pdf['User Name'] == user))
    entries_by_date = pdf.loc[filt, :]
    user_totals = entries_by_date.groupby('Task Name')['Entered Hours'].sum()
    user_totals.sort_values(inplace=True)
    
    return user_totals


### -------------- ALLOCATION TABLE -------------------------------------- ###
    
def read_table(table_name, con):
    # read from database
    df = pd.read_sql_table(table_name, con=con)
        
    return df


def build_allocation_table(df):
    # calcualte DT column
    df['DT'] = pd.to_datetime(df['Entry Year'].astype(str)
                               + df['Entry Month'], 
                               format='%Y%b')
    df.sort_values(by=['DT'], inplace=True)
    
    # add strategic year helper column
    def strategy_year(row):
        if row['DT'].month < pd.to_datetime('Apr', format='%b').month:
            return str(row['DT'].year - 1) + "-" + str(row['DT'].year)
        else:
            return str(row['DT'].year) + "-" + str(row['DT'].year + 1)
    
        
    df['Strategy Year'] = df.apply(strategy_year, axis=1)
    
    # add semester helper column
    def semester(row):
        if (row['DT'].month < pd.to_datetime('Nov', format='%b').month and
        row['DT'].month > pd.to_datetime('Mar', format='%b').month):
            return 'Sem 1'
        else: 
            return 'Sem 2'
    
    
    df['Semester'] = 'None'
    for strategy_year in df['Strategy Year'].unique():
        filt = df['Strategy Year'] == strategy_year
        df.loc[filt, 'Semester'] = df.loc[filt, :].apply(semester, axis=1)
        
    return df    


def decalc_allocation_data(data):
    df = pd.DataFrame(data)
    columns = [col for col in df.columns if col in sem_months + ['Project', 'User Name']]
    col = [col for col in df.columns if col in ['Project', 'User Name']][0]
    filt = df[col] != 'Total'
    dff = df.loc[filt, columns]
    return dff


def save_planned_hours(df, table_name, con):
    # format provided data
    
    
    
    existing_df = pd.read_sql_table(table_name, con=con)
    
    existing_df
    
    df.to_sql("planned_hrs", con=con, if_exists='replace', index=False)  