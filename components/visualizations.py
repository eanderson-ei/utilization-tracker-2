"""functions for plotting in the utilization report"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import webcolors
from components import utils 


text_grey = '#5F5F5F'
light_grey = 'lightgrey'
green = 'green'


def plot_utilization(df, name, predict_input):
    # subset df and entries by user
    idf = df[df['User Name'] == name].copy()
    idf, max_DT = utils.predict_utilization(idf, predict_input)
        
    # create figure
    fig = go.Figure()
    
    # actual filt
    filt = idf['DT'] <= max_DT

    # show breakdown by class
    colors = {'Billable': '#229954', 
                'R&D': '#F27C22', 
                'G&A': '#909497', 
                'Marketing & NBD': '#2E9DCD', 
                'Overhead': '#1F73AE',
                'Time Off': '#F1C40F',
                'None': '#333333'}
    
    for classifier in ['Billable', 'R&D', 'G&A', 'Marketing & NBD', 
                        'Overhead', 'Time Off', 'None']:
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
    for sy in idf['Strategy Year'].unique():
        filt = idf['Strategy Year'] == sy
        dff = idf.loc[filt]
        fig.add_trace(go.Scatter(
            y=dff['Avg Utilization'],
            x=dff['DT'],
            name='Average Utilization',
            line=dict(color=green, shape='spline'),
            mode='lines',
            hovertemplate='%{y:%f}',
            showlegend=False
        ))
    
        # add trace for predicted meh
        fig.add_trace(go.Scatter(
            y=dff['Avg FTE'],
            x=dff['DT'],
            name='Average FTE',
            line=dict(color=light_grey, shape='spline'),
            mode='lines',
            hovertemplate='%{y:%f}',
            showlegend=False
        ))
    
        # add trace for actual
        fig.add_trace(go.Scatter(
            y=dff.loc[filt, 'Util to Date'],
            x=dff.loc[filt, 'DT'],
            name='Predicted Utilization',
            line=dict(color=green, shape='spline'),
            mode='markers+text',
            text=dff['Util to Date'],
            textposition='top right',
            texttemplate='%{y:%f}',
            hoverinfo='skip',
            cliponaxis=False,
            showlegend=False
        ))
    
        # add trace for MEH
        fig.add_trace(go.Scatter(
            y=dff.loc[filt, 'FTE to Date'],
            x=dff.loc[filt, 'DT'],
            name='MEH',
            line=dict(color='darkgrey', shape='spline'),
            mode='markers+text',
            text=dff['Util to Date'],
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
    fig.update_xaxes(range=[(pd.to_datetime('2021' + 'Mar' + '26', format='%Y%b%d')),  #TODO
                            pd.to_datetime('2022' + 'Mar', format='%Y%b')],
                     nticks=12,
                     tickformat='%b<br>%Y',
                     linecolor=light_grey,
                    #  fixedrange=True
    )
    
    # Add space for Predicted Annotation
    fig.update_layout(margin=dict(l=10, r=150, t=20, pad=4))
                      
    # Add predicted utilization annotation
    filt = idf['DT'] == pd.to_datetime('2022' + 'Mar', format='%Y%b')  #TODO
    predicted = idf.loc[filt, 'Avg Utilization']
    if not predicted.empty:
        predict_display = predicted.values[0]
        predict_text = f'Predicted<br>Utilization ({predict_display*100:.0f}%)'
        fig.add_annotation(x=pd.to_datetime('2022' + 'Mar', format='%Y%b'),
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
    
    return fig


def plot_projects(df, name, start_date, end_date, mode, project=None):
    # subset df and entries by user
    idf = df[df['User Name'] == name].copy()
    meh = utils.get_meh_from_entries(idf, start_date, end_date)
    bar_width = .7
    fig = go.Figure()

    if mode == 'Projects':
        project_totals = utils.get_project_totals(idf, start_date, end_date)

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
        task_totals = utils.get_task_totals(idf, start_date, end_date, project)
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
    
    # Add fte annotation
    for idx, hours in enumerate(bars):
        if hours > 0:
            fig.add_annotation(
                x=hours, y=idx,
                xanchor='left',
                text=f'{hours/meh:.0%}',
                font_color=text_grey,
                showarrow=False
            )

    # Update layout
    num_bars = len(bars)
    bottom_margin = 200 if num_bars < 5 else 80
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


def plot_team(df, project, start_date, end_date, mode, user=None):
    # subset df and entries by user
    pdf = df[df['Project'] == project].copy()
    bar_width = .7
    fig = go.Figure()

    if mode == 'Users':
        user_totals = utils.get_user_totals(pdf, start_date, end_date)

        fig.add_traces(go.Bar(
            x=user_totals,
            y=user_totals.index,
            name='Users',
            orientation = 'h',
            width=bar_width,
            showlegend=False
        ))

        bars = user_totals

    elif mode == 'Tasks':
        user_task_totals = utils.get_user_task_totals(pdf, start_date, end_date, user)

        fig.add_traces(go.Bar(
            x=user_task_totals,
            y=user_task_totals.index,
            name='Tasks',
            orientation = 'h',
            width=bar_width,
            showlegend=False
        ))

        bars = user_task_totals

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
    bottom_margin = 200 if num_bars < 5 else 80
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