"""Helpers for setting Polarion custom fields through pylero's public path.

pylero builds a validating, batching setter for each custom field as a *property*
on the dynamic, type-specific subclasses of ``_SpecificWorkItem`` it generates at
import time (one per work-item type). The base ``_WorkItem`` has none of these
properties and no public ``set_custom_field`` -- only the private
``_set_custom_field``, which fires one ``setCustomField`` SOAP call per field (a
separate SVN revision each) and skips the enum validation / value wrapping (e.g.
``Text(html)``) that the property setter performs.

Assigning a custom field on the *base* ``_WorkItem`` therefore does nothing
useful: the name is not a property, so it is stored as a dead instance attribute
and silently dropped by the SOAP layer. These helpers locate the right
type-specific class and translate a custom-field id -- as reported by
``get_custom_fields`` / Polarion (e.g. ``userStory``) -- to pylero's snake_cased
property name (e.g. ``user_story``), so callers can ``setattr`` the field and let
the property setter validate, wrap, and batch it into a single ``update()``.
"""

from __future__ import annotations

from pylero.work_item import _WorkItem


def type_specific_class(wi_type) -> type:
    """Return the pylero ``_SpecificWorkItem`` subclass whose ``_wi_type`` matches.

    Only these subclasses carry the per-custom-field properties. ``wi_type`` may
    be a plain type id (``"testcase"``) or an enum object exposing ``.id``.
    """
    wi_type = getattr(wi_type, "id", None) or wi_type
    candidates = _WorkItem.get_defined_work_item_types()
    for cls in candidates:
        if getattr(cls, "_wi_type", None) == wi_type:
            return cls
    known = ", ".join(sorted(c._wi_type for c in candidates if getattr(c, "_wi_type", None)))
    raise ValueError(f"No pylero work-item class for type {wi_type!r}. Known types: {known}.")


def resolve_local_name(wi_or_cls, field_id: str) -> str:
    """Map a custom-field id (e.g. ``userStory``) to pylero's property name
    (e.g. ``user_story``). An already-snake_cased name is returned unchanged.

    The ``_cls_suds_map`` must already be populated for the work-item type, which
    happens when a type-specific instance is constructed or ``get_custom_fields``
    is called on its class.
    """
    suds_map = wi_or_cls._cls_suds_map
    for local, spec in suds_map.items():
        if isinstance(spec, dict) and spec.get("is_custom") and spec.get("field_name") == field_id:
            return local
    if field_id in suds_map:  # caller already passed the local name
        return field_id
    customs = ", ".join(
        f"{spec.get('field_name')} ({local})"
        for local, spec in suds_map.items()
        if isinstance(spec, dict) and spec.get("is_custom")
    )
    raise ValueError(
        f"Custom field {field_id!r} is not defined on this work-item type. "
        f"Known custom fields: {customs or '(none)'}."
    )
