import dash
import os
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
        return {k: f"{prefix}{prefix_sep}{v}" if k == "type" else v for k, v in component_id.items()}
    else:
        return component_id


def component_key(component_id) -> str:
    return (
        component_id
        if isinstance(component_id, str)
        else (component_id["type"] if isinstance(component_id, dict) else str(component_id))
    )


def find_call_module():
    """Find the frame before dependencies.py to get the callback's directory."""
    frame = inspect.currentframe()
    while frame:
        call_location = os.path.normcase(frame.f_code.co_filename)
        cwd = os.path.normcase(os.getcwd())
        if call_location.startswith(cwd):
            module_name = os.path.splitext(os.path.relpath(call_location, start=cwd))[0].replace(os.sep, ".")
            if module_name and not module_name == __name__:
                package_name, _, _ = module_name.rpartition(".")  # TODO contains 2 package level at most
                return package_name
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

original_component_init = dash.development.base_component.Component.__init__


@wraps(original_component_init)
def patched_component_init(self, **kwargs):
    original_component_init(self, **kwargs)
    if hasattr(self, "id") and self.id:
        # if component_key(self.id) not in callback_component_ids:
        #     # TODO: If new component are added by set_props, it's id will not be registered in callback_component_ids since there is no Input | State | Output call.
        #     return
        prefix = get_prefix_by_call_module()
        if not prefix:
            return
        if isinstance(self.id, str) and self.id in skip_component_ids:
            return
        prefix_component_id = prefix_component(prefix, self.id)
        print(f"Prefixing layout component_id -> {prefix_component_id}")
        self.id = prefix_component_id
        # we cannot add prefix for certain html component like login-button. it may corrupt the css style.
        # callback_component_id may be something like {type: xxx, index: <ALL>}, we need to match {type: xxx, index: 1} or {type: xxx, index: 2}...


dash.development.base_component.Component.__init__ = patched_component_init

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
                    k: (v[v.index(prefix_sep) + len(prefix_sep) :] if isinstance(v, str) and prefix_sep in v else v)
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


original_callback_set_props = dash._callback_context.CallbackContext.set_props


@wraps(original_callback_set_props)
def patched_callback_set_props(self, component_id: typing.Union[str, dict], props: dict):
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
