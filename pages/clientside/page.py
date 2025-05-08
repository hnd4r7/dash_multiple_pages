import dash
from dash import html, dcc, callback, Input, Output, callback_context, clientside_callback

dash.register_page(__name__, path="/clientside", name="ClientSide")

layout = html.Div(
    [
        html.Button("Button 1", id="btn1"),
        html.Button("Button 2", id="btn2"),
        html.Button("Button 3", id="btn3"),
        html.Div(id="log"),
    ]
)

clientside_callback(
    """
    function(){
        console.log(dash_clientside.callback_context);
        const triggered_id = dash_clientside.callback_context.triggered_id;
        return "triggered id: " + triggered_id
    }
    """,
    Output("log", "children"),
    Input("btn1", "n_clicks"),
    Input("btn2", "n_clicks"),
    Input("btn3", "n_clicks"),
)