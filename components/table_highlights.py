
"""https://dash.plotly.com/datatable/conditional-formatting"""

import dash_html_components as html
import colorlover
from components.functions import get_month_fte, sem_months, year_helper, decalc_allocation_data
import numpy as np


def discrete_background_color_bins(df, semester, n_bins=5):
    col = [col for col in df.columns if col in ['Project', 'User Name']][0]
    filt = df[col] != 'Total'
    dff = df.loc[filt]
    df_numeric_columns = dff[[month for month in dff.columns if month in sem_months]]
    
    sy = semester.split('|')[1].strip()
    base_year = int(sy[:4])
    sem_years = [base_year + helper for helper in year_helper]
    
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Greys'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        # conditional format project hours
        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
            
        # # add legend
        # legend.append(
        #     html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
        #         html.Div(
        #             style={
        #                 'backgroundColor': backgroundColor,
        #                 'borderLeft': '1px rgb(50, 50, 50) solid',
        #                 'height': '10px'
        #             }
        #         ),
        #         html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
        #     ])
        # )
    
    # conditional format total row
    
    # don't conditional format for Project view
    if col == 'Project':
        for column in df_numeric_columns:
            month_idx = sem_months.index(column)
            year = sem_years[month_idx]        
            fte_hours = get_month_fte(column, year)
            fte_bounds = [x * fte_hours for x in [0, 1, 1.1, 1.2]]
            colors = ['#fff', '#02b875', '#f0ad4e', '#d9534f']
            
            # apply conditional formatting for total row
            for bound, backgroundColor in zip(fte_bounds, colors):
                styles.append(
                    {'if':{
                            'filter_query': (
                                '{{{col}}} = Total && {{{column}}} >= {bound}'
                            ).format(col=col, column=column, bound=bound),
                            'column_id': column
                        },
                        'backgroundColor': backgroundColor,
                        'color': 'black'}
                )
    
    elif col == 'User Name':
        vals = df_numeric_columns.sum(axis=0)
        bin_max = vals.max()
        bin_min = vals.min()
        val_bounds = np.linspace(bin_min, bin_max, n_bins)
        for column in df_numeric_columns:
            for idx, bound in enumerate(val_bounds):
                backgroundColor = colorlover.scales[str(n_bins)]['seq']['Greens'][idx]
                color = 'white' if idx > n_bins/2. else 'inherit'
                styles.append(
                    {'if':{
                            'filter_query': (
                                '{{{col}}} = Total && {{{column}}} >= {bound}'
                            ).format(col=col, column=column, bound=bound),
                            'column_id': column
                        },
                        'backgroundColor': backgroundColor,
                        'color': color}
                )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))