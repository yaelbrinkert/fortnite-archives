import os
import json

class FileNavigator:
    def __init__(self, base_dir):
        self.base_dir = os.path.abspath(base_dir)
        self.current_path = self.base_dir
        self.entries = []

    def update_entries(self):
        try:
            entries = os.listdir(self.current_path)
            entries.sort(key=lambda e: (not os.path.isdir(os.path.join(self.current_path, e)), e.lower()))
            if self.current_path == self.base_dir:
                # Filter to only chapter_x directories at top level
                entries = [e for e in entries if os.path.isdir(os.path.join(self.current_path, e)) and e.startswith('chapter_')]
                self.entries = entries
            else:
                self.entries = ['..'] + entries
        except PermissionError:
            self.entries = []

    def go_up(self):
        if self.current_path != self.base_dir:
            self.current_path = os.path.dirname(self.current_path)
            self.update_entries()

    def enter(self, selected_index):
        if selected_index < 0 or selected_index >= len(self.entries):
            return None
        entry = self.entries[selected_index]
        if entry == '..':
            self.go_up()
            return None
        path = os.path.join(self.current_path, entry)
        if os.path.isdir(path):
            self.current_path = path
            self.update_entries()
            return None
        elif path.endswith('.json') and os.path.isfile(path):
            return path
        return None

    def read_file(self, path):
        try:
            with open(path, 'r') as f:
                content = f.read()
            return content.splitlines()
        except Exception as e:
            return [f'Error reading file: {e}']


    def search_locations(self, substring):
        """
        Search all json files within base_dir subtree for 'locations' containing the substring (case-insensitive).
        Returns a dictionary mapping chapter/season directories to lists of update versions containing matches.
        """
        matching_dirs = {}  # Maps chapter_season to list of update versions
        substring = substring.lower()  # Convert once for case-insensitive search
        
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        if 'locations' in data and isinstance(data['locations'], list):
                            # Check if any location contains our search string
                            if any(substring in loc.lower() for loc in data['locations']):
                                # Get relative path from base_dir
                                rel_path = os.path.relpath(file_path, self.base_dir)
                                # Get chapter, season, and update parts
                                parts = rel_path.split(os.sep)
                                if len(parts) >= 3:
                                    chapter_season = os.path.join(parts[0], parts[1])
                                    update_version = parts[2]
                                    
                                    if chapter_season not in matching_dirs:
                                        matching_dirs[chapter_season] = []
                                    matching_dirs[chapter_season].append(update_version)
                    except Exception:
                        continue
        
        # Convert to list of tuples (chapter_season, [update_versions])
        return [(k, sorted(matching_dirs[k])) for k in sorted(matching_dirs.keys())]
