import dash
from dash import (
    Dash,
    html,
    dcc,
    ALL,
    Patch,
    callback,
    Input,
    Output,
    callback_context,
    clientside_callback,
)

dash.register_page(__name__, path="/pattern", name="pattern")

layout = html.Div(
    [
        dcc.Dropdown(
            ["NYC", "MTL", "LA", "TOKYO"],
            id={"type": "city-filter-dropdown", "index": 1},
        ),
        dcc.Dropdown(
            ["NYC", "MTL", "LA", "TOKYO"],
            id={"type": "city-filter-dropdown", "index": 2},
        ),
        html.Div(id="dropdown-container-output-div"),
    ]
)


@callback(
    Output("dropdown-container-output-div", "children"),
    Input({"type": "city-filter-dropdown", "index": ALL}, "value"),
)
def display_output(values):
    print(callback_context.triggered_id)
    return html.Div(
        [html.Div(f"Dropdown {i + 1} = {value}") for (i, value) in enumerate(values)]
    )
