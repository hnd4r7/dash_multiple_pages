import dash
from dash import html, dcc, callback, Input, Output, callback_context

dash.register_page(__name__, path="/analytics", name="Analytics")

layout = html.Div([
    html.H1("Analytics Page"),
    dcc.Dropdown(
        id="analytics-input",
        options=['New York', 'London', 'Tokyo'],
        value='New York'
    ),
    html.Br(),
    html.Div(id="analytics-output")
])

@callback(
    Output("analytics-output", "children"),
    Input("analytics-input", "value")
)
def update_output(value):
    if callback_context.triggered_id == "analytics-input":
        return f"Triggered by input: {value}"
    return f"You selected: {value}"