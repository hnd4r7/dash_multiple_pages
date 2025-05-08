import logging
import dash
from dash import _pages, dependencies
from dash._callback_context import  CallbackContext
from typing import Dict, Any
from dash.dash import _ID_CONTENT,_ID_LOCATION, _ID_STORE, _ID_DUMMY
import inspect

logger = logging.getLogger(__name__)
callback_component_ids = set()
all_prefixs = set()
skip_package_prefixs = ["", "."]
skip_component_ids = {"url", _ID_CONTENT,_ID_LOCATION, _ID_STORE, _ID_DUMMY}

def prefix_component(prefix: str, component_id):
    if isinstance(component_id, str):
        if component_id in skip_component_ids:
            return component_id
        return f"{prefix}_{component_id}"
    elif isinstance(component_id, dict):
        return {k: f"{prefix}_{v}" if k == "type" else v for k, v in component_id.items()} 
    else:
        return component_id

def prefix_layout_ids(component, prefix, processed_components=None):
    """Recursively prefix IDs in a Dash component tree."""
    if processed_components is None:
        processed_components = set()

    component_obj_id = id(component)
    if component_obj_id in processed_components:
        return
    
    processed_components.add(component_obj_id)

    if hasattr(component, 'id') and component.id:
        prefix_component_id = prefix_component(prefix, component.id)
        logger.debug(f"Prefixing layout component_id -> {prefix_component_id}")
        #we cannot add prefix for certain html component like login-button. it may corrupt the css style.
        if str(prefix_component_id) in callback_component_ids:
            component.id = prefix_component_id
    if hasattr(component, 'children'):
        if isinstance(component.children, list):
            for child in component.children:
                if child is not None:
                    prefix_layout_ids(child, prefix, processed_components)
        elif component.children is not None:
            prefix_layout_ids(component.children, prefix, processed_components)

def find_callback_prefix():
    """Find the frame before dependencies.py to get the callback's directory."""
    frame = inspect.currentframe()
    while frame:
        if "__package__" in frame.f_locals:
            page_module_name = frame.f_locals.get('__package__')
            if page_module_name is None:
                return None
            prefix =  page_module_name.replace(".", "_")
            if not prefix or prefix == "_":
                return None
            else:
                return prefix
        frame = frame.f_back
    return None

def patched_dash_dependency_init(self, component_id, component_property):
    """Patched DashDependency.__init__ to prefix callback component_id."""
    prefix = find_callback_prefix()
    # dash builtin callback will return prefix == None. eg. _pages_location.
    if prefix is None or prefix in skip_package_prefixs:
        original_dash_dependency_init(self, component_id, component_property) 
        return
    all_prefixs.add(prefix)
    prefix_component_id = prefix_component(prefix, component_id)
    callback_component_ids.add(str(prefix_component_id))
    logger.debug(f"Prefixing callback component_id -> {prefix_component_id}")
    original_dash_dependency_init(self, prefix_component_id, component_property)

def patched_import_layouts_from_pages(pages_folder=None):
    """Patched _import_layouts_from_pages to prefix layout IDs."""
    original_import_layouts_from_pages(pages_folder) # page modules initialized, callback already registered.
    for module, registry_entry in _pages.PAGE_REGISTRY.items():
        prefix = "_".join(module.split(".")[:-1])
        if prefix in skip_package_prefixs:
            continue 
        logger.debug(f"Generated prefix for module {module}: {prefix}")

        layout = registry_entry.get('layout')
        if layout:
            if callable(layout):
                layout = layout()
            if layout is not None:
                prefix_layout_ids(layout, prefix)
            registry_entry['layout'] = layout
            logger.debug(f"Prefixed layout for module {module}")

# Save original functions
original_dash_dependency_init = dependencies.DashDependency.__init__
original_import_layouts_from_pages = dash.dash._import_layouts_from_pages

# Apply monkey patches
dependencies.DashDependency.__init__ = patched_dash_dependency_init
dash.dash._import_layouts_from_pages = patched_import_layouts_from_pages