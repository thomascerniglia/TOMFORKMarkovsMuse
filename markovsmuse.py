import random
import re
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import defaultdict

# Step 1: Data Collection
poet_files = {
    "Emily Dickinson": "dickinson.txt",  # Replace with actual file paths
    "Robert Frost": "frost.txt",
    "William Shakespeare": "shakespeare.txt",
    "Edgar Allan Poe": "poe.txt",
}

poetic_devices = [
    "None",
    "Alliteration",
    "Repetition",
    "Rhyme",
    "Metaphor"
]

# Function to preprocess the text and build the Markov chain
def preprocess_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    words = re.split(r'\W+', text.lower())
    stop_words = set(["a", "an", "the", "and", "or", "but", "is", "in", "on", "at", "by", "with"])
    words = [word for word in words if word not in stop_words]

    transition_matrix = defaultdict(dict)
    for i in range(len(words) - 1):
        word, next_word = words[i], words[i + 1]
        transition_matrix[word][next_word] = transition_matrix[word].get(next_word, 0) + 1

    return transition_matrix

# Function to apply poetic devices
def apply_poetic_device(poem, device):
    lines = poem.split("\n")

    if device == "Alliteration":
        for i in range(len(lines)):
            words = lines[i].split()
            if words:
                first_letter = words[0][0] if words[0] else ''
                words = [w for w in words if w.startswith(first_letter)]
                lines[i] = " ".join(words) if words else lines[i]

    elif device == "Repetition":
        if lines:
            repeated_phrase = lines[0].split()[:3]  # First 3 words of the first line
            if repeated_phrase:
                for i in range(1, len(lines), 2):
                    lines[i] = lines[i] + " " + " ".join(repeated_phrase)

    elif device == "Rhyme":
        for i in range(len(lines) - 1):
            words = lines[i].split()
            if words:
                last_word = words[-1]
                lines[i] = f"{' '.join(words)} ({last_word})"

    elif device == "Metaphor":
        metaphor_dict = {
            "moon": "a silver lantern",
            "sun": "a golden eye",
            "river": "a winding ribbon",
            "tree": "a silent guardian",
            "sky": "a vast ocean",
            "wind": "a whispering voice"
        }
        for i in range(len(lines)):
            for key, value in metaphor_dict.items():
                lines[i] = lines[i].replace(key, value)

    return "\n".join(lines)

# Function to generate a poem
def generate_poem(start_word, num_lines, transition_matrix, poetic_device):
    poem = []
    
    for _ in range(num_lines):
        line = [start_word]
        for _ in range(random.randint(4, 10)):  # Random words per line
            word = line[-1]
            next_words = list(transition_matrix[word].keys())
            if not next_words:
                break  # Stop if there are no next words
            next_word = random.choices(next_words, 
                                       weights=[transition_matrix[word][nw] for nw in next_words])[0]
            line.append(next_word)
        poem.append(' '.join(line).capitalize())

        # Choose a new random starting word for variety
        start_word = random.choice(list(transition_matrix.keys()))

    # Apply poetic device
    return apply_poetic_device("\n".join(poem), poetic_device)

# Function to handle poem generation in the UI
def on_generate():
    selected_poet = poet_var.get()
    num_lines = int(lines_var.get())
    selected_device = device_var.get()

    if selected_poet and num_lines > 0:
        file_path = poet_files[selected_poet]
        transition_matrix = preprocess_text(file_path)
        start_word = random.choice(list(transition_matrix.keys()))
        poem = generate_poem(start_word, num_lines, transition_matrix, selected_device)
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.INSERT, poem)

# GUI Setup
root = tk.Tk()
root.title("🌸 Poem Generator 🌸")
root.geometry("600x550")
root.configure(bg="#FFF5E1")  # Soft pastel background

# Custom fonts & styles
title_font = ("Edwardian Script ITC", 24, "bold")
label_font = ("Garamond", 14)
button_font = ("Garamond", 12, "bold")

# Title Label
title_label = tk.Label(root, text="~ Poem Generator ~", font=title_font, bg="#FFF5E1", fg="#9055A2")
title_label.pack(pady=10)

# Poet selection
poet_frame = tk.Frame(root, bg="#FFF5E1")
poet_frame.pack(pady=5)
ttk.Label(poet_frame, text="📜 Select a Poet:", font=label_font, background="#FFF5E1").pack(side=tk.LEFT, padx=5)
poet_var = tk.StringVar()
poet_dropdown = ttk.Combobox(poet_frame, textvariable=poet_var, values=list(poet_files.keys()), font=label_font)
poet_dropdown.pack(side=tk.LEFT, padx=5)
poet_dropdown.current(0)

# Line selection
lines_frame = tk.Frame(root, bg="#FFF5E1")
lines_frame.pack(pady=5)
ttk.Label(lines_frame, text="✍️ Number of Lines:", font=label_font, background="#FFF5E1").pack(side=tk.LEFT, padx=5)
lines_var = tk.StringVar()
lines_entry = ttk.Spinbox(lines_frame, from_=1, to=50, textvariable=lines_var, width=5, font=label_font)
lines_entry.pack(side=tk.LEFT, padx=5)
lines_entry.set(10)  # Default to 10 lines

# Poetic Device selection
device_frame = tk.Frame(root, bg="#FFF5E1")
device_frame.pack(pady=5)
ttk.Label(device_frame, text="🎭 Poetic Device:", font=label_font, background="#FFF5E1").pack(side=tk.LEFT, padx=5)
device_var = tk.StringVar()
device_dropdown = ttk.Combobox(device_frame, textvariable=device_var, values=poetic_devices, font=label_font)
device_dropdown.pack(side=tk.LEFT, padx=5)
device_dropdown.current(0)

# Generate button with cute colors
generate_button = tk.Button(root, text="✨ Generate Poem ✨", command=on_generate, font=button_font,
                            bg="#F3B0C3", fg="white", activebackground="#C683D7", activeforeground="white",
                            relief=tk.RAISED, bd=3, padx=10, pady=5)
generate_button.pack(pady=15)

# Poem output area with fancy frame
output_frame = tk.Frame(root, bg="#FDF0F0", relief=tk.SUNKEN, bd=2)
output_frame.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)
text_output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=60, height=10, font=("Courier", 12),
                                        bg="#FEF9E7", fg="#5B4E77", relief=tk.FLAT, borderwidth=2)
text_output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Run the GUI
root.mainloop()
