import logging
import os

import pyperclip

# Setup logging
logger = logging.getLogger(__name__)

# Default exclude paths and files
EXCLUDE_DIRS = {"venv", ".venv", "git", "__pycache__", "migrations"}
EXCLUDE_FILES = {".env", "README.md", "requirements.txt", ".gitignore", ".git"}

# Django-specific files that are commonly important
DJANGO_WHITELIST_FILES = ['models.py', 'admin.py', 'serializers.py', 'urls.py', 'views.py', 'utils.py', 'forms.py',
                          'tests.py', 'middleware.py', 'settings.py', 'factories.py', 'signals.py', 'services.py']

# Web file extensions to include
WEB_EXTENSIONS = ['.html', '.css', '.js']

# Django-specific excluded paths
DJANGO_EXCLUDED_PATHS = ['django\\contrib', 'django\\core', 'django\\db', 'django\\middleware', 'django\\utils',
                         'django\\views', 'django\\forms', 'django\\urls', 'django\\template', 'django\\test',
                         'django\\http']


def is_excluded(path, exclude_dirs, exclude_files):
    """Checks if a file or directory is in the exclusion list."""
    # Check if any excluded directory is in the path
    for exclude in exclude_dirs:
        if exclude in path.split(os.sep):
            return True
    # Check if the file is in the excluded files
    for exclude in exclude_files:
        if path.endswith(exclude):
            return True
    # Django specific exclusions
    for excluded_path in DJANGO_EXCLUDED_PATHS:
        if excluded_path in path:
            return True
    return False


def list_projects(directory):
    """List all directories in the given directory as potential projects."""
    projects = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    for idx, project in enumerate(projects):
        print(f"{idx + 1}. {project}")
    return projects


def list_django_apps(project_directory):
    """List all Django apps in the project."""
    apps_dir = os.path.join(project_directory, "apps")

    # If the apps directory exists, list apps from there
    if os.path.exists(apps_dir) and os.path.isdir(apps_dir):
        apps = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))]
        # Filter out non-app directories
        apps = [app for app in apps if not app.startswith('.') and app != '__pycache__']
    else:
        # Try to find apps in the root directory
        apps = []
        for d in os.listdir(project_directory):
            app_dir = os.path.join(project_directory, d)
            if (os.path.isdir(app_dir) and
                    os.path.exists(os.path.join(app_dir, 'models.py')) or
                    os.path.exists(os.path.join(app_dir, 'views.py'))):
                apps.append(d)

    for idx, app in enumerate(apps):
        print(f"{idx + 1}. {app}")

    return apps


def choose_file_types():
    """Let the user choose which types of files to include in the dump."""
    print("\nSelect file types to include in the dump:")
    print("1. Python files only (.py)")
    print("2. Python + HTML files (.py, .html)")
    print("3. Python + all web files (.py, .html, .css, .js)")
    print("4. All project files (including configuration files)")
    print("5. Custom selection")

    choice = input("\nEnter your choice number: ")

    try:
        choice = int(choice)
    except ValueError:
        print("Invalid choice. Using option 1 as default.")
        choice = 1

    if choice == 1:
        return ['.py'], [], []
    elif choice == 2:
        return ['.py', '.html'], [], []
    elif choice == 3:
        return ['.py'] + WEB_EXTENSIONS, [], []
    elif choice == 4:
        return ['.py', '.html', '.css', '.js', '.json', '.yml', '.yaml', '.txt', '.md'], [], []
    elif choice == 5:
        # Custom selection
        extensions = input("Enter file extensions separated by comma (e.g., .py,.html,.css): ").split(',')
        extensions = [ext.strip() for ext in extensions if ext.strip()]

        include_files = input("Enter filenames to include separated by comma (or leave empty): ").split(',')
        include_files = [f.strip() for f in include_files if f.strip()]

        exclude_files = input("Enter additional filenames to exclude separated by comma (or leave empty): ").split(',')
        exclude_files = [f.strip() for f in exclude_files if f.strip()]

        return extensions, include_files, exclude_files
    else:
        print("Invalid choice. Using option 1 as default.")
        return ['.py'], [], []


def collect_files(directory, extensions, include_files, exclude_dirs, exclude_files, app_name=None):
    """Collect all files that match the criteria."""
    collected_files = []

    # If app_name is specified, construct app directory path
    app_dir = None
    if app_name:
        # Check for app in the apps directory first
        possible_app_dir = os.path.join(directory, "apps", app_name)
        if os.path.exists(possible_app_dir) and os.path.isdir(possible_app_dir):
            app_dir = possible_app_dir
        else:
            # Check for app in the root directory
            possible_app_dir = os.path.join(directory, app_name)
            if os.path.exists(possible_app_dir) and os.path.isdir(possible_app_dir):
                app_dir = possible_app_dir

    for root, dirs, files in os.walk(directory, topdown=True):
        # Skip if app_name is specified and we're not in the app directory
        if app_name and app_dir and not root.startswith(app_dir):
            continue

        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d), exclude_dirs, exclude_files)]

        for file in files:
            file_path = os.path.join(root, file)

            # Skip excluded files
            if is_excluded(file_path, exclude_dirs, exclude_files):
                continue

            # Include file if it has one of the specified extensions
            if file.endswith(tuple(extensions)) or file in include_files:
                # Special handling for Python files
                if file.endswith('.py') and not file in DJANGO_WHITELIST_FILES:
                    if not any(file.startswith(prefix) for prefix in ['test_', 'tests_']):
                        # Only include Python files that are in the whitelist or start with test
                        continue

                collected_files.append(file_path)

    return collected_files


def extract_code(file_path):
    """Extract the code from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.exception(f"Could not read file {file_path}")
        return f"ERROR: Could not read file {file_path}: {str(e)}"


def build_project_structure(base_path, files):
    """Build a hierarchical structure of the project based on the files."""
    structure = {}
    for file_path in files:
        rel_path = os.path.relpath(file_path, base_path)
        parts = rel_path.split(os.sep)
        current_level = structure
        for part in parts[:-1]:
            current_level = current_level.setdefault(part, {})
        current_level.setdefault(parts[-1], None)
    return structure


def write_project_structure(structure, output_file, indent_level=0):
    """Write the project structure to the output file."""
    indent = ' ' * 4 * indent_level
    for name, sub_structure in sorted(structure.items()):
        if sub_structure is None:
            output_file.write(f"{indent}{name}\n")
        else:
            output_file.write(f"{indent}{name}/\n")
            write_project_structure(sub_structure, output_file, indent_level + 1)


def main():
    current_directory = os.getcwd()

    # Ask if user wants to select a project or use current directory
    use_current = input("Use current directory as project? (y/n): ").lower()

    if use_current.startswith('y'):
        project_directory = current_directory
        project_name = os.path.basename(current_directory)
    else:
        # List potential projects in current directory
        print("\nAvailable projects in current directory:")
        projects = list_projects(current_directory)

        if not projects:
            print("No projects found. Using current directory.")
            project_directory = current_directory
            project_name = os.path.basename(current_directory)
        else:
            try:
                project_number = int(input("\nSelect project number (or 0 for current directory): "))
                if project_number == 0:
                    project_directory = current_directory
                    project_name = os.path.basename(current_directory)
                else:
                    project_name = projects[project_number - 1]
                    project_directory = os.path.join(current_directory, project_name)
            except (ValueError, IndexError):
                print("Invalid choice. Using current directory.")
                project_directory = current_directory
                project_name = os.path.basename(current_directory)

    # Ask if user wants to dump files from a specific app
    dump_specific_app = input("\nDump files from a specific Django app only? (y/n): ").lower()
    selected_app = None

    if dump_specific_app.startswith('y'):
        print("\nAvailable Django apps:")
        apps = list_django_apps(project_directory)

        if not apps:
            print("No Django apps found. Dumping entire project.")
        else:
            try:
                app_number = int(input("\nSelect app number (or 0 for entire project): "))
                if app_number != 0:
                    selected_app = apps[app_number - 1]
                    print(f"Selected app: {selected_app}")
            except (ValueError, IndexError):
                print("Invalid choice. Dumping entire project.")

    # Choose which file types to include
    extensions, include_files, additional_exclude_files = choose_file_types()

    # Add additional exclude files to the default list
    exclude_files = EXCLUDE_FILES.union(set(additional_exclude_files))

    # Get output file name
    output_file_name = input(f"\nEnter filename to save the dump (default: {project_name}_dump.txt): ")
    if not output_file_name:
        if selected_app:
            output_file_name = f"{project_name}_{selected_app}_dump.txt"
        else:
            output_file_name = f"{project_name}_dump.txt"

    # Collect files that match the criteria
    if selected_app:
        print(f"\nCollecting files from app '{selected_app}'...")
    else:
        print(f"\nCollecting files from project '{project_name}'...")

    project_files = collect_files(project_directory, extensions, include_files, EXCLUDE_DIRS, exclude_files,
                                  selected_app)

    if not project_files:
        print("No files found for dump. Check your settings and try again.")
        return

    print(f"Found {len(project_files)} files for dump.")

    # Sort files by path for better organization
    project_files.sort()

    # Build project structure for overview
    structure = build_project_structure(project_directory, project_files)

    # Generate the dump
    with open(output_file_name, 'w', encoding='utf-8') as output_file:
        # Write project structure
        if selected_app:
            output_file.write(f"Project Structure Overview: {project_name} - App: {selected_app}\n")
        else:
            output_file.write(f"Project Structure Overview: {project_name}\n")

        output_file.write("=" * 3 + "\n")
        write_project_structure(structure, output_file)
        output_file.write("\n" + "=" * 3 + "\n\n")

        # Write the content of each file
        for file_path in project_files:
            rel_path = os.path.relpath(file_path, project_directory)
            output_file.write(f"File: {rel_path}\n")
            output_file.write("=" * 3 + "\n")
            file_content = extract_code(file_path)
            output_file.write(file_content)
            output_file.write("\n\n" + "=" * 3 + "\n\n")

    print(f"\nProject dump successfully saved to '{output_file_name}'.")

    # Copy to clipboard
    try:
        with open(output_file_name, 'r', encoding='utf-8') as f:
            dump_content = f.read()

        pyperclip.copy(dump_content)
        print("Dump content copied to clipboard.")
    except Exception as e:
        logger.exception("Failed to copy content to clipboard")
        print(f"Failed to copy content to clipboard: {e}")
        print("Try installing pyperclip: pip install pyperclip")


if __name__ == "__main__":
    main()
