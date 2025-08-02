from blessed import Terminal
import os
import json

class EditorTUI:
    """Text-based editor for JSON files in the navigator"""
    
    def __init__(self, file_path, content_lines, term=None):
        """Initialize the editor with file path and content"""
        self.file_path = file_path
        self.content_lines = content_lines.copy()  # Work on a copy of the content
        self.term = term or Terminal()
        
        self.cursor_row = 0
        self.cursor_col = 0
        self.viewport_offset = 0  # For scrolling vertically
        self.edit_mode = False
        self.status_message = f"Editing {os.path.basename(file_path)} - Press 'i' to enter edit mode, 'q' to quit"
        self.current_line = ""  # For line editing
        
        # Attempt to parse JSON to enable structured editing
        try:
            self.json_data = json.loads('\n'.join(content_lines))
            self.json_mode = True
        except json.JSONDecodeError:
            self.json_mode = False
    
    def run(self):
        """Run the editor interface and return updated content if saved"""
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            self.draw()
            
            while True:
                key = self.term.inkey()
                
                if not self.edit_mode:
                    # Navigation mode
                    if key.lower() == 'q':
                        return None  # Cancel without saving
                    elif key.lower() == 's':
                        return self.save_changes()
                    elif key.lower() == 'i':
                        self.edit_mode = True
                        self.status_message = "EDIT MODE - Press Esc to exit edit mode"
                    elif key.name == 'KEY_UP':
                        self.move_cursor_up()
                    elif key.name == 'KEY_DOWN':
                        self.move_cursor_down()
                    elif key.name == 'KEY_LEFT':
                        self.move_cursor_left()
                    elif key.name == 'KEY_RIGHT':
                        self.move_cursor_right()
                else:
                    # Edit mode
                    if key.name == 'KEY_ESCAPE':
                        self.edit_mode = False
                        self.status_message = f"Editing {os.path.basename(self.file_path)} - Press 'i' to enter edit mode, 's' to save, 'q' to quit"
                    elif key.name == 'KEY_ENTER':
                        self.insert_newline()
                    elif key.name == 'KEY_BACKSPACE':
                        self.handle_backspace()
                    elif key.name == 'KEY_DELETE':
                        self.handle_delete()
                    elif key.name == 'KEY_UP':
                        self.move_cursor_up()
                    elif key.name == 'KEY_DOWN':
                        self.move_cursor_down()
                    elif key.name == 'KEY_LEFT':
                        self.move_cursor_left()
                    elif key.name == 'KEY_RIGHT':
                        self.move_cursor_right()
                    elif not key.is_sequence:  # Regular character input
                        self.insert_character(key)
                
                self.draw()
    
    def draw(self):
        """Draw the editor interface"""
        height, width = self.term.height, self.term.width
        print(self.term.home + self.term.clear)
        
        # Draw header
        header = f"Editing: {self.file_path}"
        print(self.term.move(0, 0) + self.term.bold(header[:width]))
        
        # Calculate visible content range
        max_display_lines = height - 3  # Reserve lines for header and status
        visible_lines = self.content_lines[self.viewport_offset:self.viewport_offset + max_display_lines]
        
        # Draw content lines
        for i, line in enumerate(visible_lines):
            line_num = self.viewport_offset + i
            line_prefix = f"{line_num+1:4d} | "
            
            # If this is the cursor line and in edit mode, show cursor
            if line_num == self.cursor_row and self.edit_mode:
                if self.cursor_col > len(line):
                    pad_length = self.cursor_col - len(line)
                    line = line + " " * pad_length
                
                # Show cursor by highlighting the character at cursor position
                before_cursor = line[:self.cursor_col]
                cursor_char = line[self.cursor_col:self.cursor_col+1] if self.cursor_col < len(line) else " "
                after_cursor = line[self.cursor_col+1:] if self.cursor_col < len(line) else ""
                
                display_line = line_prefix + before_cursor + self.term.reverse(cursor_char) + after_cursor
            else:
                display_line = line_prefix + line
            
            # Highlight cursor line
            if line_num == self.cursor_row:
                print(self.term.move(i + 1, 0) + self.term.underline(display_line[:width]))
            else:
                print(self.term.move(i + 1, 0) + display_line[:width])
        
        # Draw status line
        status = self.status_message
        if self.json_mode:
            status += " [JSON]"
        
        print(self.term.move(height - 1, 0) + self.term.reverse(status[:width]))
    
    def move_cursor_up(self):
        """Move cursor up one line"""
        if self.cursor_row > 0:
            self.cursor_row -= 1
            # Adjust column if new line is shorter
            if self.cursor_col > len(self.content_lines[self.cursor_row]):
                self.cursor_col = len(self.content_lines[self.cursor_row])
            
            # Scroll if needed
            if self.cursor_row < self.viewport_offset:
                self.viewport_offset = self.cursor_row
    
    def move_cursor_down(self):
        """Move cursor down one line"""
        if self.cursor_row < len(self.content_lines) - 1:
            self.cursor_row += 1
            # Adjust column if new line is shorter
            if self.cursor_col > len(self.content_lines[self.cursor_row]):
                self.cursor_col = len(self.content_lines[self.cursor_row])
            
            # Scroll if needed
            if self.cursor_row >= self.viewport_offset + self.term.height - 3:
                self.viewport_offset = max(0, self.cursor_row - (self.term.height - 4))
    
    def move_cursor_left(self):
        """Move cursor left one character"""
        if self.cursor_col > 0:
            self.cursor_col -= 1
    
    def move_cursor_right(self):
        """Move cursor right one character"""
        if self.cursor_col < len(self.content_lines[self.cursor_row]):
            self.cursor_col += 1
    
    def insert_character(self, key):
        """Insert a character at the current cursor position"""
        current_line = self.content_lines[self.cursor_row]
        new_line = current_line[:self.cursor_col] + key + current_line[self.cursor_col:]
        self.content_lines[self.cursor_row] = new_line
        self.cursor_col += 1
    
    def insert_newline(self):
        """Insert a new line at the current cursor position"""
        current_line = self.content_lines[self.cursor_row]
        left_part = current_line[:self.cursor_col]
        right_part = current_line[self.cursor_col:]
        
        # Replace current line with left part
        self.content_lines[self.cursor_row] = left_part
        
        # Insert new line with right part
        self.content_lines.insert(self.cursor_row + 1, right_part)
        
        # Move cursor to beginning of new line
        self.cursor_row += 1
        self.cursor_col = 0
        
        # Adjust viewport if needed
        if self.cursor_row >= self.viewport_offset + self.term.height - 3:
            self.viewport_offset += 1
    
    def handle_backspace(self):
        """Handle backspace key in edit mode"""
        if self.cursor_col > 0:
            # Delete character before cursor
            current_line = self.content_lines[self.cursor_row]
            new_line = current_line[:self.cursor_col-1] + current_line[self.cursor_col:]
            self.content_lines[self.cursor_row] = new_line
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            # Join with previous line
            prev_line = self.content_lines[self.cursor_row - 1]
            current_line = self.content_lines[self.cursor_row]
            
            # Set cursor position to end of previous line
            self.cursor_col = len(prev_line)
            
            # Join lines
            self.content_lines[self.cursor_row - 1] = prev_line + current_line
            
            # Remove current line
            self.content_lines.pop(self.cursor_row)
            
            # Move cursor to previous line
            self.cursor_row -= 1
    
    def handle_delete(self):
        """Handle delete key in edit mode"""
        current_line = self.content_lines[self.cursor_row]
        
        if self.cursor_col < len(current_line):
            # Delete character at cursor
            new_line = current_line[:self.cursor_col] + current_line[self.cursor_col+1:]
            self.content_lines[self.cursor_row] = new_line
        elif self.cursor_row < len(self.content_lines) - 1:
            # Join with next line
            next_line = self.content_lines[self.cursor_row + 1]
            self.content_lines[self.cursor_row] = current_line + next_line
            
            # Remove next line
            self.content_lines.pop(self.cursor_row + 1)
    
    def save_changes(self):
        """Save changes and return updated content"""
        # If in JSON mode, try to validate JSON before saving
        if self.json_mode:
            try:
                json_content = '\n'.join(self.content_lines)
                json.loads(json_content)  # Validate JSON
                self.status_message = "JSON validated and saved"
                return self.content_lines
            except json.JSONDecodeError as e:
                self.status_message = f"Invalid JSON: {str(e)}"
                return None
        else:
            # For non-JSON files, just return updated content
            return self.content_lines

    @staticmethod
    def edit_file(file_path, content_lines=None):
        """Static method to create and run an editor instance for a file"""
        if content_lines is None:
            try:
                with open(file_path, 'r') as f:
                    content_lines = f.read().splitlines()
            except Exception as e:
                return None
        
        editor = EditorTUI(file_path, content_lines)
        return editor.run()