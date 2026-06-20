"""Search-before-create helpers keyed by natural keys from the project spec."""
from __future__ import annotations


def render_vals(template: dict, i: int) -> dict:
    """Render a vals template, substituting {i} (and format specs) in string values."""
    out = {}
    for k, v in template.items():
        if isinstance(v, str) and "{" in v:
            out[k] = v.format(i=i)
        else:
            out[k] = v
    return out


def ensure(client, model: str, key_field: str, vals: dict):
    """Create the record unless one with the same natural key already exists.

    Returns (id, created: bool).
    """
    key_value = vals[key_field]
    existing = client.search(model, [[key_field, "=", key_value]])
    if existing:
        return existing[0], False
    return client.create(model, vals), True


def ensure_many(client, ent: dict, trace=None) -> int:
    """Idempotently materialise `ent['target']` records for an entity spec.

    Returns the number actually created this run (0 on a clean re-run).
    """
    created = 0
    for i in range(1, ent["target"] + 1):
        vals = render_vals(ent["vals"], i)
        _id, was_created = ensure(client, ent["model"], ent["key_field"], vals)
        if was_created:
            created += 1
            if trace:
                trace.write(ent["model"], vals.get(ent["key_field"], str(i)))
    return created
