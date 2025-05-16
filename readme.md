# Motivation
Dash operates as a Single-Page Application (SPA), meaning the entire application runs within a single browser page, and page navigation typically involves dynamically updating the content of a container (e.g., page-content or dash.page_container) without a full page reload.

Duplicate Callback Output:
Callbacks Are Shared Across Pages! If a callback references the avatar-name component and is active across multiple pages, it may behave unexpectedly because Dash won't know which avatar-name to target when the callback is triggered.
In this repo, pages/home and pages/analytics contains duplicate callback output id, thus causing conflicts.

Duplicate layout ID:
In a multi-page Dash app, only the components of the currently active page are rendered in the layout at any given time. Components from other pages are not part of the active DOM (Document Object Model) unless explicitly loaded. Since Dash validates component IDs for uniqueness only within the currently rendered layout, duplicate IDs across different pages do not trigger a Duplicate ID error. When you navigate to a new page, the previous page's components are removed from the layout, and the new page's components are rendered. As a result, Dash never sees multiple components with the same ID simultaneously in the active layout.
In this repo, pages/home and pages/analytics contains duplicate layout id, but that will not be a problem because they are rendered on different pages. 
If you move the duplicate callback to a single module, like app.py, those two pages will works fine.


# TODO
## Frontend
- css style: id selector

- client-side callback
https://dash.plotly.com/clientside-callbacks#callback-context
client_side callback trigger_id need to handled manually (remove the prefix)
dash_clientside.set_props


## Backend
- component ID
 _id = stringify_id(component_id)

- callback_context set_props
    - If new component are added by set_props. 

- background=True