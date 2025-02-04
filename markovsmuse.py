import random
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, Menu, filedialog, messagebox
from collections import defaultdict
import json
from datetime import datetime
import os

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

# Add to your constants section
SAVES_DIR = "saved_poems"
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR)

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
    
    tk.Label(device_frame, text="Poetic Devices", font=("Tahoma", 12, "bold"), 
            bg=xp_colors['frame_bg'], fg=xp_colors['title']).pack(anchor="w", pady=2)
    
    device_vars = {}
    for device in poetic_devices:
        if device == "Rhyme":
            rhyme_frame = tk.Frame(device_frame, bg=xp_colors['frame_bg'])
            rhyme_frame.pack(anchor="w", padx=20)
            
            rhyme_var = tk.BooleanVar()
            device_vars[device] = rhyme_var
            rhyme_cb = tk.Checkbutton(rhyme_frame, text=device, variable=rhyme_var,
                                    font=("Tahoma", 11), bg=xp_colors['frame_bg'],
                                    activebackground=xp_colors['button'],
                                    command=lambda: toggle_rhyme_schemes(rhyme_var.get()))
            rhyme_cb.pack(anchor="w")
            
            scheme_frame = tk.Frame(rhyme_frame, bg=xp_colors['frame_bg'])
            scheme_frame.pack(anchor="w", padx=30)
            
            scheme_var = tk.StringVar(value="AABB (Paired)")
            device_vars["rhyme_scheme"] = scheme_var
            
            for scheme in rhyme_schemes:
                tk.Radiobutton(scheme_frame, text=scheme, variable=scheme_var,
                              value=scheme, font=("Tahoma", 10), 
                              bg=xp_colors['frame_bg'],
                              activebackground=xp_colors['frame_bg'],
                              state="disabled").pack(anchor="w")
        else:
            device_vars[device] = tk.BooleanVar()
            tk.Checkbutton(device_frame, text=device, variable=device_vars[device],
                          font=("Tahoma", 11), bg=xp_colors['frame_bg'],
                          activebackground=xp_colors['button']).pack(anchor="w", padx=20)
    
    return device_vars

def toggle_rhyme_schemes(enabled):
    """Enable/disable rhyme scheme options based on Rhyme checkbox"""
    state = "normal" if enabled else "disabled"
    for widget in root.winfo_children():
        if isinstance(widget, tk.Frame):
            for subwidget in widget.winfo_children():
                if isinstance(subwidget, tk.Radiobutton):
                    subwidget.configure(state=state)

# Add these functions before the GUI Setup section
def show_popup(event):
    """Show right-click menu"""
    popup_menu.tk_popup(event.x_root, event.y_root)

def change_theme(event=None):
    """Change the application theme"""
    global xp_colors
    theme_name = theme_var.get()
    xp_colors = apply_xp_style(theme_name)
    current_font = themes[theme_name]['font']
    title_font = themes[theme_name]['title_font']
    
    # Update all existing widgets with new colors and fonts
    root.configure(bg=xp_colors['bg'])
    
    # Update title
    title_frame.configure(bg=xp_colors['title'])
    title_label.configure(bg=xp_colors['title'], font=title_font)
    
    # Update all frames and their contents
    content_frame.configure(bg=xp_colors['bg'])
    
    # Update all frames and their children
    for frame in [poet_frame, lines_frame, theme_frame]:
        frame.configure(bg=xp_colors['frame_bg'])
        # Update frame label font
        if isinstance(frame, tk.LabelFrame):
            frame.configure(font=current_font)
        # Update all widgets in the frame
        for widget in frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Button)):
                widget.configure(font=current_font)
            elif isinstance(widget, ttk.Combobox):
                widget.configure(font=current_font)
            elif isinstance(widget, ttk.Spinbox):
                widget.configure(font=current_font)
    
    # Update poetic devices frame and its widgets
    for widget in content_frame.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.configure(bg=xp_colors['frame_bg'])
            if isinstance(widget, tk.LabelFrame):
                widget.configure(font=current_font)
            
            # First level - main frames
            for child in widget.winfo_children():
                if isinstance(child, (tk.Checkbutton, tk.Radiobutton, tk.Label)):
                    child.configure(bg=xp_colors['frame_bg'], font=current_font)
                
                # Second level - rhyme frame
                if isinstance(child, tk.Frame):
                    child.configure(bg=xp_colors['frame_bg'])
                    
                    # Third level - scheme frame
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Frame):
                            subchild.configure(bg=xp_colors['frame_bg'])
                            for radio in subchild.winfo_children():
                                if isinstance(radio, tk.Radiobutton):
                                    radio.configure(
                                        bg=xp_colors['frame_bg'],
                                        activebackground=xp_colors['frame_bg'],
                                        selectcolor=xp_colors['frame_bg'],
                                        font=current_font
                                    )
                        elif isinstance(subchild, (tk.Checkbutton, tk.Radiobutton, tk.Label)):
                            subchild.configure(bg=xp_colors['frame_bg'], font=current_font)
    
    # Update the new button frame and buttons
    button_frame.configure(bg=xp_colors['frame_bg'])
    for button in [save_button, load_button, export_button]:
        button.configure(
            bg=xp_colors['button'],
            activebackground=xp_colors['highlight'],
            font=current_font
        )
        if theme_name == "Dark Mode":
            button.configure(fg='white')
        else:
            button.configure(fg='black')

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
        "devices": [device for device, var in device_vars.items() if var.get()]
    }
    
    # Generate filename based on date
    filename = f"poem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SAVES_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(poem_data, f, indent=4)
        messagebox.showinfo("Success", "Poem saved successfully!")
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

# GUI Setup
root = tk.Tk()
root.title("🌸 Poem Generator 🌸")
root.geometry("700x650")
root.minsize(600, 500)  # Set minimum window size

# Make the root window scalable
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Apply Windows XP theme
xp_colors = apply_xp_style()
root.configure(bg=xp_colors['bg'])

# Create main container that will scale
main_container = tk.Frame(root, bg=xp_colors['bg'])
main_container.grid(row=0, column=0, sticky="nsew")
main_container.grid_columnconfigure(0, weight=1)
main_container.grid_rowconfigure(1, weight=1)  # Make content frame expandable

# Create title bar with XP style
title_frame = tk.Frame(main_container, bg=xp_colors['title'], relief="raised", bd=1)
title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
title_label = tk.Label(title_frame, text="~ Markov's Muse - Poem Generator ~", 
                      font=themes["Default (Cute)"]['title_font'], 
                      bg=xp_colors['title'], fg="white", pady=5)
title_label.pack()

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

# Add mouse wheel scrolling
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

# Start the main loop
root.mainloop()
