"""functions for plotting in the utilization report"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np

sem_months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
                'Jan', 'Feb', 'Mar']
year_helper = [0] * 9 + [1] * 3
#TODO: calculate this rather than hard-code
meh = [176, 168, 176, 184, 168, 176, 176, 168, 184,
       168, 160, 184]

text_grey = '#5F5F5F'
light_grey = 'lightgrey'
green = 'green'

def plot_utilization(df, names, predict_input):
    # create date time column for easier sorting
    df['DT'] = pd.to_datetime(df['Entry Year'].astype(str)
                         + df['Entry Month'], 
                         format='%Y%b')
    # subset df by user
    idf = df[df['User Name'].isin(names)].copy()
    
    # average across users
    if len(names)>1:
        idf = idf.groupby(['DT', 'Entry Year', 'Entry Month']).mean()
        idf.reset_index(inplace=True)
    
    # calculated predicted values
    filt = idf['DT'] == idf['DT'].max()
    predicted_utilization = idf.loc[filt, 'Util to Date'].values[0]
    predicted_fte = idf.loc[filt, 'FTE to Date'].values[0]
    
    # update with predicted input
    # TODO: add button to clear value of predict_input
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
    
    # calculate averages
    #TODO: add Strategy Year column and loop through (breaks for older employees)
    filt = idf['DT'] >= pd.to_datetime(pd.to_datetime('2020' + 'Apr', 
                                                      format='%Y%b'))
    idf.loc[filt, 'Predicted Billable'] = idf.loc[filt, 'Predicted Billable'] + idf.loc[filt, 'Billable']
    idf.loc[filt, 'Predicted Total'] = idf.loc[filt, 'Predicted Total'] + idf.loc[filt, 'Total']
    idf.loc[filt, 'Avg Utilization'] = (idf.loc[filt, 'Predicted Billable'].cumsum()
                                  / idf.loc[filt, 'MEH'].cumsum())
    idf.loc[filt, 'Avg FTE'] = (idf.loc[filt, 'Predicted Total'].cumsum()
                                  / idf.loc[filt, 'MEH'].cumsum())
                                  
    print(idf)
    
    # create figure
    fig = go.Figure()
    
    # actual filt
    filt = idf['DT'] <= max_DT
    
    # add trace for average, show predicted on hover
    fig.add_trace(go.Scatter(
        y=idf['Avg Utilization'],
        x=idf['DT'],
        name='Average Utilization',
        line=dict(color=green, shape='spline'),
        mode='lines',
        hovertemplate='%{y:%f}'
    ))
    
    # add trace for predicted meh
    fig.add_trace(go.Scatter(
        y=idf['Avg FTE'],
        x=idf['DT'],
        name='Average FTE',
        line=dict(color=light_grey, shape='spline'),
        mode='lines',
        hovertemplate='%{y:%f}'
    ))
    
    # add trace for actual
    fig.add_trace(go.Scatter(
        y=idf.loc[filt, 'Util to Date'],
        x=idf.loc[filt, 'DT'],
        name='Predicted Utilization',
        line=dict(color=green, shape='spline'),
        mode='markers+text',
        text=idf['Util to Date'],
        textposition='top right',
        texttemplate='%{y:%f}',
        hoverinfo='skip'
    ))
    
    # add trace for MEH
    fig.add_trace(go.Scatter(
        y=idf.loc[filt, 'FTE to Date'],
        x=idf.loc[filt, 'DT'],
        name='MEH',
        line=dict(color='darkgrey', shape='spline'),
        mode='markers+text',
        text=idf['Util to Date'],
        textposition='top right',
        texttemplate='%{y:%f}',
        hoverinfo='skip'
    ))
    
    # add 'x' for this month's actuals
    filt = idf['DT'] == max_DT
    fig.add_trace(go.Scatter(
        y=idf.loc[filt, 'Utilization'],
        x=idf.loc[filt, 'DT'],
        name='Utilization Actual',
        mode='markers',
        marker=dict(symbol='x-thin', 
                    line=dict(color=green, width=1)),
        hovertemplate='%{y:%f}',
        line_color=green
    ))
    
    fig.add_trace(go.Scatter(
        y=idf.loc[filt, 'FTE'],
        x=idf.loc[filt, 'DT'],
        name='FTE Actual',
        mode='markers',
        marker=dict(symbol='x-thin', 
                    line=dict(color='darkgrey', width=1)),
        hovertemplate='%{y:%f}',
        line_color='darkgrey'
    ))
    
    # Update layout
    fig.update_layout(plot_bgcolor='white',
                      xaxis_showgrid=False,
                      yaxis_showgrid=False)
    
    # Update yaxes
    fig.update_yaxes(rangemode='tozero',
                     tickformat='%')
    
    # Update xaxes
    fig.update_xaxes(range=[(pd.to_datetime('2020' + 'Mar' + '26', format='%Y%b%d')),
                            pd.to_datetime('2021' + 'Mar', format='%Y%b')],
                     nticks=12,
                     tickformat='%b<br>%Y',
                     linecolor=light_grey
    )
    
    # Add space for Predicted Annotation
    fig.update_layout(margin=dict(r=150,pad=4))
                      
    # Add predicted utilization annotation
    filt = idf['DT'] == pd.to_datetime('2021' + 'Mar', format='%Y%b')
    predict_display = idf.loc[filt, 'Avg Utilization'].values[0]
    predict_text = f'Predicted<br>Utilization ({predict_display*100:.0f}%)'
    fig.add_annotation(x=pd.to_datetime('2021' + 'Mar', format='%Y%b'),
                       y=predict_display,
                       text=predict_text,
                       xanchor='left',
                       yanchor='middle',
                       xshift=10,
                       showarrow=False,
                       align='left'
    )
    
    # Update font
    fig.update_layout(font=dict(family='Gill Sans MT, Arial', 
                                size=14, color=text_grey))
    
    # Remove legend
    fig.update_layout(showlegend=False)
    
    return fig


if __name__=='__main__':
    import pygsheets
    
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
    
    client = auth_gspread()
    df = load_report(client, 'Utilization-Hours', 'Utilization-Hours-2')
    plot_utilization(df, 'Anderson, Erik')
    fig.show()
    
    
