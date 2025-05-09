import dash
import typing
from dash import _pages, dependencies
import json
from dash.dash import _ID_CONTENT, _ID_LOCATION, _ID_STORE, _ID_DUMMY
from functools import wraps
import inspect

callback_component_ids = set()
skip_package_prefixs = ["", "."]
skip_component_ids = {"url", _ID_CONTENT, _ID_LOCATION, _ID_STORE, _ID_DUMMY}
prefix_sep = "||"
pages_root_module = "pages"


def prefix_component(prefix: str, component_id):
    if isinstance(component_id, str):
        if component_id in skip_component_ids:
            return component_id
        return f"{prefix}{prefix_sep}{component_id}"
    elif isinstance(component_id, dict):
        return {
            k: f"{prefix}{prefix_sep}{v}" if k == "type" else v
            for k, v in component_id.items()
        }
    else:
        return component_id


def component_key(component_id) -> str:
    return (
        component_id
        if isinstance(component_id, str)
        else (
            component_id["type"]
            if isinstance(component_id, dict)
            else str(component_id)
        )
    )


def prefix_layout_ids(component, prefix):
    """Recursively prefix IDs in a Dash component tree."""
    if hasattr(component, "id") and component.id:
        if component_key(component.id) not in callback_component_ids:
            # TODO: If new component are added by set_props, it's id will not be registered in callback_component_ids since there is no Input | State | Output call.
            return
        prefix_component_id = prefix_component(prefix, component.id)
        print(f"Prefixing layout component_id -> {prefix_component_id}")
        component.id = prefix_component_id
        # we cannot add prefix for certain html component like login-button. it may corrupt the css style.
        # callback_component_id may be something like {type: xxx, index: <ALL>}, we need to match {type: xxx, index: 1} or {type: xxx, index: 2}...
    if hasattr(component, "children"):
        if isinstance(component.children, list):
            for child in component.children:
                if child is not None:
                    prefix_layout_ids(child, prefix)
        elif component.children is not None:
            prefix_layout_ids(component.children, prefix)


def find_call_module():
    # frame = inspect.currentframe()
    # while frame:
    #     m = inspect.getmodule(frame)
    #     # if module name is None, it means we're executing the module in dash._pages, the module initialization is not finished
    #     if m is not None and m.__name__ is not None:
    #         print(m.__name__)
    #     frame = frame.f_back

    """Find the frame before dependencies.py to get the callback's directory."""
    frame = inspect.currentframe()
    while frame:
        m = inspect.getmodule(frame)
        # if module name is None, it means we're executing the module in dash._pages, the module initialization is not finished
        pkg = None
        if m is None or m.__name__ is None:
            if "__package__" in frame.f_locals:
                return frame.f_locals.get("__package__")
            pkg = ".".join(frame.f_locals.get("__name__").split(".")[:-1])
            return pkg
        if m.__name__.startswith(pages_root_module):
            pkg = m.__name__
            return pkg
        frame = frame.f_back
    return None


def get_prefix_by_call_module():
    page_module_name = find_call_module()
    # dash builtin callback will return prefix == None. eg. _pages_location.
    if not page_module_name or page_module_name in skip_package_prefixs:
        return None
    prefix = page_module_name.replace(".", "_")
    return prefix


original_dash_dependency_init = dependencies.DashDependency.__init__


@wraps(original_dash_dependency_init)
def patched_dash_dependency_init(self, component_id, component_property):
    """Patched DashDependency.__init__ to prefix callback component_id."""
    if isinstance(component_id, str) and component_id in skip_component_ids:
        original_dash_dependency_init(self, component_id, component_property)
        return
    prefix = get_prefix_by_call_module()
    if not prefix:
        original_dash_dependency_init(self, component_id, component_property)
        return
    callback_component_ids.add(component_key(component_id))
    prefix_component_id = prefix_component(prefix, component_id)
    print(f"Prefixing callback component_id -> {prefix_component_id}")
    original_dash_dependency_init(self, prefix_component_id, component_property)


# Apply monkey patches
dependencies.DashDependency.__init__ = patched_dash_dependency_init

original_import_layouts_from_pages = dash.dash._import_layouts_from_pages


def patched_import_layouts_from_pages(pages_folder=None):
    """Patched _import_layouts_from_pages to prefix layout IDs."""
    original_import_layouts_from_pages(
        pages_folder
    )  # page modules initialized, callback already registered.
    for module, registry_entry in _pages.PAGE_REGISTRY.items():
        pkg_module_name, _, _ = module.rpartition(".")
        if pkg_module_name in skip_package_prefixs:
            continue
        prefix = pkg_module_name.replace(".", "_")
        print(f"Prefixing layout for module {module}: {prefix}")

        layout = registry_entry.get("layout")
        if layout:
            if callable(layout):
                layout = layout()
            if layout is not None:
                prefix_layout_ids(layout, prefix)
            registry_entry["layout"] = layout


dash.dash._import_layouts_from_pages = patched_import_layouts_from_pages

original_get_context_value = dash._callback_context._get_context_value


@wraps(original_get_context_value)
def patched_get_context_value():
    ctx = original_get_context_value()
    # page_module_name = find_call_module()
    # if not page_module_name:  # It's called by dash itself. Skip in this case? May cause other problems
    #     return ctx

    triggered = getattr(ctx, "triggered_inputs", [])
    items = []
    for item in triggered:
        prefixed_prop_id: str = item["prop_id"]
        if prefixed_prop_id == ".":
            items.append(item)
            continue
        prefixed_id, _, prop = prefixed_prop_id.rpartition(".")
        if prefixed_id.startswith("{"):
            original_id = json.dumps(
                {
                    k: (
                        v[v.index(prefix_sep) + len(prefix_sep) :]
                        if isinstance(v, str) and prefix_sep in v
                        else v
                    )
                    for k, v in json.loads(prefixed_id).items()
                }
            )
        else:
            _, _, original_id = prefixed_id.rpartition(prefix_sep)
        original_prop_id = f"{original_id}.{prop}"
        items.append({"prop_id": original_prop_id, "value": item["value"]})

    ctx.triggered_inputs = items
    return ctx


dash._callback_context._get_context_value = patched_get_context_value


original_dispatch = dash.Dash.dispatch


# Patched:
# {"multi":true,"response":{"pages_pattern_dyn\\u002fdropdown-container-div":{"children":{"__dash_patch_update":"__dash_patch_update","operations":[{"operation":"Append","location":[],"params":{"value":{"props":{"options":["NYC","MTL","LA","TOKYO"],"id":{"type":"city-filter-dropdown","index":0}},"type":"Dropdown","namespace":"dash_core_components"}}}]}}}}
# Non-Patched:
# {"multi":true,"response":{"pages_pattern_dyn\\u002fdropdown-container-div":{"children":[{"props":{"options":["NYC","MTL","LA","TOKYO"],"id":{"type":"city-filter-dropdown","index":0}},"type":"Dropdown","namespace":"dash_core_components"}]}}}
def prefix_resp(m, prefix):
    if isinstance(m, dict):
        for k, v in m.items():
            if k == "id" and component_key(v) in callback_component_ids:
                m[k] = prefix_component(prefix, v)
            elif isinstance(v, dict):
                prefix_resp(v, prefix)
            elif isinstance(v, list) and k in ["children", "operations"]:
                for i in v:
                    prefix_resp(i, prefix)


@wraps(original_dispatch)
def patched_dispatch(self):
    """Patch Dash.dispatch to prefix component IDs in callback responses."""
    response = original_dispatch(self)

    # Deep copy the response to avoid modifying the original
    # response_copy = copy.deepcopy(response)
    response = response.json
    for k, v in response["response"].items():
        if prefix_sep not in k:
            continue
        prefix, _, _ = k.rpartition(prefix_sep)
        prefix_resp(v, prefix)
    # response.set_data(to_json(response))
    return response


# Apply the patch to Dash.dispatch
dash.Dash.dispatch = patched_dispatch

original_callback_set_props = dash._callback_context.CallbackContext.set_props


@wraps(original_callback_set_props)
def patched_callback_set_props(
    self, component_id: typing.Union[str, dict], props: dict
):
    """
    Set the props for a component not included in the callback outputs.
    """
    prefix = get_prefix_by_call_module()
    if not prefix:
        original_callback_set_props(self, component_id, props)
        return
    prefix_component_id = prefix_component(prefix, component_id)
    print(f"Prefixing set_props component_id -> {prefix_component_id}")
    original_callback_set_props(self, prefix_component_id, props)


dash._callback_context.CallbackContext.set_props = patched_callback_set_props
