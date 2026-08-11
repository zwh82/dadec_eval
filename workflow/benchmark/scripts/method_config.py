#!/usr/bin/env python3
import re

METHOD_LABELS = {
    "dadec": "DADEC", "fmlrc": "FMLRC", "f_hero": "F_HERO",
    "ratatosk": "Ratatosk", "r_hero": "R_HERO", "lordec": "LoRDEC",
    "l_hero": "L_HERO", "colormap": "CoLoRMap", "proovread": "Proovread",
    "vechat": "VeChat", "dechat": "DeChat",
}
ALIASES = {re.sub(r"[^a-z0-9]", "", label.lower()): key for key, label in METHOD_LABELS.items()}
ALIASES.update({re.sub(r"[^a-z0-9]", "", key): key for key in METHOD_LABELS})
K_FIELDS = ("dadec_k1", "dadec_k2", "fmlrc_k1", "fmlrc_k2",
            "ratatosk_k1", "ratatosk_k2", "lordec_k")
SETTING_FIELDS = {
    "dadec_split": int,
    "dadec_threshold": float,
    "dadec_abundance1": int,
    "dadec_abundance2": int,
    "hero_split": int,
    "hero_iterations": int,
    "lordec_solid": int,
}

def normalize_method(value):
    key = re.sub(r"[^a-z0-9]", "", str(value).lower())
    if key not in ALIASES:
        raise ValueError(f"Unknown method: {value}")
    return ALIASES[key]

def select_methods(value):
    if isinstance(value, list):
        values = value
    elif str(value).strip().lower() == "all":
        return list(METHOD_LABELS)
    else:
        values = [part.strip() for part in str(value).split(",") if part.strip()]
    selected = [normalize_method(value) for value in values]
    if not selected:
        raise ValueError("At least one method must be selected")
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate methods are not allowed")
    return selected

def resolve_coverage_parameters(config, coverage=None):
    profile = str(config.get("parameter_profile", "study"))
    profiles = config["parameters"]["profiles"]
    if profile not in profiles:
        raise ValueError(f"Unknown parameter_profile: {profile}")
    values = dict(profiles[profile] or {})
    coverage_config = config["parameters"].get("by_coverage", {}).get(str(coverage), {})
    coverage_profiles = coverage_config.get("profiles", {})
    if profile in coverage_profiles:
        values.update(coverage_profiles[profile] or {})
    for field in K_FIELDS:
        if field in config and config[field] is None:
            raise ValueError(f"{field} is blank; fill it or remove the key")
        if field in config:
            values[field] = int(config[field])
    unknown = sorted(set(values) - set(K_FIELDS))
    if unknown:
        raise ValueError(f"Unknown k parameters: {', '.join(unknown)}")
    for field, value in values.items():
        value = int(value)
        if value <= 0 or value % 2 == 0:
            raise ValueError(f"{field} must be a positive odd integer")
        values[field] = value

    settings = {
        "dadec_split": config["dadec"]["split_number"],
        "dadec_threshold": config["dadec"]["msa_threshold"],
        "dadec_abundance1": config["dadec"]["abundance_min1"],
        "dadec_abundance2": config["dadec"]["abundance_min2"],
        "hero_split": config["parameters"]["hero_split"],
        "hero_iterations": config["parameters"]["hero_iterations"],
        "lordec_solid": config["parameters"]["lordec_solid"],
    }
    overrides = coverage_config.get("settings", {})
    unknown_settings = sorted(set(overrides) - set(SETTING_FIELDS))
    if unknown_settings:
        raise ValueError(f"Unknown settings for {coverage}: {', '.join(unknown_settings)}")
    settings.update(overrides)
    for field, converter in SETTING_FIELDS.items():
        if field in config and config[field] is None:
            raise ValueError(f"{field} is blank; fill it or remove the key")
        if field in config:
            settings[field] = config[field]
        settings[field] = converter(settings[field])
        if settings[field] <= 0 and field != "dadec_threshold":
            raise ValueError(f"{field} must be positive")
        if field == "dadec_threshold" and not 0 < settings[field] <= 1:
            raise ValueError("dadec_threshold must be in (0, 1]")
    values.update(settings)
    return profile, values

def resolve_k_values(config):
    profile, values = resolve_coverage_parameters(config)
    return profile, {field: values[field] for field in K_FIELDS if field in values}

def validate_lordec(methods, values):
    if any(method in {"lordec", "l_hero"} for method in methods) and "lordec_k" not in values:
        raise ValueError("LoRDEC 0.9 requires -k; use parameter_profile=study or set lordec_k")

def k_args(method, values):
    base = {"f_hero": "fmlrc", "r_hero": "ratatosk", "l_hero": "lordec"}.get(method, method)
    flags = {
        "dadec": (("dadec_k1", "-k"), ("dadec_k2", "-K")),
        "fmlrc": (("fmlrc_k1", "-k"), ("fmlrc_k2", None)),
        "ratatosk": (("ratatosk_k1", "-k"), ("ratatosk_k2", "-K")),
        "lordec": (("lordec_k", "-k"),),
    }.get(base, ())
    if base == "fmlrc":
        selected = [str(values[name]) for name, _ in flags if name in values]
        return ["-k", *selected] if selected else []
    result = []
    for name, flag in flags:
        if name in values:
            result.extend([flag, str(values[name])])
    return result
