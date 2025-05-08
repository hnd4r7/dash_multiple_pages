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

dash.register_page(__name__, path="/pattern-dyn", name="pattern-dyn")

layout = html.Div(
    [
        html.Button("Add Filter", id="add-filter-btn", n_clicks=0),
        html.Div(id="dropdown-container-div", children=[]),
        html.Div(id="dropdown-container-output-div"),
    ]
)


@callback(
    Output("dropdown-container-div", "children"), Input("add-filter-btn", "n_clicks")
)
def display_dropdowns(n_clicks):
    patched_children = Patch()
    new_dropdown = dcc.Dropdown(
        ["NYC", "MTL", "LA", "TOKYO"],
        id={"type": "city-filter-dropdown", "index": n_clicks},
    )
    patched_children.append(new_dropdown)
    return patched_children


@callback(
    Output("dropdown-container-output-div", "children"),
    Input({"type": "city-filter-dropdown", "index": ALL}, "value"),
)
def display_output(values):
    print(callback_context.triggered_id)
    return html.Div(
        [html.Div(f"Dropdown {i + 1} = {value}") for (i, value) in enumerate(values)]
    )
