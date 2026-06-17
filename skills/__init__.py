import importlib
import functools
from pathlib import Path


def load_skills():
    skills_dir = Path(__file__).parent
    loaded = []

    for path in sorted(skills_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue

        module_name = f"skills.{path.stem}"
        try:
            mod = importlib.import_module(module_name)
        except Exception as e:
            print(f"  [skills] Failed to import {path.name}: {e}")
            continue

        name = getattr(mod, "SKILL_NAME", None)
        desc = getattr(mod, "SKILL_DESCRIPTION", None)
        run_fn = getattr(mod, "run", None)

        if not all([name, desc, run_fn]):
            print(f"  [skills] Skipping {path.name}: missing SKILL_NAME, SKILL_DESCRIPTION, or run()")
            continue

        @functools.wraps(run_fn)
        def wrapper(*args, _fn=run_fn, **kwargs):
            return _fn(*args, **kwargs)

        wrapper.__name__ = name
        wrapper.__doc__ = desc

        loaded.append(wrapper)
        print(f"  Loaded skill: {name}")

    return loaded
