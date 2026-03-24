import re


def read_requirements():
    """Reads requirements.txt and returns a dict of packages and their versions."""
    requirements = {}
    with open('requirements.txt', 'r') as file:
        for line in file:
            if '==' in line:  # Checks for the standard format package==version
                package, version = line.strip().split('==')
                requirements[package] = version
    return requirements


def update_pipfile(requirements):
    """Updates the Pipfile with the specified package versions."""
    # Load the Pipfile
    with open('Pipfile', 'r') as file:
        pipfile_lines = file.readlines()

    # Prepare to update the Pipfile content
    package_regex = re.compile(r'^(\s*"?([\w\-]+)"?\s*=\s*)".*"\s*$')
    updated_lines = []
    found_packages = set()

    # Update existing packages
    for line in pipfile_lines:
        match = package_regex.match(line)
        if match:
            prefix, package_name = match.groups()
            if package_name in requirements:
                new_line = f'{prefix}"=={requirements[package_name]}"\n'
                updated_lines.append(new_line)
                found_packages.add(package_name)
                continue
        updated_lines.append(line)

    # Add new packages that weren't in the Pipfile
    for package, version in requirements.items():
        if package not in found_packages:
            updated_lines.append(f'{package} = "=={version}"\n')

    # Write the updated Pipfile
    with open('Pipfile', 'w') as file:
        file.writelines(updated_lines)

    print("Pipfile has been updated.")


# Main execution
requirements = read_requirements()
update_pipfile(requirements)
