# TODO
- css style: id selector

- client-side callback
https://dash.plotly.com/clientside-callbacks#callback-context
dash_clientside.set_props

- dynamically created components
```python
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
```