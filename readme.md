# Motivation
Dash operates as a Single-Page Application (SPA), meaning the entire application runs within a single browser page, and page navigation typically involves dynamically updating the content of a container (e.g., page-content or dash.page_container) without a full page reload.

The multi-app pattern was never officially documented or supported.

One solution is add prefix to both layout and callback automatically by monkey patching dash internals.

Since the component id are used inside the source code , we must unprefix it before it came out of dash internal code, but we must also keep it unique across the whole python process, so there is no way we can came up with a perfect dropin replacement.
- replace @dash with @section
: what ever you do inside the decorator, the hard-coded component id inside the source code canot be changed.


Duplicate Callback Output:
Callbacks Are Shared Across Pages! If there is duplicate component and a callback references the duplicate component and is active across multiple pages, it may behave unexpectedly because Dash won't know which to target when the callback is triggered.
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

Ref:
we must split those apps into different process if we want to isolate dash apps because dash have a few global pkg-dependent states registered inside the global state like dash._callback.GLOBAL_CALLBACK_LIST and dash._callback.GLOBAL_CALLBACK_MAP.
https://github.com/plotly/dash/issues/2812
https://github.com/mckinsey/vizro/issues/109#issuecomment-1765733474
- All In One compoennt
https://dash.plotly.com/all-in-one-components
- dash-building-block
id=self.register('dropdown'),
https://dash-building-blocks.readthedocs.io/en/latest/motivation.html