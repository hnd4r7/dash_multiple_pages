import dash
import copy
from dash import _pages, dependencies
import json
from dash import _callback
from typing import Dict, Any
from dash.dash import _ID_CONTENT, _ID_LOCATION, _ID_STORE, _ID_DUMMY
from dash._utils import to_json
from functools import wraps
import inspect

callback_component_ids = set()
skip_package_prefixs = ["", "."]
skip_component_ids = {"url", _ID_CONTENT, _ID_LOCATION, _ID_STORE, _ID_DUMMY}
prefix_sep = "||"


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


def prefix_component_key(prefix_component_id) -> str:
    return (
        prefix_component_id
        if isinstance(prefix_component_id, str)
        else prefix_component_id["type"]
    )


def prefix_layout_ids(component, prefix):
    """Recursively prefix IDs in a Dash component tree."""
    if hasattr(component, "id") and component.id:
        prefix_component_id = prefix_component(prefix, component.id)
        print(f"Prefixing layout component_id -> {prefix_component_id}")
        # we cannot add prefix for certain html component like login-button. it may corrupt the css style.
        # callback_component_id may be something like {type: xxx, index: <ALL>}, we need to match {type: xxx, index: 1} or {type: xxx, index: 2}...
        if prefix_component_key(prefix_component_id) in callback_component_ids:
            component.id = prefix_component_id
    if hasattr(component, "children"):
        if isinstance(component.children, list):
            for child in component.children:
                if child is not None:
                    prefix_layout_ids(child, prefix)
        elif component.children is not None:
            prefix_layout_ids(component.children, prefix)


# def find_call_module():
#     """Find the frame before dependencies.py to get the callback's directory."""
#     frame = inspect.currentframe()
#     while frame:
#         call_m = inspect.getmodule(frame)
#         print("call_m", call_m)
#         if "__name__" in frame.f_locals and frame.f_locals["__name__"].startswith(
#             page_parent_module
#         ):
#             print("page_module_name", call_m)
#             page_module_name, _, _ = frame.f_locals["__name__"].rpartition(".")
#             return page_module_name
#         frame = frame.f_back
#     return None


def find_call_module():
    """Find the frame before dependencies.py to get the callback's directory."""
    frame = inspect.currentframe()
    while frame:
        # TODO: __package__ is not reliable.
        if "__package__" in frame.f_locals:
            page_module_name = frame.f_locals.get("__package__")
            if page_module_name is None:
                return None
            return page_module_name
        frame = frame.f_back
    return None


def patched_dash_dependency_init(self, component_id, component_property):
    """Patched DashDependency.__init__ to prefix callback component_id."""
    page_module_name = find_call_module()
    # dash builtin callback will return prefix == None. eg. _pages_location.
    if (
        not page_module_name
        or page_module_name == "."
        or page_module_name in skip_package_prefixs
    ):
        original_dash_dependency_init(self, component_id, component_property)
        return
    prefix = page_module_name.replace(".", "_")
    prefix_component_id = prefix_component(prefix, component_id)
    callback_component_ids.add(prefix_component_key(prefix_component_id))
    print(f"Prefixing callback component_id -> {prefix_component_id}")
    original_dash_dependency_init(self, prefix_component_id, component_property)


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


# Save original functions
original_dash_dependency_init = dependencies.DashDependency.__init__
original_import_layouts_from_pages = dash.dash._import_layouts_from_pages

# Apply monkey patches
dependencies.DashDependency.__init__ = patched_dash_dependency_init
dash.dash._import_layouts_from_pages = patched_import_layouts_from_pages

original_get_context_value = dash._callback_context._get_context_value


@wraps(original_get_context_value)
def patched_get_context_value():
    ctx = original_get_context_value()
    # page_module_name = find_call_module()
    # if not page_module_name:  # It's called by dash itself. Skip in this case.
    #     return ctx

    triggered = getattr(ctx, "triggered_inputs", [])
    items = []
    module_dir = None
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
                        v[v.index(prefix_sep) + 1 :]
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
            if k == "id":
                m[k] = prefix_component(prefix, v)
            elif isinstance(v, dict):
                prefix_resp(v, prefix)
            elif isinstance(v, list):
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
