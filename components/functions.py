"""functions required to run utilization report"""

import pygsheets
import pandas as pd


sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']
year_helper = [0] * 9 + [1] * 3
#TODO: calculate this rather than hard-code
meh = [176, 168, 176, 184, 168, 176, 176, 168, 184,
       168, 160, 184]


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


def import_hours():
    client = auth_gspread()
    df = load_report(client, 'Utilization-Hours', 'Utilization-Hours-2')
    
    # set dtypes
    df['DT'] = pd.to_datetime(df['DT'])
    
    # get entries
    entries = load_report(client, 'Utilization-Hours', 'june-mar-2020')
    entries['Hours Date'] = pd.to_datetime(entries['Hours Date'])
    
    return df, entries


def predict_utilization(idf, predict_input):
    # calculated predicted values
    filt = idf['DT'] == idf['DT'].max()
    predicted_utilization = idf.loc[filt, 'Util to Date'].values[0]
    predicted_fte = idf.loc[filt, 'FTE to Date'].values[0]
    
    # update with predicted input
    if predict_input and predict_input > 0:
        predicted_utilization = predict_input/100
    
    # create prediction space
    filt = idf['Entry Year'] == idf['Entry Year'].max()  # Necessary?
    max_DT = idf.loc[filt, 'DT'].max()
    max_month_index = sem_months.index(max_DT.strftime('%b')) + 1
    prediction_months = sem_months[max_month_index:] 
    prediction_years = [helper + idf['Entry Year'].max() 
                        for helper in year_helper[max_month_index:]]
    pdf = pd.DataFrame({'Entry Year': prediction_years, 
                        'Entry Month': prediction_months})
    pdf['DT'] = pd.to_datetime(pdf['Entry Year'].astype(str)
                               + pdf['Entry Month'], 
                               format='%Y%b')
    pdf['MEH'] = meh[max_month_index:]
    
    
    # add predicted values 
    pdf['Predicted Billable'] = pdf['MEH'] * predicted_utilization
    pdf['Predicted Total'] = pdf['MEH'] * predicted_fte
    
    # append to idf
    idf = idf.append(pdf, ignore_index=True)
    idf.fillna(0, inplace=True)
    
    # populate predicted columns
    filt = idf['DT'] >= pd.to_datetime(pd.to_datetime('2020' + 'Apr', 
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
    filt = idf['DT'] >= pd.to_datetime(pd.to_datetime('2020' + 'Apr', 
                                                      format='%Y%b'))
    idf.loc[filt, 'Avg Utilization'] = (idf.loc[filt, 'Predicted Billable'].cumsum()
                                  / idf.loc[filt, 'MEH'].cumsum())
    idf.loc[filt, 'Avg FTE'] = (idf.loc[filt, 'Predicted Total'].cumsum()
                                  / idf.loc[filt, 'MEH'].cumsum())
                            
    print(idf)
        
    return idf, max_DT
