from blessed import Terminal
import os
import sys
import json
from navigator.tui.editor import EditorTUI

term = Terminal()

def get_user_input(prompt, initial_text="", y_pos=10, x_pos=2, max_width=60):
    """Custom input method that shows what the user is typing"""
    current_text = initial_text
    cursor_pos = len(current_text)
    
    # Clear input area and show prompt
    print(term.move(y_pos, x_pos) + term.clear_eol + prompt)
    print(term.move(y_pos+1, x_pos) + term.clear_eol + "> " + current_text + " ")
    
    while True:
        # Position cursor and refresh
        print(term.move(y_pos+1, x_pos+2+cursor_pos))
        
        # Get input
        key = term.inkey()
        
        if key.name == 'KEY_ENTER':
            return current_text
        elif key.name == 'KEY_ESCAPE':
            return ""
        elif key.name == 'KEY_BACKSPACE' and cursor_pos > 0:
            # Remove character before cursor
            current_text = current_text[:cursor_pos-1] + current_text[cursor_pos:]
            cursor_pos -= 1
        elif key.name == 'KEY_DELETE' and cursor_pos < len(current_text):
            # Remove character at cursor
            current_text = current_text[:cursor_pos] + current_text[cursor_pos+1:]
        elif key.name == 'KEY_LEFT' and cursor_pos > 0:
            cursor_pos -= 1
        elif key.name == 'KEY_RIGHT' and cursor_pos < len(current_text):
            cursor_pos += 1
        elif key.name == 'KEY_HOME':
            cursor_pos = 0
        elif key.name == 'KEY_END':
            cursor_pos = len(current_text)
        elif not key.is_sequence and ord(key) >= 32:
            # Insert printable character at cursor
            current_text = current_text[:cursor_pos] + key + current_text[cursor_pos:]
            cursor_pos += 1
            
        # Update display
        if len(current_text) > max_width:
            visible_text = current_text[max(0, cursor_pos-max_width//2):cursor_pos] + current_text[cursor_pos:cursor_pos+max_width//2]
            if cursor_pos > max_width//2:
                visible_pos = max_width//2
            else:
                visible_pos = cursor_pos
        else:
            visible_text = current_text
            visible_pos = cursor_pos
            
        print(term.move(y_pos+1, x_pos) + term.clear_eol + "> " + visible_text + " ")

class NavigatorTUI:
    def __init__(self, navigator):
        self.navigator = navigator
        self.selected = 0
        self.viewing_file = False
        self.file_content_lines = []
        self.file_line_offset = 0
        self.file_path = ""

        self.search_mode = False
        self.search_query = ""
        self.search_results = []
        self.search_selected = 0
        self.in_search_results_view = False

    def execute_search(self):
        self.search_results = []
        self.search_selected = 0
        if self.search_query.strip():
            results = self.navigator.search_locations(self.search_query)
            self.search_results = results
        self.search_mode = False
        self.in_search_results_view = len(self.search_results) > 0
        # Force redraw at current terminal size
        height, width = term.height, term.width
        self.draw(height, width)

    def run(self):
        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            height, width = term.height, term.width
            self.draw(height, width)
            while True:
                if self.search_mode:
                    key = term.inkey()
                    if key.name == 'KEY_ESCAPE':
                        self.search_mode = False
                        self.search_query = ""
                        self.search_results = []
                        self.draw(height, width)
                        continue
                    elif key.name == 'KEY_ENTER' or key == '\n':
                        self.execute_search()
                        # execute_search now handles drawing
                        continue
                    elif key.name == 'KEY_BACKSPACE':
                        self.search_query = self.search_query[:-1]
                        self.draw(height, width)
                        continue
                    else:
                        if key.is_sequence or key == '':
                            continue
                        self.search_query += key
                        self.draw(height, width)
                        continue

                key = term.inkey()

                if key.lower() == 'q':
                    break

                if key.lower() == 'f':
                    self.search_mode = True
                    self.search_query = ""
                    self.draw_search_prompt(height, width)
                    continue

                if self.viewing_file:
                    if key.name == 'KEY_UP':
                        self.scroll_file(-1, height)
                    elif key.name == 'KEY_DOWN':
                        self.scroll_file(1, height)
                    elif key.name == 'KEY_PPAGE':
                        self.scroll_file(-(height - 2), height)
                    elif key.name == 'KEY_NPAGE':
                        self.scroll_file(height - 2, height)
                    elif key.lower() == 'e':
                        self.show_edit_menu()
                        self.draw(height, width)
                        continue
                    elif key.name in ('KEY_BACKSPACE', 'KEY_ESCAPE'):
                        self.viewing_file = False
                        self.draw(height, width)
                        continue

                if self.in_search_results_view:
                    if key.name == 'KEY_UP':
                        self.search_selected = max(0, self.search_selected - 1)
                    elif key.name == 'KEY_DOWN':
                        self.search_selected = min(len(self.search_results) - 1, self.search_selected + 1)
                    elif key.name == 'KEY_ENTER' or key == '\n':
                        # Instead of opening file, enter the directory selected in search results
                        selected_dir = self.search_results[self.search_selected]
                        if isinstance(selected_dir, tuple) or isinstance(selected_dir, list):
                            selected_dir = selected_dir[0]  # handle if list of tuples
                        # Set navigator current path to selected directory
                        new_path = os.path.join(self.navigator.base_dir, selected_dir)
                        if os.path.isdir(new_path):
                            self.navigator.current_path = new_path
                            self.navigator.update_entries()
                            self.selected = 0
                        self.in_search_results_view = False
                        self.search_results = []
                    elif key.name in ('KEY_BACKSPACE', 'KEY_ESCAPE'):
                        self.in_search_results_view = False
                        self.search_results = []
                        self.selected = 0
                    self.draw(height, width)
                    continue

                if key.name == 'KEY_UP':
                    self.selected = max(0, self.selected - 1)
                elif key.name == 'KEY_DOWN':
                    self.selected = min(len(self.navigator.entries) - 1, self.selected + 1)
                elif key.name == 'KEY_ENTER' or key == '\n':
                    res = self.navigator.enter(self.selected)
                    if res:
                        # Viewing a JSON file, read contents
                        self.file_content_lines = self.navigator.read_file(res)
                        self.file_line_offset = 0
                        self.file_path = res
                        self.viewing_file = True
                    else:
                        # Directory changed, reset selection
                        self.selected = 0
                elif key.name == 'KEY_BACKSPACE':
                    self.navigator.go_up()
                    self.selected = 0
                self.draw(height, width)

    def draw(self, height, width):
        print(term.home + term.clear)
        if self.search_mode:
            self.draw_search_prompt(height, width)
        elif self.in_search_results_view and self.search_results:
            self.draw_search_results(height, width)
        elif self.viewing_file:
            self.draw_file_view(height, width)
        else:
            self.draw_directory_view(height, width)
        if self.viewing_file:
            print(term.move(height - 1, 0) + term.reverse(' q:quit  e:edit  Backspace:return ') + term.normal)
        else:
            print(term.move(height - 1, 0) + term.reverse(' q:quit  Enter:open  Backspace:up  f:search ') + term.normal)

    def draw_search_prompt(self, height, width):
        prompt = "Search locations: " + self.search_query
        print(term.move(height // 2, max(0, (width - len(prompt)) // 2)) + term.reverse(prompt) + term.normal)

    def draw_search_results(self, height, width):
        title = f"Search results for '{self.search_query}' (Press Backspace to cancel)"
        print(term.move(0, 0) + term.bold(title[:width]))
        if not self.search_results:
            print(term.move(2, 0) + "No results found.")
            return
            
        max_display = height - 3
        start = max(0, self.search_selected - max_display + 1) if self.search_selected >= max_display else 0
        
        for i, (chapter_season, updates) in enumerate(self.search_results[start:start + max_display]):
            focused = (start + i == self.search_selected)
            
            # Format as "chapter_x/season_y    [update1, update2, ...]"
            updates_str = f"[{', '.join(updates)}]"
            
            # Calculate available width for main text and updates
            display_width = width - 4  # Leave some margin
            
            # If combined length is too long, truncate updates list
            if len(chapter_season) + len(updates_str) + 4 > display_width:
                max_updates_width = display_width - len(chapter_season) - 8
                if max_updates_width > 10:  # Only if we have reasonable space
                    updates_str = updates_str[:max_updates_width] + "...]"
            
            # Format with updates right-aligned
            padding = display_width - len(chapter_season) - len(updates_str)
            line = chapter_season + " " * max(1, padding) + updates_str
            
            if len(line) > width:
                line = line[:width - 3] + "..."
                
            if focused:
                print(term.move(i + 1, 0) + term.reverse(line))
            else:
                print(term.move(i + 1, 0) + line)

    def draw_directory_view(self, height, width):
        title = f'Directory: {self.navigator.current_path}'
        print(term.move(0, 0) + term.bold(title[:width]))
        max_display = height - 2
        start = max(0, self.selected - max_display + 1) if self.selected >= max_display else 0
        for i, entry in enumerate(self.navigator.entries[start:start+max_display]):
            focused = (start + i == self.selected)
            entry_path = os.path.join(self.navigator.current_path, entry if entry != '..' else os.pardir)
            line = entry + ('/' if os.path.isdir(entry_path) else '')
            if focused:
                print(term.move(i+1, 0) + term.reverse(line[:width]))
            else:
                print(term.move(i+1, 0) + line[:width])

    def draw_file_view(self, height, width):
        title = f'Viewing file: {self.file_path}'
        print(term.move(0, 0) + term.bold(title[:width]))
        max_display = height - 2
        lines_to_show = self.file_content_lines[self.file_line_offset:self.file_line_offset + max_display]
        for i, line in enumerate(lines_to_show):
            if len(line) > width:
                line = line[:width-3] + '...'
            print(term.move(i + 1, 0) + line)
        status = f'Lines {self.file_line_offset + 1} - {min(self.file_line_offset + max_display, len(self.file_content_lines))} of {len(self.file_content_lines)}'
        print(term.move(height - 1, 0) + term.reverse(status.ljust(width)) + term.normal)

    def scroll_file(self, direction, height):
        max_display = height - 2
        new_offset = self.file_line_offset + direction
        if new_offset < 0:
            new_offset = 0
        elif new_offset > max(0, len(self.file_content_lines) - max_display):
            new_offset = max(0, len(self.file_content_lines) - max_display)
        self.file_line_offset = new_offset
        
    def show_edit_menu(self):
        """Show a menu of editing options for the current file"""
        if not self.viewing_file or not self.file_path:
            return
            
        height, width = term.height, term.width
        menu_options = [
            "Add a new location", 
            "Edit existing location", 
            "Remove a location", 
            "Add/edit a category",
            "Remove a category",
            "Cancel"
        ]
        selected = 0
        
        while True:
            # Draw menu
            print(term.clear)
            print(term.move(2, 2) + term.bold(f"Edit options for {os.path.basename(self.file_path)}:"))
            
            for i, option in enumerate(menu_options):
                if i == selected:
                    print(term.move(4 + i, 4) + term.reverse(f"▶ {option}"))
                else:
                    print(term.move(4 + i, 4) + f"  {option}")
            
            print(term.move(4 + len(menu_options) + 2, 2) + "Use arrow keys to select, Enter to confirm")
            
            # Get input
            key = term.inkey()
            
            if key.name == 'KEY_UP' and selected > 0:
                selected -= 1
            elif key.name == 'KEY_DOWN' and selected < len(menu_options) - 1:
                selected += 1
            elif key.name == 'KEY_ENTER' or key == '\n':
                if selected == 0:  # Add location
                    self.add_location()
                    break
                elif selected == 1:  # Edit location
                    self.edit_location()
                    break
                elif selected == 2:  # Remove location
                    self.remove_location()
                    break
                elif selected == 3:  # Add/edit category
                    self.add_category()
                    break
                elif selected == 4:  # Remove category
                    self.remove_category()
                    break
                else:  # Cancel
                    break
            elif key.name == 'KEY_ESCAPE' or key.lower() == 'q':
                break
            
    def add_location(self):
        """Add a new location to the current JSON file"""
        if not self.viewing_file or not self.file_path:
            return
        
        # Get current file content as JSON
        try:
            with open(self.file_path, 'r') as f:
                json_data = json.loads(f.read())
                
            if "locations" not in json_data or not isinstance(json_data["locations"], list):
                json_data["locations"] = []
        except Exception:
            # Create new data structure if file doesn't exist or is invalid
            json_data = {"locations": []}
        
        # Save current terminal state
        height, width = term.height, term.width
        
        # Clear the screen for input
        print(term.clear)
        print(term.move(2, 2) + term.bold("Add a new location to " + os.path.basename(self.file_path)))
        print(term.move(4, 2) + "Current locations:")
        
        # Display existing locations for reference
        for i, loc in enumerate(json_data.get("locations", [])):
            if i < 15:  # Show only first 15 to avoid cluttering
                print(term.move(5+i, 4) + f"• {loc}")
            elif i == 15:
                print(term.move(5+i, 4) + f"... and {len(json_data['locations'])-15} more")
                
        # Get user input with custom input method
        prompt = "Enter location name (or press ESC to cancel):"
        print(term.move(8, 2) + term.normal_cursor)
        location_name = get_user_input(prompt, y_pos=8).strip()
        print(term.hidden_cursor)
        
        if location_name:
            # Add the new location if not already present
            if location_name not in json_data["locations"]:
                json_data["locations"].append(location_name)
                json_data["locations"].sort()  # Sort alphabetically
                
                # Save updated JSON
                try:
                    with open(self.file_path, 'w') as f:
                        f.write(json.dumps(json_data, indent=2))
                    
                    # Update the displayed content
                    self.file_content_lines = json.dumps(json_data, indent=2).splitlines()
                    
                    # Show success message
                    print(term.move(20, 2) + term.green(f"Added '{location_name}' to locations!"))
                    print(term.move(22, 2) + "Press any key to continue...")
                    term.inkey()
                except Exception as e:
                    print(term.move(20, 2) + term.red(f"Error: {str(e)}"))
                    print(term.move(22, 2) + "Press any key to continue...")
                    term.inkey()
                    self.file_content_lines = [f"Error saving file: {str(e)}"]
        
    def add_category(self):
        """Add a new category/field to the current JSON file"""
        if not self.viewing_file or not self.file_path:
            return
        
        # Get current file content as JSON
        try:
            with open(self.file_path, 'r') as f:
                json_data = json.loads(f.read())
        except Exception:
            json_data = {}
        
        # Clear the screen for input
        print(term.clear)
        print(term.move(2, 2) + term.bold("Add a new category to " + os.path.basename(self.file_path)))
        
        # Show existing categories
        print(term.move(4, 2) + "Current categories:")
        row = 5
        for i, (key, value) in enumerate(json_data.items()):
            if i < 10:  # Show only first 10 to avoid cluttering
                value_str = str(value)
                if len(value_str) > 40:
                    value_str = value_str[:37] + "..."
                print(term.move(row, 4) + f"• {key}: {value_str}")
                row += 1
            elif i == 10:
                print(term.move(row, 4) + f"... and {len(json_data)-10} more")
                row += 1
        
        # Get category name with custom input method
        print(term.normal_cursor)
        prompt = "Enter category name (or press ESC to cancel):"
        category_name = get_user_input(prompt, y_pos=row+2).strip()
        
        if category_name:
            row += 5
            
            # Ask if this category should be an array (like locations)
            print(term.move(row, 2) + "Should this be a list of items like locations? (y/n)")
            is_array = term.inkey().lower() == 'y'
            
            row += 2
            
            if is_array:
                if category_name in json_data and isinstance(json_data[category_name], list):
                    items = json_data[category_name]
                    items_str = ", ".join(items) if items else ""
                    value_prompt = f"Enter comma-separated items for '{category_name}' (current: {items_str}):"
                else:
                    value_prompt = f"Enter comma-separated items for '{category_name}':"
                
                # Get comma-separated values
                value = get_user_input(value_prompt, y_pos=row)
                
                # Parse as array of strings
                if value.strip():
                    # Split by commas and trim whitespace from each item
                    items = [item.strip() for item in value.split(',')]
                    
                    # Remove empty items
                    items = [item for item in items if item]
                    
                    # Sort items alphabetically
                    items.sort()
                    
                    parsed_value = items
                else:
                    parsed_value = []
            else:
                if category_name in json_data:
                    value_prompt = f"Update value for '{category_name}' (current: {json_data[category_name]}):"
                else:
                    value_prompt = f"Enter value for '{category_name}' (leave empty for empty string):"
                
                # Get value with custom input
                value = get_user_input(value_prompt, y_pos=row)
                
                # Try to parse the value as JSON first (for numbers, booleans, arrays)
                try:
                    # Try to detect if this should be treated as JSON
                    if value.lower() in ('true', 'false'):
                        parsed_value = value.lower() == 'true'
                    elif value.isdigit() or (value and value[0] == '-' and value[1:].isdigit()):
                        parsed_value = int(value)
                    elif value and value[0] in '[{':
                        # Looks like JSON array or object
                        parsed_value = json.loads(value)
                    else:
                        # Treat as string
                        parsed_value = value
                except json.JSONDecodeError:
                    # If not valid JSON, treat as a string
                    parsed_value = value
            
            # Set the value in the JSON data
            json_data[category_name] = parsed_value
                
            # Save updated JSON
            try:
                with open(self.file_path, 'w') as f:
                    f.write(json.dumps(json_data, indent=2))
                
                # Update the displayed content
                self.file_content_lines = json.dumps(json_data, indent=2).splitlines()
                
                # Show success message
                print(term.move(row+4, 2) + term.green(f"Added/updated '{category_name}' successfully!"))
                print(term.move(row+6, 2) + "Press any key to continue...")
                term.inkey()
            except Exception as e:
                print(term.move(row+4, 2) + term.red(f"Error: {str(e)}"))
                print(term.move(row+6, 2) + "Press any key to continue...")
                term.inkey()
                self.file_content_lines = [f"Error saving file: {str(e)}"]
        
        # Restore terminal state
        print(term.hidden_cursor)
        
    def edit_location(self):
        """Edit an existing location in the current JSON file"""
        if not self.viewing_file or not self.file_path:
            return
        
        # Get current file content as JSON
        try:
            with open(self.file_path, 'r') as f:
                json_data = json.loads(f.read())
        except Exception:
            json_data = {"locations": []}
            
        if "locations" not in json_data or not isinstance(json_data["locations"], list) or not json_data["locations"]:
            print(term.clear)
            print(term.move(2, 2) + term.bold("No locations to edit"))
            print(term.move(4, 2) + "This file doesn't have any locations to edit.")
            print(term.move(6, 2) + "Press any key to continue...")
            term.inkey()
            return
            
        # Show the selection menu
        locations = json_data["locations"]
        selected = 0
        
        while True:
            print(term.clear)
            print(term.move(2, 2) + term.bold("Select a location to edit:"))
            
            # Calculate visible range
            max_display = term.height - 10
            start_idx = max(0, selected - max_display//2)
            end_idx = min(len(locations), start_idx + max_display)
            
            # Show locations
            for i, loc in enumerate(locations[start_idx:end_idx]):
                idx = i + start_idx
                if idx == selected:
                    print(term.move(4 + i, 4) + term.reverse(f"▶ {loc}"))
                else:
                    print(term.move(4 + i, 4) + f"  {loc}")
                    
            print(term.move(term.height - 4, 2) + "Use arrow keys to navigate, Enter to select, ESC to cancel")
            
            key = term.inkey()
            
            if key.name == 'KEY_UP' and selected > 0:
                selected -= 1
            elif key.name == 'KEY_DOWN' and selected < len(locations) - 1:
                selected += 1
            elif key.name == 'KEY_ENTER' or key == '\n':
                old_name = locations[selected]
                print(term.clear)
                print(term.move(2, 2) + term.bold(f"Editing location: {old_name}"))
                print(term.move(4, 2) + "Enter new name (or press ESC to cancel):")
                
                print(term.normal_cursor)
                new_name = get_user_input("", old_name, y_pos=4, x_pos=2)
                print(term.hidden_cursor)
                
                if new_name and new_name != old_name:
                    # Update the location
                    locations[selected] = new_name
                    locations.sort()  # Keep sorted
                    
                    # Save back to file
                    try:
                        with open(self.file_path, 'w') as f:
                            f.write(json.dumps(json_data, indent=2))
                        
                        # Update displayed content
                        self.file_content_lines = json.dumps(json_data, indent=2).splitlines()
                        
                        print(term.move(8, 2) + term.green(f"Updated '{old_name}' to '{new_name}'!"))
                    except Exception as e:
                        print(term.move(8, 2) + term.red(f"Error saving file: {str(e)}"))
                        
                    print(term.move(10, 2) + "Press any key to continue...")
                    term.inkey()
                break
            elif key.name == 'KEY_ESCAPE':
                break
                
    def remove_location(self):
        """Remove a location from the current JSON file"""
        if not self.viewing_file or not self.file_path:
            return
        
        # Get current file content as JSON
        try:
            with open(self.file_path, 'r') as f:
                json_data = json.loads(f.read())
        except Exception:
            json_data = {"locations": []}
            
        if "locations" not in json_data or not isinstance(json_data["locations"], list) or not json_data["locations"]:
            print(term.clear)
            print(term.move(2, 2) + term.bold("No locations to remove"))
            print(term.move(4, 2) + "This file doesn't have any locations to remove.")
            print(term.move(6, 2) + "Press any key to continue...")
            term.inkey()
            return
            
        # Show the selection menu
        locations = json_data["locations"]
        selected = 0
        
        while True:
            print(term.clear)
            print(term.move(2, 2) + term.bold("Select a location to remove:"))
            
            # Calculate visible range
            max_display = term.height - 10
            start_idx = max(0, selected - max_display//2)
            end_idx = min(len(locations), start_idx + max_display)
            
            # Show locations
            for i, loc in enumerate(locations[start_idx:end_idx]):
                idx = i + start_idx
                if idx == selected:
                    print(term.move(4 + i, 4) + term.reverse(f"▶ {loc}"))
                else:
                    print(term.move(4 + i, 4) + f"  {loc}")
                    
            print(term.move(term.height - 4, 2) + "Use arrow keys to navigate, Enter to select, ESC to cancel")
            
            key = term.inkey()
            
            if key.name == 'KEY_UP' and selected > 0:
                selected -= 1
            elif key.name == 'KEY_DOWN' and selected < len(locations) - 1:
                selected += 1
            elif key.name == 'KEY_ENTER' or key == '\n':
                location = locations[selected]
                
                # Confirm deletion
                print(term.clear)
                print(term.move(2, 2) + term.bold(f"Confirm removal of: {location}"))
                print(term.move(4, 2) + "Are you sure? (y/n)")
                
                confirm_key = term.inkey()
                if confirm_key.lower() == 'y':
                    # Remove the location
                    locations.pop(selected)
                    
                    # Save back to file
                    try:
                        with open(self.file_path, 'w') as f:
                            f.write(json.dumps(json_data, indent=2))
                        
                        # Update displayed content
                        self.file_content_lines = json.dumps(json_data, indent=2).splitlines()
                        
                        print(term.move(6, 2) + term.green(f"Removed '{location}' successfully!"))
                    except Exception as e:
                        print(term.move(6, 2) + term.red(f"Error saving file: {str(e)}"))
                        
                    print(term.move(8, 2) + "Press any key to continue...")
                    term.inkey()
                break
            elif key.name == 'KEY_ESCAPE':
                break
                
    def remove_category(self):
        """Remove a category from the current JSON file"""
        if not self.viewing_file or not self.file_path:
            return
        
        # Get current file content as JSON
        try:
            with open(self.file_path, 'r') as f:
                json_data = json.loads(f.read())
        except Exception:
            json_data = {}
            
        # Filter out "locations" to handle separately
        categories = [key for key in json_data.keys() if key != "locations"]
        
        if not categories:
            print(term.clear)
            print(term.move(2, 2) + term.bold("No categories to remove"))
            print(term.move(4, 2) + "This file doesn't have any categories to remove.")
            print(term.move(6, 2) + "Press any key to continue...")
            term.inkey()
            return
            
        # Show the selection menu
        selected = 0
        
        while True:
            print(term.clear)
            print(term.move(2, 2) + term.bold("Select a category to remove:"))
            
            # Calculate visible range
            max_display = term.height - 10
            start_idx = max(0, selected - max_display//2)
            end_idx = min(len(categories), start_idx + max_display)
            
            # Show categories
            for i, cat in enumerate(categories[start_idx:end_idx]):
                idx = i + start_idx
                value_str = str(json_data[cat])
                if len(value_str) > 30:
                    value_str = value_str[:27] + "..."
                    
                if idx == selected:
                    print(term.move(4 + i, 4) + term.reverse(f"▶ {cat}: {value_str}"))
                else:
                    print(term.move(4 + i, 4) + f"  {cat}: {value_str}")
                    
            print(term.move(term.height - 4, 2) + "Use arrow keys to navigate, Enter to select, ESC to cancel")
            
            key = term.inkey()
            
            if key.name == 'KEY_UP' and selected > 0:
                selected -= 1
            elif key.name == 'KEY_DOWN' and selected < len(categories) - 1:
                selected += 1
            elif key.name == 'KEY_ENTER' or key == '\n':
                category = categories[selected]
                
                # Confirm deletion
                print(term.clear)
                print(term.move(2, 2) + term.bold(f"Confirm removal of category: {category}"))
                print(term.move(4, 2) + "Are you sure? (y/n)")
                
                confirm_key = term.inkey()
                if confirm_key.lower() == 'y':
                    # Remove the category
                    del json_data[category]
                    
                    # Save back to file
                    try:
                        with open(self.file_path, 'w') as f:
                            f.write(json.dumps(json_data, indent=2))
                        
                        # Update displayed content
                        self.file_content_lines = json.dumps(json_data, indent=2).splitlines()
                        
                        print(term.move(6, 2) + term.green(f"Removed category '{category}' successfully!"))
                    except Exception as e:
                        print(term.move(6, 2) + term.red(f"Error saving file: {str(e)}"))
                        
                    print(term.move(8, 2) + "Press any key to continue...")
                    term.inkey()
                break
            elif key.name == 'KEY_ESCAPE':
                break