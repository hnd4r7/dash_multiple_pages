import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path="/", name="Home")

layout = html.Div([
    html.H1("Home Page"),
    dcc.Dropdown(
        id="analytics-input",  # Same ID as in page1.py
        options=['Paris', 'Berlin', 'Madrid'],
        value='Paris'
    ),
    html.Br(),
    html.Div(id="analytics-output")  # Same ID as in page1.py
])

@callback(
    Output("analytics-output", "children"),
    Input("analytics-input", "value")
)
def update_output(value):
    return f"You selected: {value}"