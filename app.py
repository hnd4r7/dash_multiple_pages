import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

import patch

app = dash.Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Create a simple navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page["name"], href=page["path"]))
        for page in dash.page_registry.values()
    ],
    brand="Multi-Page Dash App Demo",
    color="primary",
    dark=True,
)

# App layout
app.layout = dbc.Container(
    [
        navbar,
        dash.page_container
    ],
    fluid=True
)

if __name__ == "__main__":
    app.run(debug=True)