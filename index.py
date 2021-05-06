import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# see https://community.plot.ly/t/nolayoutexception-on-deployment-of-multi-page-dash-app-example-code/12463/2?u=dcomfort
from app import server

from app import app
from layouts import layout_main, projects_layout, allocation_layout
import callbacks

# see https://dash.plot.ly/external-resources to alter header, footer and favicon
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Utilization Report</title>
        {%favicon%}
        {%css%}
        
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-151885346-2"></script>
        <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());

        gtag('config', 'UA-151885346-2');
        </script>

    </head>
    <body>
        <div></div>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <div></div>
    </body>
</html>
'''

# Layout placeholder
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='initial-state'),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return layout_main
    elif pathname == '/my_projects':
         return projects_layout
    elif pathname == '/allocation':
         return allocation_layout
    else:
        return '404'


if __name__ == '__main__':
    app.run_server(debug=False)