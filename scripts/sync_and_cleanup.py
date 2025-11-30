#!/usr/bin/env python3
"""
Sync and Cleanup Script for ToknNews Repository.

This script reorganizes the repository files into a versioned sync set, grouping code into
logical domains (ingestion_brain, processing, distribution) and archiving any backup or dev-only files.
It can run in a dry-run mode to preview actions, and should be executed from the repository root.
"""
import os
import shutil
import subprocess
import sys

def is_git_repo():
    # Check if the current directory is a Git repository (looks for .git folder)
    return os.path.isdir(".git")

def git_branch_exists(branch_name):
    # Check if a Git branch already exists (locally or on origin)
    # Local branch check
    res1 = subprocess.run(
        ["git", "rev-parse", "--verify", branch_name],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if res1.returncode == 0:
        return True
    # Remote branch check on origin
    res2 = subprocess.run(
        ["git", "ls-remote", "--exit-code", "origin", f"refs/heads/{branch_name}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return res2.returncode == 0

def move_path(src, dest, dry_run=False):
    # Move a file or directory from src to dest (or simulate if dry_run=True).
    # Creates destination directories as needed.
    if not os.path.exists(src):
        print(f"[WARN] Source {src} does not exist, skipping.")
        return
    if dry_run:
        print(f"Would move: {src} -> {dest}")
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(src, dest)
        print(f"Moved: {src} -> {dest}")

def main(version, dry_run):
    # Ensure we are at the repo root (Git present)
    if not is_git_repo():
        print("Error: Current directory is not a git repository (no .git folder).")
        sys.exit(1)
    branch_name = f"sync-cleanup-v{version}"
    # Safety check: avoid overwriting an existing branch of the same name
    if git_branch_exists(branch_name):
        print(f"Error: Branch '{branch_name}' already exists. Choose a new version or delete the existing branch.")
        sys.exit(1)
    # If not a dry run, create a new Git branch for the sync/cleanup
    if not dry_run:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        print(f"Created new branch: {branch_name}")

    # Define target directories for the structured sync set
    sync_dir = os.path.join("sync_sets", f"v{version}")
    current_dir = os.path.join(sync_dir, "current")
    dev_dir = os.path.join(sync_dir, "dev")

    # Prevent accidental overwrite if the version directory already exists
    if os.path.exists(current_dir) or os.path.exists(dev_dir):
        print(f"Error: Target directory {sync_dir} already exists. Use a new version name or remove the existing directory.")
        sys.exit(1)

    # Create the base folder structure for current and dev
    if dry_run:
        print(f"Would create directory structure: {current_dir}/{{ingestion_brain,processing,distribution}} and {dev_dir}/")
    else:
        os.makedirs(os.path.join(current_dir, "ingestion_brain"), exist_ok=True)
        os.makedirs(os.path.join(current_dir, "processing"), exist_ok=True)
        os.makedirs(os.path.join(current_dir, "distribution"), exist_ok=True)
        os.makedirs(dev_dir, exist_ok=True)
        print(f"Created directories: {current_dir}/(ingestion_brain, processing, distribution) and {dev_dir}/")

    # Define paths for domain folders under 'current'
    ingestion_path = os.path.join(current_dir, "ingestion_brain")
    processing_path = os.path.join(current_dir, "processing")
    distribution_path = os.path.join(current_dir, "distribution")

    # Step 1: Move all backup, old, or dev-only files/directories into the dev archive
    for root, dirs, files in os.walk("."):
        # Skip the Git directory and the newly created sync_sets directory to avoid interference
        if root.startswith("./.git") or root.startswith("./sync_sets"):
            continue
        # Check each subdirectory in this root for patterns indicating backups or dev content
        for d in list(dirs):
            d_lower = d.lower()
            src_dir = os.path.join(root, d)
            if (d_lower.startswith("backup_") or "backup" in d_lower or "old_backup" in d_lower 
                    or d_lower.endswith("_old") or d_lower.endswith("_backup") 
                    or d_lower == "sandbox" or "dev_only" in d_lower):
                # Determine destination path under dev (preserve original sub-path structure)
                rel_path = os.path.normpath(os.path.join(root, d))
                if rel_path.startswith("./"):
                    rel_path = rel_path[2:]  # trim leading "./"
                dest_dir = os.path.join(dev_dir, rel_path)
                move_path(src_dir, dest_dir, dry_run=dry_run)
                # Remove this directory from traversal to avoid moving its contents twice
                try:
                    dirs.remove(d)
                except ValueError:
                    pass
        # Check each file in this root for backup/old patterns (e.g., filenames ending in ~ or .bak)
        for f in files:
            f_lower = f.lower()
            src_file = os.path.join(root, f)
            if (f.endswith("~") or f_lower.endswith(".bak") or ".bak." in f_lower 
                    or f_lower.endswith("_old") or f_lower.endswith("_backup")):
                rel_path = os.path.normpath(os.path.join(root, f))
                if rel_path.startswith("./"):
                    rel_path = rel_path[2:]
                dest_file = os.path.join(dev_dir, rel_path)
                move_path(src_file, dest_file, dry_run=dry_run)

    # Step 2: Move primary code files into the structured 'current' directories
    # Ingestion domain: move all files from backend/live/ into ingestion_brain/
    if os.path.isdir("backend/live"):
        for name in os.listdir("backend/live"):
            # Skip any files that were identified as dev-only (they would have been moved above)
            if (name.endswith("~") or name.lower().endswith(".bak") 
                    or name.lower().endswith("_old") or name.lower().endswith("_backup") 
                    or ".bak." in name.lower()):
                continue
            src = os.path.join("backend/live", name)
            if not os.path.exists(src):
                continue  # file might have been moved already
            dest = os.path.join(ingestion_path, name)
            move_path(src, dest, dry_run=dry_run)
        # Remove the empty backend/live directory (no longer needed in current structure)
        try:
            if not dry_run:
                os.rmdir("backend/live")
                print("Removed empty directory backend/live")
            else:
                print("Would remove directory backend/live (now empty)")
        except OSError:
            pass

    # RollingBrain is a legacy module; moving it under ingestion_brain for reference
    if os.path.exists("backend/script_engine/rolling_brain.py"):
        dest = os.path.join(ingestion_path, "rolling_brain.py")
        move_path("backend/script_engine/rolling_brain.py", dest, dry_run=dry_run)

    # Processing domain: move the entire script_engine module (excluding what was moved above) into processing/
    if os.path.isdir("backend/script_engine"):
        dest = os.path.join(processing_path, "script_engine")
        move_path("backend/script_engine", dest, dry_run=dry_run)

    # Distribution domain: move broadcast loop code and other distribution components
    if os.path.isdir("backend/broadcast"):
        dest = os.path.join(distribution_path, "broadcast")
        move_path("backend/broadcast", dest, dry_run=dry_run)
    if os.path.isdir("unreal"):
        dest = os.path.join(distribution_path, "unreal")
        move_path("unreal", dest, dry_run=dry_run)
    if os.path.isdir("backend/social"):
        dest = os.path.join(distribution_path, "social")
        move_path("backend/social", dest, dry_run=dry_run)
    if os.path.isdir("backend/integrations"):
        dest = os.path.join(distribution_path, "integrations")
        move_path("backend/integrations", dest, dry_run=dry_run)

    if dry_run:
        print("Dry run complete. No changes were made.")
    else:
        print("Sync and cleanup completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync and cleanup ToknNews repository.")
    parser.add_argument("--version", default="1.0", help="Version label for sync set (e.g., 1.0)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files or Git")
    args = parser.parse_args()
    main(args.version, args.dry_run)
