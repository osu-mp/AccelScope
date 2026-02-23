"""
One-time migration script: converts old project config JSON
(data_root_directory dict + reviewers dict) to the new `users` list format.

Usage:
    python scripts/migrate_config.py path/to/config.json [path/to/another.json ...]
"""
import json
import shutil
import sys


def migrate_file_entries(entries):
    """Recursively normalize user_verified -> verified_by in file entries."""
    for entry in entries:
        if "entries" in entry:
            migrate_file_entries(entry["entries"])
        elif "path" in entry:
            # It's a file entry — normalize user_verified if present
            if "user_verified" in entry and "verified_by" not in entry:
                if entry["user_verified"]:
                    entry["verified_by"] = ["default"]
                else:
                    entry["verified_by"] = []
                del entry["user_verified"]


def migrate_config(data):
    """Convert old config dict to new format with users list. Returns modified dict."""
    excluded = {"default", "active"}
    drd = data.get("data_root_directory", {})
    reviewers = data.get("reviewers", {})

    # Handle legacy string data_root_directory (single path)
    if isinstance(drd, str):
        drd = {"default": drd}

    # Build users list
    users = []
    for username, path in drd.items():
        if username in excluded:
            continue
        alias = reviewers.get(username, {}).get("alias", username[:2].upper())
        users.append({
            "username": username,
            "display_name": username.capitalize(),
            "alias": alias,
            "data_root": path,
        })

    # Special case: mpace gets the "active" path if present and mpace user exists
    active_path = drd.get("active")
    if active_path:
        for u in users:
            if u["username"] == "mpace":
                u["data_root"] = active_path
                break

    data["users"] = users

    # Remove old keys
    data.pop("data_root_directory", None)
    data.pop("reviewers", None)

    # Normalize file entries
    if "entries" in data:
        migrate_file_entries(data["entries"])

    return data


def migrate_file(path):
    """Read, backup, migrate, and write a single config file."""
    with open(path, "r") as f:
        data = json.load(f)

    # Skip if already migrated
    if "users" in data and "data_root_directory" not in data:
        print(f"  SKIP (already migrated): {path}")
        return

    # Backup
    backup_path = path + ".bak"
    shutil.copy2(path, backup_path)
    print(f"  Backup: {backup_path}")

    data = migrate_config(data)

    with open(path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"  Migrated: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_config.py <config.json> [...]")
        sys.exit(1)

    for config_path in sys.argv[1:]:
        print(f"Processing: {config_path}")
        migrate_file(config_path)
