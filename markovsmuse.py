import random
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, Menu, filedialog, messagebox
from collections import defaultdict
import json
from datetime import datetime
import os
from pathlib import Path
import time
import threading

# Move the SHORTCUTS dictionary to the top with other constants
SHORTCUTS = {
    '<Control-g>': 'Generate Poem',
    '<Control-s>': 'Save Poem',
    '<Control-o>': 'Load Poem',
    '<Control-b>': 'Browse Poems',
    '<Control-z>': 'Undo',
    '<Control-y>': 'Redo',
    '<Control-c>': 'Copy',
    '<Escape>': 'Clear'
}

# After imports and before poet_files dictionary
class PoemBrowser(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📚 Poem Browser")
        self.geometry("900x600")
        self.minsize(800, 400)
        
        # Configure grid weights for main window
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Apply current theme
        self.configure(bg=xp_colors['bg'])
        current_font = themes[theme_var.get()]['font']
        is_dark = theme_var.get() == "Dark Mode"
        text_color = 'white' if is_dark else 'black'
        
        # Create top control frame
        control_frame = tk.Frame(self, bg=xp_colors['frame_bg'], relief="groove", bd=2)
        control_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        control_frame.grid_columnconfigure(1, weight=1)
        
        # Add sort options
        sort_frame = tk.Frame(control_frame, bg=xp_colors['frame_bg'])
        sort_frame.grid(row=0, column=0, padx=10)
        
        tk.Label(sort_frame, text="Sort by:", font=current_font, 
                bg=xp_colors['frame_bg'], fg=text_color).pack(side=tk.LEFT)
        
        self.sort_var = tk.StringVar(value="Date (Newest)")
        sort_options = ["Date (Newest)", "Date (Oldest)", "Poet A-Z", "Poet Z-A", "Favorites First"]
        sort_menu = ttk.Combobox(sort_frame, textvariable=self.sort_var, 
                                values=sort_options, font=current_font, width=15,
                                foreground=text_color)
        sort_menu.pack(side=tk.LEFT, padx=5)
        sort_menu.bind('<<ComboboxSelected>>', lambda e: self.load_poem_list())
        
        # Add search (expandable)
        search_frame = tk.Frame(control_frame, bg=xp_colors['frame_bg'])
        search_frame.grid(row=0, column=1, sticky="ew", padx=10)
        search_frame.grid_columnconfigure(1, weight=1)  # Make entry expand
        
        tk.Label(search_frame, text="Search:", font=current_font, 
                bg=xp_colors['frame_bg'], fg=text_color).grid(row=0, column=0, padx=(0,5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_poems)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                              font=current_font)
        search_entry.grid(row=0, column=1, sticky="ew")
        
        # Create main content frame
        content_frame = tk.Frame(self, bg=xp_colors['bg'])
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        content_frame.grid_columnconfigure(1, weight=1)  # Make preview expand
        content_frame.grid_rowconfigure(0, weight=1)    # Make content expand vertically
        
        # Create poem list with scrollbar
        list_frame = tk.Frame(content_frame, bg=xp_colors['frame_bg'], relief="sunken", bd=1)
        list_frame.grid(row=0, column=0, sticky="ns", padx=(0,5))
        
        self.poem_list = tk.Listbox(list_frame, font=current_font, 
                                  bg=xp_colors['text_bg'],
                                  selectmode=tk.SINGLE,
                                  exportselection=False,
                                  width=45)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                command=self.poem_list.yview)
        self.poem_list.configure(yscrollcommand=scrollbar.set)
        
        self.poem_list.pack(side=tk.LEFT, fill="both")
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.poem_list.bind('<<ListboxSelect>>', self.show_selected_poem)
        
        # Create preview frame
        preview_frame = tk.Frame(content_frame, bg=xp_colors['frame_bg'], relief="sunken", bd=1)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        preview_frame.grid_rowconfigure(1, weight=1)    # Make text area expand
        preview_frame.grid_columnconfigure(0, weight=1) # Make preview expand horizontally
        
        # Preview header
        self.preview_header = tk.Label(preview_frame, text="", font=current_font,
                                     bg=xp_colors['frame_bg'], anchor="w", fg=text_color)
        self.preview_header.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Preview text
        self.preview_text = scrolledtext.ScrolledText(preview_frame, 
                                                    font=current_font,
                                                    bg=xp_colors['text_bg'],
                                                    wrap=tk.WORD, fg=text_color)
        self.preview_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Button frame
        button_frame = tk.Frame(preview_frame, bg=xp_colors['frame_bg'])
        button_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        
        # Action buttons
        buttons = [
            ("📝 Load", self.load_selected),
            ("🗑️ Delete", self.delete_selected),
            ("⭐ Favorite", self.toggle_favorite),
            ("📤 Export", self.export_selected)
        ]
        
        for i, (text, command) in enumerate(buttons):
            button_frame.grid_columnconfigure(i, weight=1)  # Make buttons expand equally
            tk.Button(button_frame, text=text, command=command,
                     font=current_font, bg=xp_colors['button'],
                     activebackground=xp_colors['highlight'], fg=text_color).grid(row=0, column=i, padx=2, sticky="ew")
        
        # Load poems
        self.load_poem_list()
        
        # Configure text colors for list and preview
        self.poem_list.configure(fg=text_color)
        self.preview_text.configure(fg=text_color)
        self.preview_header.configure(fg=text_color)
    
    def load_poem_list(self):
        """Load and display the list of saved poems"""
        self.poem_list.delete(0, tk.END)
        try:
            files = list(Path(SAVES_DIR).glob('*.json'))
            poems = []
            
            for file in files:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Add favorite status if not present
                    if 'favorite' not in data:
                        data['favorite'] = False
                    # Add file path for later use
                    data['file_path'] = file
                    poems.append(data)
            
            # Sort based on selected option
            sort_option = self.sort_var.get()
            if sort_option == "Date (Newest)":
                poems.sort(key=lambda x: x['date'], reverse=True)
            elif sort_option == "Date (Oldest)":
                poems.sort(key=lambda x: x['date'])
            elif sort_option == "Poet A-Z":
                poems.sort(key=lambda x: x['poet'])
            elif sort_option == "Poet Z-A":
                poems.sort(key=lambda x: x['poet'], reverse=True)
            elif sort_option == "Favorites First":
                poems.sort(key=lambda x: (not x['favorite'], x['date']), reverse=True)
            
            for data in poems:
                date = datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S")
                star = "⭐ " if data['favorite'] else "   "
                display_text = f"{star}{date.strftime('%Y-%m-%d %H:%M')} │ {data['poet']}"
                self.poem_list.insert(tk.END, display_text)
                self.poem_list.itemconfig(tk.END, {'bg': xp_colors['text_bg']})
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load poems: {str(e)}")
    
    def show_selected_poem(self, event=None):
        """Display the selected poem's content"""
        selection = self.poem_list.curselection()
        if not selection:
            return
            
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            file = files[selection[0]]
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update header with more metadata
            header = f"Poet: {data['poet']}\n"
            header += f"Date: {data['date']}\n"
            if 'devices' in data:
                header += f"Devices: {', '.join(data['devices'])}\n"
            if 'favorite' in data:
                header += f"Favorite: {'Yes' if data['favorite'] else 'No'}\n"
            if 'theme' in data:
                header += f"Theme: {data['theme']}\n"
            
            self.preview_header.config(text=header)
            
            # Update preview
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', data['text'])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load poem: {str(e)}")
    
    def filter_poems(self, *args):
        """Filter poems based on search text"""
        search_text = self.search_var.get().lower()
        self.poem_list.delete(0, tk.END)
        
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            for file in files:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    date = datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S")
                    display_text = f"{date.strftime('%Y-%m-%d %H:%M')} │ {data['poet']}"
                    if (search_text in display_text.lower() or 
                        search_text in data['text'].lower()):
                        self.poem_list.insert(tk.END, display_text)
                        self.poem_list.itemconfig(tk.END, {'bg': xp_colors['text_bg']})
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter poems: {str(e)}")
    
    def load_selected(self):
        """Load the selected poem into the main window"""
        selection = self.poem_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a poem to load!")
            return
            
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            file = files[selection[0]]
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Update main window
            text_output.delete("1.0", tk.END)
            text_output.insert("1.0", data["text"])
            
            # Update metadata if possible
            if data["poet"] in poet_files:
                poet_var.set(data["poet"])
            if data["theme"] in themes:
                theme_var.set(data["theme"])
                change_theme()
                
            self.destroy()  # Close browser window
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load poem: {str(e)}")
    
    def delete_selected(self):
        """Delete the selected poem"""
        selection = self.poem_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a poem to delete!")
            return
            
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this poem?"):
            return
            
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            file = files[selection[0]]
            os.remove(file)
            self.load_poem_list()  # Refresh the list
            self.preview_header.config(text="")
            self.preview_text.delete('1.0', tk.END)
            messagebox.showinfo("Success", "Poem deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete poem: {str(e)}")
    
    def toggle_favorite(self):
        """Toggle favorite status of the selected poem"""
        selection = self.poem_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a poem to favorite!")
            return
            
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            file = files[selection[0]]
            
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Toggle favorite status
            data['favorite'] = not data.get('favorite', False)
            
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            
            # Refresh the list to show updated status
            self.load_poem_list()
            
            status = "added to" if data['favorite'] else "removed from"
            messagebox.showinfo("Success", f"Poem {status} favorites!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update favorite status: {str(e)}")
    
    def export_selected(self):
        """Export the selected poem"""
        selection = self.poem_list.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a poem to export!")
            return
            
        try:
            files = sorted(Path(SAVES_DIR).glob('*.json'), key=os.path.getmtime, reverse=True)
            file = files[selection[0]]
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filepath = filedialog.asksaveasfilename(
                initialdir=".",
                title="Export Poem",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")]
            )
            
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Generated by Markov's Muse\n")
                    f.write(f"Poet: {data['poet']}\n")
                    f.write(f"Date: {data['date']}\n")
                    if 'devices' in data:
                        f.write(f"Devices: {', '.join(data['devices'])}\n")
                    f.write("\n" + "="*40 + "\n\n")
                    f.write(data['text'])
                    
                messagebox.showinfo("Success", "Poem exported successfully!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export poem: {str(e)}")

# Step 1: Data Collection - Dictionary containing available poets and their respective text files
poet_files = {
    "Emily Dickinson": "dickinson.txt",  # Replace with actual file paths
    "Robert Frost": "frost.txt",
    "William Shakespeare": "shakespeare.txt",
    "Edgar Allan Poe": "poe.txt",
}

# List of available poetic devices that the user can apply to the poem
poetic_devices = [
    "Alliteration",
    "Repetition", 
    "Rhyme",  # This will become a parent option
    "Metaphor"
]

# Add rhyme scheme options
rhyme_schemes = [
    "AABB (Paired)",
    "ABAB (Alternating)",
    "ABBA (Enclosed)"
]

# Add this to your constants section
themes = {
    "Default (Cute)": {
        'bg': '#F8F0FF',           # Soft lavender background
        'button': '#E8D5F0',       # Soft lavender button
        'highlight': '#D4B8E8',    # Medium lavender highlight
        'border': '#C8A4D4',       # Darker lavender border
        'title': '#B088C9',        # Deep lavender title
        'text_bg': '#FDF4FF',      # Almost white lavender text background
        'frame_bg': '#F4E6FF',     # Light lavender frame background
        'font': ("Comic Sans MS", 11),  # Playful font
        'title_font': ("Comic Sans MS", 14, "bold")
    },
    "Vaporwave": {
        'bg': '#FF6AD5',           # Hot pink
        'button': '#C774E8',       # Purple
        'highlight': '#AD8CFF',    # Light purple
        'border': '#94D0FF',       # Light blue
        'title': '#FF8DC7',        # Pink
        'text_bg': '#FFCEF3',      # Light pink
        'frame_bg': '#CAADFF',     # Soft purple
        'font': ("VT323", 12),     # Retro digital font (fallback: "Courier")
        'title_font': ("VT323", 16, "bold")
    },
    "Dark Mode": {
        'bg': '#1A1A1A',           # Almost black
        'button': '#333333',       # Dark gray
        'highlight': '#4A4A4A',    # Medium gray
        'border': '#2A2A2A',       # Darker gray
        'title': '#8A2BE2',        # Bright purple
        'text_bg': '#2D2D2D',      # Dark gray
        'frame_bg': '#242424',     # Very dark gray
        'font': ("Consolas", 11),  # Modern monospace
        'title_font': ("Consolas", 14, "bold")
    },
    "Medieval": {
        'bg': '#8B4513',           # Saddle brown
        'button': '#CD853F',       # Peru
        'highlight': '#DEB887',    # Burly wood
        'border': '#8B7355',       # Dark goldenrod
        'title': '#800000',        # Maroon
        'text_bg': '#F5DEB3',      # Wheat
        'frame_bg': '#D2B48C',     # Tan
        'font': ("Old English Text MT", 11),  # Medieval font (fallback: "Times New Roman")
        'title_font': ("Old English Text MT", 14, "bold")
    }
}

# Update the saves directory to use user's documents folder
def get_save_directory():
    """Get or create the save directory in user's documents folder"""
    if os.name == 'nt':  # Windows
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
    else:  # macOS and Linux
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
    
    save_path = os.path.join(docs_path, 'MarkovsMuse', 'saved_poems')
    
    # Create directory if it doesn't exist
    Path(save_path).mkdir(parents=True, exist_ok=True)
    
    return save_path

# Replace the SAVES_DIR constant with this
SAVES_DIR = get_save_directory()

# Function to preprocess the text and build the Markov chain
def preprocess_text(file_path, depth=2):
    """
    Reads the poet's text file, processes it, and creates a Markov transition matrix
    to generate more coherent lines of poetry.
    
    :param file_path: Path to the text file of the poet
    :param depth: Number of words to use as context for the Markov model (bigram or trigram)
    :return: A dictionary representing the transition probabilities for the Markov chain
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            if not text:
                print(f"Warning: {file_path} is empty")
                return defaultdict(lambda: defaultdict(int))
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return defaultdict(lambda: defaultdict(int))
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return defaultdict(lambda: defaultdict(int))

    # Remove Roman numerals (common in classic poetry collections)
    text = re.sub(r'\b[IVXLCDM]+\b', '', text)

    # Extract words while preserving only alphabetical words (removes numbers and symbols)
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

    # Stop words to exclude common but unhelpful words
    stop_words = {
        "a", "an", "the", "and", "or", "but", "is", "in", "on", "at", "by", "with",
        "of", "to", "for", "as", "was", "were", "be", "am", "are", "it", "this", "that"
    }
    words = [word for word in words if word not in stop_words]

    # Create a Markov transition matrix using n-grams for better coherence
    transition_matrix = defaultdict(lambda: defaultdict(int))

    for i in range(len(words) - depth):
        key = tuple(words[i:i + depth])  # Use 'depth' words as context
        next_word = words[i + depth]
        transition_matrix[key][next_word] += 1  # Count occurrences

    return transition_matrix

def get_rhyme_pattern(word):
    """Get the rhyming pattern of a word's ending"""
    word = word.lower().strip('.,!?;:')
    if len(word) < 3:
        return None
        
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    
    # Find last stressed syllable
    last_vowel_pos = -1
    vowel_count = 0
    for i in range(len(word) - 1, -1, -1):
        if word[i] in vowels:
            if vowel_count == 0:
                last_vowel_pos = i
            vowel_count += 1
            # Include consecutive vowels
            while i > 0 and word[i - 1] in vowels:
                i -= 1
                
    if last_vowel_pos == -1:
        return None
        
    # Get the rhyming part (from last stressed syllable to end)
    rhyme_part = word[max(0, last_vowel_pos - 1):]
    
    # Handle special cases
    if rhyme_part.endswith('e') and len(rhyme_part) > 2:  # Silent e
        rhyme_part = rhyme_part[:-1]
    
    # Get vowel and consonant patterns separately
    vowel_pattern = ''.join(c for c in rhyme_part if c in vowels)
    consonant_pattern = ''.join(c for c in rhyme_part if c in consonants)
    
    return (vowel_pattern, consonant_pattern) if vowel_pattern else None

def find_rhyming_pairs(lines):
    """
    Find pairs of lines that could rhyme based on their last words.
    Uses strict AABB rhyming pattern with precise sound matching.
    """
    pairs = []
    common_words = {
        'the', 'and', 'but', 'or', 'if', 'of', 'to', 'in', 'on', 'at', 'a', 'an', 'for', 'with',
        'is', 'was', 'were', 'be', 'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'shall', 'can', 'us', 'me', 'we',
        'they', 'them', 'him', 'her', 'his', 'their', 'our', 'your', 'my', 'so', 'go', 'no',
        'here', 'there', 'where', 'when', 'then', 'than', 'this', 'that', 'these', 'those',
        'through', 'though', 'although', 'yet', 'still', 'just', 'now', 'how', 'who', 'what'
    }
    
    # Process lines in pairs for AABB pattern
    for i in range(0, len(lines)-1, 2):
        if i + 1 >= len(lines):
            break
            
        words1 = lines[i].split()
        words2 = lines[i+1].split()
        
        if not words1 or not words2:
            continue
            
        last_word1 = words1[-1]
        last_word2 = words2[-1]
        
        # Skip common words, short words, and identical words
        if (last_word1.lower() in common_words or 
            last_word2.lower() in common_words or
            len(last_word1) < 3 or len(last_word2) < 3 or
            last_word1.lower() == last_word2.lower()):
            continue
            
        pattern1 = get_rhyme_pattern(last_word1)
        pattern2 = get_rhyme_pattern(last_word2)
        
        if pattern1 and pattern2:
            vowels1, cons1 = pattern1
            vowels2, cons2 = pattern2
            
            # Perfect rhyme: same vowel and consonant patterns
            if vowels1 == vowels2 and cons1 == cons2:
                pairs.append((i, i+1, 4))
            # Strong rhyme: same vowel pattern, similar consonants
            elif vowels1 == vowels2 and len(set(cons1) & set(cons2)) >= max(1, len(cons1) // 2):
                pairs.append((i, i+1, 3))
            # Assonance: same vowel pattern
            elif vowels1 == vowels2 and len(vowels1) >= 2:
                pairs.append((i, i+1, 2))
            # Weak rhyme: similar ending sound
            elif vowels1[-1:] == vowels2[-1:] and cons1[-1:] == cons2[-1:]:
                pairs.append((i, i+1, 1))
    
    return pairs

# Function to apply multiple poetic devices to the generated poem
def apply_poetic_devices(poem, devices):
    """
    Enhances the generated poem by applying selected poetic devices.
    
    :param poem: The poem text as a string
    :param devices: A list of poetic devices selected by the user
    :return: Modified poem with applied poetic effects
    """
    lines = poem.split("\n")

    if "Alliteration" in devices:
        # Enhanced alliteration that actually creates alliterative patterns
        new_lines = []
        consonant_clusters = {
            'ch': [], 'sh': [], 'th': [], 'wh': [], 'ph': [],
            'b': [], 'c': [], 'd': [], 'f': [], 'g': [], 'h': [], 
            'j': [], 'k': [], 'l': [], 'm': [], 'n': [], 'p': [], 
            'q': [], 'r': [], 's': [], 't': [], 'v': [], 'w': [], 
            'x': [], 'y': [], 'z': []
        }
        
        for line in lines:
            words = [w for w in line.split() if len(w) >= 2]  # Only consider words of 2+ characters
            if not words:
                new_lines.append(line)
                continue
            
            # Categorize words by their starting sounds
            for word in words:
                word_lower = word.lower()
                # Skip single letters or very short fragments
                if len(word_lower) < 2:
                    continue
                    
                # Check for consonant clusters first
                first_two = word_lower[:2]
                if first_two in consonant_clusters and len(word) >= 3:  # Ensure word is long enough
                    consonant_clusters[first_two].append(word)
                    continue
                
                # Check for single consonants
                if word_lower[0] in consonant_clusters and len(word) >= 3:  # Ensure word is long enough
                    consonant_clusters[word_lower[0]].append(word)
            
            # Try to create alliteration
            most_common_sound = None
            max_words = 1  # Start at 1 to ensure we have enough words
            
            for sound, word_list in consonant_clusters.items():
                # Only consider sounds that have enough valid words
                if len(word_list) > max_words and all(len(w) >= 3 for w in word_list):
                    max_words = len(word_list)
                    most_common_sound = sound
            
            if most_common_sound and len(consonant_clusters[most_common_sound]) >= 2:
                # Create new line with alliteration
                alliterative_words = [w for w in consonant_clusters[most_common_sound][:3] 
                                    if len(w) >= 3]  # Additional length check
                remaining_words = [w for w in words 
                                 if w not in alliterative_words 
                                 and len(w) >= 3][:2]  # Only use valid remaining words
                
                if len(alliterative_words) >= 2:  # Ensure we have at least 2 alliterative words
                    new_line = ' '.join(alliterative_words + remaining_words)
                    new_lines.append(new_line.capitalize())
                else:
                    new_lines.append(line)
                
                # Clear the used words
                consonant_clusters[most_common_sound] = []
            else:
                new_lines.append(line)
            
            # Clear all categorized words for the next line
            for sound in consonant_clusters:
                consonant_clusters[sound] = []
        
        lines = new_lines

    if "Repetition" in devices and len(lines) > 2:
        # Repeats a phrase from the first line in every second line
        repeated_phrase = lines[0].split()[:3]  # First 3 words of first line
        if repeated_phrase:
            for i in range(1, len(lines), 2):
                lines[i] = lines[i] + " " + " ".join(repeated_phrase)

    if "Rhyme" in devices:
        new_lines = []
        used_lines = set()
        
        # Find rhyming pairs
        rhyme_pairs = find_rhyming_pairs(lines)
        
        # Sort by score
        rhyme_pairs.sort(key=lambda x: x[2], reverse=True)
        
        # Apply rhymes in order of best scores
        for i, j, score in rhyme_pairs:
            if i not in used_lines and j not in used_lines:
                new_lines.extend([lines[i], lines[j]])
                used_lines.add(i)
                used_lines.add(j)
        
        # Add remaining lines
        for i, line in enumerate(lines):
            if i not in used_lines:
                new_lines.append(line)
        
        lines = new_lines

    if "Metaphor" in devices:
        # Replaces common words with metaphorical descriptions
        metaphor_dict = {
            "moon": "a silver lantern",
            "sun": "a golden eye",
            "river": "a winding ribbon",
            "tree": "a silent guardian",
            "sky": "a vast ocean",
            "wind": "a whispering voice",
            "stars": "celestial diamonds",
            "clouds": "wandering dreamers",
            "night": "a velvet shroud"
        }
        for i in range(len(lines)):
            for key, value in metaphor_dict.items():
                lines[i] = lines[i].replace(key, value)

    return "\n".join(lines)

# Function to generate a thoughtful poem using the Markov chain model
def generate_poem(start_word, num_lines, transition_matrix, devices, depth=2):
    """
    Generates a poem using a Markov chain with simpler rhyming.
    """
    def get_rhyme_ending(word):
        """Get the rhyming ending of a word"""
        if len(word) < 4:
            return None
            
        # Common rhyming patterns with their variants
        patterns = {
            'ing': ['ing', 'ring', 'sing', 'wing'],
            'ight': ['ight', 'ite', 'yte', 'eight'],
            'ound': ['ound', 'owned'],
            'ead': ['ead', 'ed', 'eed'],
            'ame': ['ame', 'aim'],
            'ay': ['ay', 'ey', 'eigh'],
            'ear': ['ear', 'eer', 'ere'],
            'ine': ['ine', 'ign'],
            'all': ['all', 'awl'],
            'ow': ['ow', 'oe', 'o'],
            'iss': ['iss', 'is'],
            'est': ['est', 'essed']
        }
        
        # Check for pattern matches
        word = word.lower()
        for main_pattern, variants in patterns.items():
            if any(word.endswith(v) for v in variants):
                return main_pattern
        return word[-2:] if len(word) > 3 else None

    def find_rhyming_word(word, available_words):
        """Find a word that rhymes with the given word"""
        if not word:
            return None
        ending = get_rhyme_ending(word)
        if not ending:
            return None
            
        candidates = [w for w in available_words 
                     if len(w) >= 4 and w != word and get_rhyme_ending(w) == ending]
        return random.choice(candidates) if candidates else None

    def generate_line(start_words, target_end=None):
        """Generate a line with optional target ending"""
        line = list(start_words)
        if target_end:
            line.append(target_end)
            return line
            
        for _ in range(8):  # Keep lines reasonably short
            if len(line) >= 4:  # If line long enough
                break
            key = tuple(line[-depth:])
            if key not in transition_matrix:
                break
            next_words = list(transition_matrix[key].keys())
            if not next_words:
                break
            next_word = random.choices(next_words, 
                                     weights=[transition_matrix[key][w] for w in next_words])[0]
            line.append(next_word)
        return line if len(line) >= 4 else None

    # Collect all available words
    available_words = set()
    for words in transition_matrix.values():
        available_words.update(words.keys())

    poem_lines = []
    i = 0
    while i < num_lines - 1:  # Process pairs of lines
        # Generate first line
        line1 = generate_line(start_word)
        if not line1:
            start_word = random.choice(list(transition_matrix.keys()))
            continue
            
        # Try to find a rhyming word for second line
        rhyme_word = find_rhyming_word(line1[-1], available_words)
        if rhyme_word:
            line2 = generate_line(random.choice(list(transition_matrix.keys())), rhyme_word)
            if line2:
                poem_lines.extend([' '.join(line1).capitalize(),
                                 ' '.join(line2).capitalize()])
                i += 2
                start_word = random.choice(list(transition_matrix.keys()))
                continue
        
        # If no rhyme found, just add the first line
        poem_lines.append(' '.join(line1).capitalize())
        i += 1
        start_word = random.choice(list(transition_matrix.keys()))

    # Add final line if needed
    if i < num_lines:
        if line1 := generate_line(start_word):
            poem_lines.append(' '.join(line1).capitalize())

    return apply_poetic_devices("\n".join(poem_lines), devices)

# Function to handle poem generation in the UI
def on_generate():
    """
    Triggers poem generation when the "Generate" button is pressed.
    """
    selected_poet = poet_var.get()
    num_lines = int(lines_var.get())
    selected_devices = [device for device, var in device_vars.items() if var.get()]

    if selected_poet and num_lines > 0:
        file_path = poet_files[selected_poet]
        try:
            transition_matrix = preprocess_text(file_path)
            if not transition_matrix:
                text_output.delete("1.0", tk.END)
                text_output.insert(tk.INSERT, "Error: Could not generate poem from empty text file")
                return
                
            start_word = random.choice(list(transition_matrix.keys()))
            poem = generate_poem(start_word, num_lines, transition_matrix, selected_devices)
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.INSERT, poem)
        except Exception as e:
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.INSERT, f"Error generating poem: {e}")

# Add this before the GUI Setup section
def copy_text():
    """
    Copies the text from the text output area to the clipboard with better error handling
    and user feedback.
    """
    try:
        text = text_output.get("1.0", "end-1c").strip()
        if not text:
            copy_button.config(text="❌ No text to copy", bg="#FFB6B6")
            root.after(1000, lambda: copy_button.config(text="📋 Copy to Clipboard", bg="SystemButtonFace"))
            return
            
        root.clipboard_clear()
        root.clipboard_append(text)
        root.clipboard_get()  # Verify copy worked
        root.update()  # Required for Linux systems
        
        # Visual feedback
        copy_button.config(text="✓ Copied!", bg="#90EE90")
        root.after(1000, lambda: copy_button.config(text="📋 Copy to Clipboard", bg="SystemButtonFace"))
        
    except tk.TclError as e:
        print(f"Clipboard error: {e}")
        copy_button.config(text="❌ Copy failed", bg="#FFB6B6")
        root.after(1000, lambda: copy_button.config(text="📋 Copy to Clipboard", bg="SystemButtonFace"))
    except Exception as e:
        print(f"Copy failed: {e}")
        copy_button.config(text="❌ Copy failed", bg="#FFB6B6")
        root.after(1000, lambda: copy_button.config(text="📋 Copy to Clipboard", bg="SystemButtonFace"))

# Update apply_xp_style to accept a theme name
def apply_xp_style(theme_name="Default (Cute)"):
    style = ttk.Style()
    style.theme_use('clam')
    
    xp_colors = themes[theme_name]
    
    style.configure('TButton', 
                   padding=5,
                   relief="raised",
                   background=xp_colors['button'])
    
    style.configure('TCombobox',
                   fieldbackground=xp_colors['text_bg'],
                   background=xp_colors['button'])
    
    style.configure('TSpinbox',
                   fieldbackground=xp_colors['text_bg'],
                   background=xp_colors['button'])
    
    return xp_colors

# Also need to define create_poetic_device_frame before it's used
def create_poetic_device_frame(parent):
    device_frame = tk.Frame(parent, bg=xp_colors['frame_bg'], relief="groove", bd=2)
    device_frame.pack(pady=5, padx=10, fill="x")
    
    # Use theme font for header
    tk.Label(device_frame, text="Poetic Devices", 
            font=themes[theme_var.get()]['font'], 
            bg=xp_colors['frame_bg'], 
            fg=xp_colors['title']).pack(anchor="w", pady=2)
    
    device_vars = {}
    for device in poetic_devices:
        if device == "Rhyme":
            rhyme_frame = tk.Frame(device_frame, bg=xp_colors['frame_bg'])
            rhyme_frame.pack(anchor="w", padx=20)
            
            rhyme_var = tk.BooleanVar()
            device_vars[device] = rhyme_var
            rhyme_cb = tk.Checkbutton(rhyme_frame, text=device, variable=rhyme_var,
                                    font=themes[theme_var.get()]['font'],
                                    bg=xp_colors['frame_bg'],
                                    activebackground=xp_colors['frame_bg'],
                                    selectcolor=xp_colors['frame_bg'],
                                    command=lambda: toggle_rhyme_schemes(rhyme_var.get()))
            rhyme_cb.pack(anchor="w")
            
            scheme_frame = tk.Frame(rhyme_frame, bg=xp_colors['frame_bg'])
            scheme_frame.pack(anchor="w", padx=30)
            
            scheme_var = tk.StringVar(value="AABB (Paired)")
            device_vars["rhyme_scheme"] = scheme_var
            
            tk.Label(scheme_frame, text="Scheme:", 
                    font=themes[theme_var.get()]['font'],
                    bg=xp_colors['frame_bg']).pack(side=tk.LEFT, padx=(0, 5))
            
            for scheme in rhyme_schemes:
                tk.Radiobutton(scheme_frame, text=scheme, variable=scheme_var,
                             value=scheme, font=themes[theme_var.get()]['font'],
                             bg=xp_colors['frame_bg'],
                             activebackground=xp_colors['frame_bg'],
                             selectcolor=xp_colors['frame_bg'],
                             state="disabled").pack(side=tk.LEFT, padx=5)
        else:
            device_vars[device] = tk.BooleanVar()
            tk.Checkbutton(device_frame, text=device, variable=device_vars[device],
                          font=themes[theme_var.get()]['font'],
                          bg=xp_colors['frame_bg'],
                          activebackground=xp_colors['frame_bg'],
                          selectcolor=xp_colors['frame_bg']).pack(anchor="w", padx=20)
    
    return device_vars

def toggle_rhyme_schemes(enabled):
    """Enable/disable rhyme scheme options based on Rhyme checkbox"""
    state = "normal" if enabled else "disabled"
    for widget in scheme_frame.winfo_children():
        if isinstance(widget, tk.Radiobutton):
            widget.configure(state=state)

# Add these functions before the GUI Setup section
def show_popup(event):
    """Show right-click menu"""
    popup_menu.tk_popup(event.x_root, event.y_root)

def fade_color(widget, from_color, to_color, steps=10, duration=200):
    """Smoothly transition between two colors"""
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def update_color(step):
        if step <= steps:
            t = step / steps
            current_rgb = tuple(int(from_rgb[j] + (to_rgb[j] - from_rgb[j]) * t) for j in range(3))
            current_color = rgb_to_hex(current_rgb)
            widget.configure(bg=current_color)
            # Schedule next update
            widget.after(duration // steps, update_color, step + 1)
    
    from_rgb = hex_to_rgb(from_color)
    to_rgb = hex_to_rgb(to_color)
    update_color(0)

def change_theme(event=None):
    """Change the application theme"""
    global xp_colors
    theme_name = theme_var.get()
    xp_colors = apply_xp_style(theme_name)
    current_font = themes[theme_name]['font']
    title_font = themes[theme_name]['title_font']
    
    # Update all existing widgets with new colors and fonts
    root.configure(bg=xp_colors['bg'])
    
    # Update title bar for dark mode
    if theme_name == "Dark Mode":
        title_frame.configure(bg='black')
        title_label.configure(bg='black', fg='white', font=title_font)
    else:
        title_frame.configure(bg=xp_colors['title'])
        title_label.configure(bg=xp_colors['title'], fg='white', font=title_font)
    
    # Update all frames and their contents
    content_frame.configure(bg=xp_colors['bg'])
    
    # Update main section labels and their contents
    for frame in [theme_frame, poet_frame, lines_frame]:
        if isinstance(frame, tk.LabelFrame):
            frame.configure(
                bg=xp_colors['frame_bg'],
                fg='white' if theme_name == "Dark Mode" else 'black',  # Update frame label color
                font=current_font  # Update frame label font
            )
        for widget in frame.winfo_children():
            if isinstance(widget, (tk.Label, ttk.Label)):
                widget.configure(
                    bg=xp_colors['frame_bg'],
                    fg='white' if theme_name == "Dark Mode" else 'black',
                    font=current_font
                )
            elif isinstance(widget, ttk.Combobox):
                widget.configure(
                    foreground='white' if theme_name == "Dark Mode" else 'black',
                    font=current_font
                )
            elif isinstance(widget, ttk.Spinbox):
                widget.configure(
                    foreground='white' if theme_name == "Dark Mode" else 'black',
                    font=current_font
                )
    
    # Update poetic devices section
    for widget in content_frame.winfo_children():
        if isinstance(widget, tk.Frame):  # Main poetic devices frame
            widget.configure(bg=xp_colors['frame_bg'])
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(
                        bg=xp_colors['frame_bg'],
                        fg='white' if theme_name == "Dark Mode" else 'black',
                        font=current_font
                    )
                elif isinstance(child, tk.Checkbutton):
                    child.configure(
                        bg=xp_colors['frame_bg'],
                        fg='white' if theme_name == "Dark Mode" else 'black',
                        activebackground=xp_colors['frame_bg'],
                        activeforeground='white' if theme_name == "Dark Mode" else 'black',
                        selectcolor=xp_colors['frame_bg'] if theme_name == "Dark Mode" else 'white',
                        font=current_font
                    )
                elif isinstance(child, tk.Frame):  # Rhyme frame
                    child.configure(bg=xp_colors['frame_bg'])
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Label):
                            subchild.configure(
                                bg=xp_colors['frame_bg'],
                                fg='white' if theme_name == "Dark Mode" else 'black',
                                font=current_font
                            )
                        elif isinstance(subchild, tk.Checkbutton):
                            subchild.configure(
                                bg=xp_colors['frame_bg'],
                                fg='white' if theme_name == "Dark Mode" else 'black',
                                activebackground=xp_colors['frame_bg'],
                                activeforeground='white' if theme_name == "Dark Mode" else 'black',
                                selectcolor=xp_colors['frame_bg'] if theme_name == "Dark Mode" else 'white',
                                font=current_font
                            )
                        elif isinstance(subchild, tk.Frame):  # Scheme frame
                            subchild.configure(bg=xp_colors['frame_bg'])
                            for item in subchild.winfo_children():
                                if isinstance(item, tk.Label):
                                    item.configure(
                                        bg=xp_colors['frame_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )
                                elif isinstance(item, tk.Radiobutton):
                                    item.configure(
                                        bg=xp_colors['frame_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        activebackground=xp_colors['frame_bg'],
                                        activeforeground='white' if theme_name == "Dark Mode" else 'black',
                                        selectcolor=xp_colors['frame_bg'] if theme_name == "Dark Mode" else 'white',
                                        font=current_font
                                    )
    
    # Update text output area
    text_output.configure(
        bg=xp_colors['text_bg'],
        fg='white' if theme_name == "Dark Mode" else 'black',
        font=current_font
    )
    
    # Update all buttons in the main button frame
    button_frame.configure(bg=xp_colors['frame_bg'])
    all_buttons = [
        generate_button,
        copy_button, 
        save_button,
        load_button,
        export_button,
        browse_button,
        help_button
    ]
    
    for button in all_buttons:
        button.configure(
            bg=xp_colors['button'],
            activebackground=xp_colors['highlight'],
            font=current_font,
            fg='white' if theme_name == "Dark Mode" else 'black'
        )
    
    # Update the Generate Poem button separately since it might have different styling
    generate_button.configure(
        bg=xp_colors['button'],
        activebackground=xp_colors['highlight'],
        font=current_font,
        fg='white' if theme_name == "Dark Mode" else 'black'
    )
    
    # Update status bar
    status_bar.configure(
        bg=xp_colors['frame_bg'],
        fg='white' if theme_name == "Dark Mode" else 'black',
        font=current_font
    )
    
    # Update any poem browsers
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.configure(bg=xp_colors['bg'])
            
            # Update all text widgets in the poem browser
            for child in widget.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=xp_colors['frame_bg'])
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Frame):
                            subchild.configure(bg=xp_colors['frame_bg'])
                            for item in subchild.winfo_children():
                                if isinstance(item, (tk.Label, ttk.Label)):
                                    item.configure(
                                        bg=xp_colors['frame_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )
                                elif isinstance(item, ttk.Combobox):  # Add this for sort options
                                    item.configure(
                                        foreground='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )
                                elif isinstance(item, tk.Listbox):
                                    item.configure(
                                        bg=xp_colors['text_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )
                                elif isinstance(item, scrolledtext.ScrolledText):
                                    item.configure(
                                        bg=xp_colors['text_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )
                                elif isinstance(item, tk.Label):
                                    item.configure(
                                        bg=xp_colors['frame_bg'],
                                        fg='white' if theme_name == "Dark Mode" else 'black',
                                        font=current_font
                                    )

# Add these functions for save/load functionality
def save_current_poem():
    """Save the current poem with metadata"""
    current_text = text_output.get("1.0", "end-1c").strip()
    if not current_text:
        messagebox.showwarning("No Poem", "There is no poem to save!")
        return
        
    # Create poem data
    poem_data = {
        "text": current_text,
        "poet": poet_var.get(),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "theme": theme_var.get(),
        "devices": [device for device, var in device_vars.items() if var.get()],
        "favorite": False  # Initialize as not favorite
    }
    
    # Generate filename based on date
    filename = f"poem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SAVES_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(poem_data, f, indent=4)
        messagebox.showinfo("Success", f"Poem saved to:\n{filepath}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save poem: {str(e)}")

def load_saved_poem():
    """Load a previously saved poem"""
    files = [f for f in os.listdir(SAVES_DIR) if f.endswith('.json')]
    if not files:
        messagebox.showinfo("No Saves", "No saved poems found!")
        return
        
    filepath = filedialog.askopenfilename(
        initialdir=SAVES_DIR,
        title="Select Poem",
        filetypes=[("JSON files", "*.json")]
    )
    
    if not filepath:
        return
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            poem_data = json.load(f)
            
        # Update UI with loaded poem
        text_output.delete("1.0", tk.END)
        text_output.insert("1.0", poem_data["text"])
        
        # Update metadata if possible
        if poem_data["poet"] in poet_files:
            poet_var.set(poem_data["poet"])
        if poem_data["theme"] in themes:
            theme_var.set(poem_data["theme"])
            change_theme()
            
        # Show metadata in status
        status = f"Loaded poem by {poem_data['poet']} ({poem_data['date']})"
        messagebox.showinfo("Poem Loaded", status)
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load poem: {str(e)}")

def export_poem():
    """Export the current poem as a formatted text file"""
    current_text = text_output.get("1.0", "end-1c").strip()
    if not current_text:
        messagebox.showwarning("No Poem", "There is no poem to export!")
        return
        
    filepath = filedialog.asksaveasfilename(
        initialdir=".",
        title="Export Poem",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")]
    )
    
    if not filepath:
        return
        
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"Generated by Markov's Muse\n")
            f.write(f"Poet: {poet_var.get()}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n" + "="*40 + "\n\n")
            # Write poem
            f.write(current_text)
            
        messagebox.showinfo("Success", "Poem exported successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export poem: {str(e)}")

# Add status bar to main window
def show_status(message, duration=3000):
    """Show a message in the status bar and clear it after duration"""
    status_bar.config(text=message)
    root.after(duration, lambda: status_bar.config(text="Ready"))

# Add keyboard shortcut handling
def handle_shortcut(event):
    """Handle keyboard shortcuts and show in status bar"""
    if event.keysym == 'g' and event.state & 4:  # Control-G
        show_status("Generating poem...")
        on_generate()
    elif event.keysym == 's' and event.state & 4:  # Control-S
        show_status("Saving poem...")
        save_current_poem()
    elif event.keysym == 'z' and event.state & 4:  # Control-Z
        undo_action()
    elif event.keysym == 'y' and event.state & 4:  # Control-Y
        redo_action()
    # ... add other shortcuts

# GUI Setup
root = tk.Tk()
root.title("🌸 Poem Generator 🌸")
root.geometry("700x650")
root.minsize(600, 500)

# Make the root window scalable
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Apply Windows XP theme
xp_colors = apply_xp_style()
root.configure(bg=xp_colors['bg'])

# Create theme variable after root
theme_var = tk.StringVar(value="Default (Cute)")

# Create main container that will scale
main_container = tk.Frame(root, bg=xp_colors['bg'])
main_container.grid(row=0, column=0, sticky="nsew")
main_container.grid_columnconfigure(0, weight=1)
main_container.grid_rowconfigure(1, weight=1)

# Create title bar with XP style
title_frame = tk.Frame(main_container, bg=xp_colors['title'], relief="raised", bd=1)
title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
title_label = tk.Label(title_frame, text="~ Markov's Muse - Poem Generator ~", 
                      font=themes["Default (Cute)"]['title_font'], 
                      bg=xp_colors['title'],
                      fg="white", pady=5)
title_label.pack()

# Add status bar
status_bar = tk.Label(main_container, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                     font=themes["Default (Cute)"]['font'], bg=xp_colors['frame_bg'])
status_bar.grid(row=2, column=0, sticky="ew")

# Create scrollable content frame
canvas = tk.Canvas(main_container, bg=xp_colors['bg'])
canvas.grid(row=1, column=0, sticky="nsew")

scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
scrollbar.grid(row=1, column=1, sticky="ns")

canvas.configure(yscrollcommand=scrollbar.set)

# Create content frame inside canvas
content_frame = tk.Frame(canvas, bg=xp_colors['bg'], relief="groove", bd=2)
canvas.create_window((0, 0), window=content_frame, anchor="nw", tags="content")
content_frame.grid_columnconfigure(0, weight=1)

# Function to update canvas scroll region
def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    width = main_container.winfo_width() - scrollbar.winfo_width()
    canvas.itemconfig("content", width=width)

content_frame.bind("<Configure>", update_scrollregion)

# Add theme frame
theme_frame = tk.LabelFrame(content_frame, text="Theme", 
                          font=themes["Default (Cute)"]['font'], 
                          bg=xp_colors['frame_bg'])
theme_frame.pack(padx=10, pady=5, fill="x")

theme_dropdown = ttk.Combobox(theme_frame, textvariable=theme_var, 
                            values=list(themes.keys()), 
                            font=themes["Default (Cute)"]['font'])
theme_dropdown.pack(pady=5, padx=10, fill="x")
theme_dropdown.bind('<<ComboboxSelected>>', change_theme)

# Poet selection with XP styling
poet_frame = tk.LabelFrame(content_frame, text="Select Poet", 
                          font=("Tahoma", 11, "bold"), bg=xp_colors['frame_bg'])
poet_frame.pack(padx=10, pady=5, fill="x")

poet_var = tk.StringVar()
poet_dropdown = ttk.Combobox(poet_frame, textvariable=poet_var, 
                            values=list(poet_files.keys()), font=("Tahoma", 11))
poet_dropdown.pack(pady=5, padx=10, fill="x")
poet_dropdown.current(0)

# Line count with XP styling
lines_frame = tk.LabelFrame(content_frame, text="Number of Lines", 
                           font=("Tahoma", 11, "bold"), bg=xp_colors['frame_bg'])
lines_frame.pack(padx=10, pady=5, fill="x")

lines_var = tk.StringVar()
lines_entry = ttk.Spinbox(lines_frame, from_=1, to=50, textvariable=lines_var, 
                         width=5, font=("Tahoma", 11))
lines_entry.pack(pady=5)
lines_entry.set(10)

# Add poetic devices frame
device_vars = create_poetic_device_frame(content_frame)

# Generate button with XP styling
generate_button = tk.Button(content_frame, text="✨ Generate Poem ✨", 
                          command=on_generate, font=("Tahoma", 11, "bold"),
                          bg=xp_colors['button'], relief="raised",
                          activebackground=xp_colors['highlight'],
                          activeforeground="white")
generate_button.pack(pady=10)

# Output text area with XP styling
text_output = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, 
                                      width=60, height=12, 
                                      font=("Lucida Console", 11),
                                      bg=xp_colors['text_bg'], relief="sunken")
text_output.pack(pady=10, padx=10, fill="both", expand=True)

# Copy button with XP styling
copy_button = tk.Button(content_frame, text="📋 Copy to Clipboard", 
                       command=copy_text, font=("Tahoma", 11),
                       bg=xp_colors['button'], relief="raised",
                       activebackground=xp_colors['highlight'])
copy_button.pack(pady=5)

# Add right-click menu
popup_menu = Menu(root, tearoff=0)
popup_menu.add_command(label="Copy", command=copy_text)

# Bind events
text_output.bind("<Button-3>", show_popup)  # Right click
text_output.bind("<Control-c>", lambda e: copy_text())  # Ctrl+C shortcut

# Add buttons to the UI (add after the copy button)
button_frame = tk.Frame(content_frame, bg=xp_colors['frame_bg'])
button_frame.pack(pady=5)

save_button = tk.Button(button_frame, text="💾 Save Poem", 
                       command=save_current_poem, 
                       font=themes["Default (Cute)"]['font'],
                       bg=xp_colors['button'], relief="raised",
                       activebackground=xp_colors['highlight'])
save_button.pack(side=tk.LEFT, padx=5)

load_button = tk.Button(button_frame, text="📂 Load Poem", 
                       command=load_saved_poem, 
                       font=themes["Default (Cute)"]['font'],
                       bg=xp_colors['button'], relief="raised",
                       activebackground=xp_colors['highlight'])
load_button.pack(side=tk.LEFT, padx=5)

export_button = tk.Button(button_frame, text="📤 Export", 
                         command=export_poem, 
                         font=themes["Default (Cute)"]['font'],
                         bg=xp_colors['button'], relief="raised",
                         activebackground=xp_colors['highlight'])
export_button.pack(side=tk.LEFT, padx=5)

# Add to the button frame creation
browse_button = tk.Button(button_frame, text="📚 Browse Poems", 
                         command=lambda: PoemBrowser(root),
                         font=themes["Default (Cute)"]['font'],
                         bg=xp_colors['button'], relief="raised",
                         activebackground=xp_colors['highlight'])
browse_button.pack(side=tk.LEFT, padx=5)

# Add mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# Add after the imports
class UndoRedoManager:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.undo_stack = []
        self.redo_stack = []
        self.last_state = ""
        
    def save_state(self):
        """Save current state for undo"""
        current_state = self.text_widget.get("1.0", "end-1c")
        if current_state != self.last_state:
            self.undo_stack.append(self.last_state)
            self.last_state = current_state
            self.redo_stack.clear()
            
    def undo(self):
        """Restore last state"""
        if self.undo_stack:
            current_state = self.text_widget.get("1.0", "end-1c")
            self.redo_stack.append(current_state)
            last_state = self.undo_stack.pop()
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", last_state)
            self.last_state = last_state
            show_status("Undo")
            
    def redo(self):
        """Redo last undone action"""
        if self.redo_stack:
            current_state = self.text_widget.get("1.0", "end-1c")
            self.undo_stack.append(current_state)
            next_state = self.redo_stack.pop()
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", next_state)
            self.last_state = next_state
            show_status("Redo")

# Create undo manager after text_output creation
undo_manager = UndoRedoManager(text_output)

# Update generate function to use undo manager
def on_generate():
    undo_manager.save_state()
    selected_poet = poet_var.get()
    num_lines = int(lines_var.get())
    selected_devices = [device for device, var in device_vars.items() if var.get()]

    if selected_poet and num_lines > 0:
        file_path = poet_files[selected_poet]
        try:
            transition_matrix = preprocess_text(file_path)
            if not transition_matrix:
                text_output.delete("1.0", tk.END)
                text_output.insert(tk.INSERT, "Error: Could not generate poem from empty text file")
                return
                
            start_word = random.choice(list(transition_matrix.keys()))
            poem = generate_poem(start_word, num_lines, transition_matrix, selected_devices)
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.INSERT, poem)
        except Exception as e:
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.INSERT, f"Error generating poem: {e}")

# Add undo/redo functions
def undo_action():
    undo_manager.undo()

def redo_action():
    undo_manager.redo()

def show_shortcuts():
    """Display keyboard shortcuts help dialog"""
    dialog = tk.Toplevel(root)
    dialog.title("Keyboard Shortcuts")
    dialog.geometry("400x300")
    
    # Apply current theme
    dialog.configure(bg=xp_colors['bg'])
    current_font = themes[theme_var.get()]['font']
    
    # Create scrollable text area
    text = scrolledtext.ScrolledText(dialog, font=current_font, 
                                   bg=xp_colors['text_bg'],
                                   wrap=tk.WORD)
    text.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Add shortcuts
    text.insert("1.0", "Keyboard Shortcuts:\n\n")
    for shortcut, description in SHORTCUTS.items():
        text.insert("end", f"{shortcut:<15} - {description}\n")
    
    text.configure(state="disabled")

# Add help button to button frame
help_button = tk.Button(button_frame, text="⌨ Shortcuts", 
                       command=show_shortcuts,
                       font=themes["Default (Cute)"]['font'],
                       bg=xp_colors['button'],
                       activebackground=xp_colors['highlight'])
help_button.pack(side=tk.LEFT, padx=5)

# Add keyboard shortcuts binding after all GUI elements are created
root.bind_all('<Key>', handle_shortcut)

# Start the main loop
root.mainloop()
