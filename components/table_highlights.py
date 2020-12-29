
"""https://dash.plotly.com/datatable/conditional-formatting"""

import dash_html_components as html
import colorlover
from components.functions import get_month_fte
import numpy as np

def discrete_background_color_bins(df, n_bins=5, columns='all'):
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[[col for col in columns if col in df.columns]]
    print(df_numeric_columns)
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
    col = [col for col in df.columns if col in ['Project', 'User Name']][0]
    # don't conditional format for Project view
    if col == 'Project':
        for column in df_numeric_columns:
            fte_hours = get_month_fte(column, 2020)
            fte_bounds = [x * fte_hours for x in [1, 1.1, 1.2]]
            colors = ['#02b875', '#f0ad4e', '#d9534f']
            
            # override project-scale conditional formatting
            styles.append(
                    {'if':{
                            'filter_query': (
                                '{{{col}}} = Total && {{{column}}} < {fte_hours}'
                            ).format(col=col, column=column, fte_hours=fte_hours),
                            'column_id': column
                        },
                        'backgroundColor': 'white',
                        'color': 'black'}
                )
            
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
        val_bounds = np.linspace(bin_min, bin_max, 5)
        for column in df_numeric_columns:
            for idx, bound in enumerate(val_bounds):
                backgroundColor = colorlover.scales[str(5)]['seq']['Greens'][idx]
                color = 'white' if idx > 5/2. else 'inherit'
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