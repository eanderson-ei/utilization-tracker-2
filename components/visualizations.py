"""functions for plotting in the utilization report"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import webcolors
from components import functions 


text_grey = '#5F5F5F'
light_grey = 'lightgrey'
green = 'green'


def plot_utilization(df, name, predict_input, entries,  # add month_class for project breakdown
                     breakdown=True):
    # subset df and entries by user
    idf = df[df['User Name'] == name].copy()
    # edf = month_class[month_class['User Name'] == name].copy()  # used for project breakdown
    
    print (name)
    
    idf, max_DT = functions.predict_utilization(idf, predict_input)
        
    # create figure
    fig = go.Figure()
    
    # actual filt
    filt = idf['DT'] <= max_DT
    
    if breakdown:
        # map colors with opacity
        # TODO: consider moving to functions, get_classification
        # def map_colors(df):
        #     colors = {'Billable': '#229954', 
        #             'R&D': '#F27C22', 
        #             'G&A': '#909497', 
        #             'Marketing & NBD': '#2E9DCD', 
        #             'Overhead': '#1F73AE',
        #             'Time Off': '#F1C40F'}
        #     df['color'] = df['Classification'].map(colors)
            # df['rgb'] = df['color'].map(webcolors.hex_to_rgb)
            # count_entries = df.groupby('Classification')['Project'].nunique()
            # df = df.merge(count_entries, left_on='Classification', right_index=True,
            #               suffixes=(None, '_count'))
            # df_list = []
            # for classifier in df['Classification'].unique():
            #     filt = df['Classification'] == classifier
            #     n_unique_projects = df.loc[filt, 'Project_count'].max()
            #     opacities = np.linspace(.8, .2, n_unique_projects)
            #     projects = df.loc[filt, 'Project'].unique()
            #     dff = pd.DataFrame({'Project': projects, 'opacity': opacities})
            #     df_list.append(dff)
            # odf = pd.concat(df_list)
            # df = df.merge(odf, on='Project')            
            
            
            # color_table = df['rgb'].apply(pd.Series)
            # color_table[3] = df['opacity']
            # color_table[4] = list(zip(color_table[0], 
            #                           color_table[1],
            #                           color_table[2],
            #                           color_table[3]))
            # color_table[5] = 'rbga' + color_table[4].astype(str)
            # df['fcolor'] = color_table[5]
            # df['fcolor'] = df['fcolor'].apply(lambda x: "".join(x.split())).astype(str)
            
            # return df
        
        # # show breakdown by class
        # filt1 = edf['DT'] <= max_DT
        # edf_filt = edf.loc[filt1, :].copy()
        # edf_filt = map_colors(edf_filt)
        # for classifier in ['Billable', 'R&D', 'G&A', 'Marketing & NBD', 
        #                    'Overhead', 'Time Off']:
        #     filt1 = edf_filt['Classification'] == classifier
        #     edf_filt_class = edf_filt.loc[filt1, :]
        #     if not edf_filt_class.empty:
        #         # get color
        #         color = edf_filt_class.loc[filt1, 'color'].unique()[0]
        #         fig.add_trace(go.Scatter(
        #             y=edf_filt_class.loc[filt1, 'FTE'],
        #             x=edf_filt_class.loc[filt1, 'DT'],
        #             name=classifier,
        #             mode='lines',
        #             line=dict(width=0, color=color),
        #             # fillcolor=color,
        #             fill='tonexty',
        #             stackgroup='classes',
        #             hoveron='fills', # fills not working
        #             hoverinfo='text+y',
        #             text=classifier,
        #             showlegend=True
        #             ))
        
        # show breakdown by class
        colors = {'Billable': '#229954', 
                    'R&D': '#F27C22', 
                    'G&A': '#909497', 
                    'Marketing & NBD': '#2E9DCD', 
                    'Overhead': '#1F73AE',
                    'Time Off': '#F1C40F'}
        
        for classifier in ['Billable', 'R&D', 'G&A', 'Marketing & NBD', 
                           'Overhead', 'Time Off']:
            # get color
            color = colors.get(classifier, '#000000')
            fig.add_trace(go.Scatter(
                y=idf.loc[filt, classifier]/idf.loc[filt, 'MEH'],
                x=idf.loc[filt, 'DT'],
                name=classifier,
                mode='lines',
                line=dict(width=0, color=color),
                # fillcolor=color,
                fill='tonexty',
                stackgroup='classes',
                hoveron='points', # fills not working
                hoverinfo='text+y',
                text=classifier,
                showlegend=True
                ))
    
    
    # add trace for average, show predicted on hover
    fig.add_trace(go.Scatter(
        y=idf['Avg Utilization'],
        x=idf['DT'],
        name='Average Utilization',
        line=dict(color=green, shape='spline'),
        mode='lines',
        hovertemplate='%{y:%f}',
        showlegend=False
    ))
    
    # add trace for predicted meh
    fig.add_trace(go.Scatter(
        y=idf['Avg FTE'],
        x=idf['DT'],
        name='Average FTE',
        line=dict(color=light_grey, shape='spline'),
        mode='lines',
        hovertemplate='%{y:%f}',
        showlegend=False
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
        hoverinfo='skip',
        cliponaxis=False,
        showlegend=False
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
        hoverinfo='skip',
        cliponaxis=False,
        showlegend=False
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
        line_color=green,
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        y=idf.loc[filt, 'FTE'],
        x=idf.loc[filt, 'DT'],
        name='FTE Actual',
        mode='markers',
        marker=dict(symbol='x-thin', 
                    line=dict(color='darkgrey', width=1)),
        hovertemplate='%{y:%f}',
        line_color='darkgrey',
        showlegend=False
    ))
    
    # add projects from entries table
    # TODO: Delete or fix
    
    # filt = edf['DT'] <= max_DT
    # edf_filt = edf.loc[filt, :].copy()
    # edf_filt = map_colors(edf_filt)
    # for classifier in ['Billable', 'R&D', 'G&A', 'Marketing & NBD', 'Overhead', 'Time Off']:
    #     filt = edf_filt['Classification'] == classifier
    #     edf_filt_class = edf_filt.loc[filt, :]
    #     for idx, project in enumerate(edf_filt_class['Project'].unique()):
    #         filt = edf_filt_class['Project'] == project
    #         # get color
    #         color = edf_filt_class.loc[filt, 'color'].unique()[0]
    #         fig.add_trace(go.Scatter(
    #             y=edf_filt_class.loc[filt, 'FTE'],
    #             x=edf_filt_class.loc[filt, 'DT'],
    #             legendgroup=classifier,
    #             name=classifier,
    #             mode='lines',
    #             line=dict(width=0, color=color),
    #             # fillcolor=color,
    #             fill='tonexty',
    #             stackgroup='projects',
    #             hoveron='points+fills', # fills not working
    #             hoverinfo='text+x+y',
    #             text=project,
    #             showlegend=[True if idx == 0 else False][0]
    #             ))
    
    
    
    
    
    # Update layout
    fig.update_layout(plot_bgcolor='white',
                      xaxis_showgrid=False,
                      yaxis_showgrid=False,
                      autosize=False,
                      height=500,
                      dragmode='pan'
                      )
    
    # Update yaxes
    fig.update_yaxes(rangemode='tozero',
                     tickformat='%',
                     range=[0,1.39],
                     fixedrange=True)
    
    # Update xaxes
    fig.update_xaxes(range=[(pd.to_datetime('2020' + 'Mar' + '26', format='%Y%b%d')),
                            pd.to_datetime('2021' + 'Mar', format='%Y%b')],
                     nticks=12,
                     tickformat='%b<br>%Y',
                     linecolor=light_grey,
                    #  fixedrange=True
    )
    
    
    
    # Add space for Predicted Annotation
    fig.update_layout(margin=dict(l=10, r=150, t=20, pad=4))
                      
    # Add predicted utilization annotation
    filt = idf['DT'] == pd.to_datetime('2021' + 'Mar', format='%Y%b')
    predicted = idf.loc[filt, 'Avg Utilization']
    if not predicted.empty:
        predict_display = predicted.values[0]
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
    
    if breakdown:
        # update legend and increase graph height and margins to accomodate with slider
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor='bottom',
                y=-0.4,
                xanchor='center',
                x=.5
                ),
            height=600,
            margin=dict(t=50)
        )
    
 
    # # Add Relayout button
    # fig.update_layout(
    #     updatemenus=[
    #         dict(
    #             type="buttons",
    #             buttons=[
    #                 dict(label="Refresh",
    #                      method='relayout',
    #                      args=["xaxes", dict(
    #                          range=[(pd.to_datetime('2020' + 'Mar' + '26', format='%Y%b%d')),
    #                         pd.to_datetime('2021' + 'Mar', format='%Y%b')],
    #                         nticks=12,
    #                      )])
    #             ]
    #         )
    #     ]
    # )
    # # Remove legend
    # fig.update_layout(showlegend=True)
    
    return fig


def plot_projects(df, name, start_date, end_date, mode, project=None):
    # subset df and entries by user
    idf = df[df['User Name'] == name].copy()
    
    bar_width = .7
    
    fig = go.Figure()
    
    if mode == 'Projects':
        project_totals = functions.get_project_totals(idf, start_date, end_date)

        fig.add_traces(go.Bar(
            x=project_totals,
            y=project_totals.index,
            name='Projects',
            orientation = 'h',
            width=bar_width,
            showlegend=False
        ))
        
        bars = project_totals
    
    elif mode == 'Tasks':
        task_totals = functions.get_task_totals(idf, start_date, end_date, project)
        task_totals
        
        fig.add_traces(go.Bar(
            x=task_totals,
            y=task_totals.index,
            name='Tasks',
            orientation = 'h',
            width=bar_width,
            showlegend=False
        ))
        
        bars = task_totals
    
    # Add hours annotation
    for idx, hours in enumerate(bars):
        if hours > 0:
            fig.add_annotation(
                x=0, y=idx,
                xanchor='right',
                text=f'{hours:,.1f}',
                font_color=text_grey,
                showarrow=False
            )
    
    # Update layout
    num_bars = len(bars)
    if num_bars < 5:
        bottom_margin = 200
    else: 
        bottom_margin = 80
        
    fig.update_layout(plot_bgcolor='white',
                      xaxis_showgrid=True,
                      yaxis_showgrid=False,
                      autosize=False,
                      height=(num_bars-1) * 40 + (60 + bottom_margin)
                      )
    
    # Add space for Calendar drop down
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=bottom_margin, pad=30))
    
    # Update font
    fig.update_layout(font=dict(family='Gill Sans MT, Arial', 
                                size=14, color=text_grey))
    
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
    # plot_utilization(df, 'Anderson, Erik')
    # fig.show()
    
    
