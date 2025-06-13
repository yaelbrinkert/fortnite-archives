import os
import sys

# Add project root to sys.path so navigator package can be imported when run as a script
script_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(script_path))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.navigator import FileNavigator
from tui.navigator import NavigatorTUI

def main():
    # Determine the project root directory by going up until we find the root (for now assume this script is in navigator/ under project root)
    script_path = os.path.abspath(__file__)
    # Project root directory is parent of navigator directory
    project_root = os.path.dirname(os.path.dirname(script_path))

    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = project_root

    if not os.path.isdir(base_dir):
        print(f'Error: Base directory {base_dir} does not exist or is not a directory.')
        sys.exit(1)

    navigator = FileNavigator(base_dir)
    navigator.update_entries()

    tui = NavigatorTUI(navigator)
    tui.run()

if __name__ == '__main__':
    main()
