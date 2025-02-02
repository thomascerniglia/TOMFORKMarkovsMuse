import random
import re
import tkinter as tk
from tkinter import ttk, scrolledtext
from collections import defaultdict

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
    "Rhyme",
    "Metaphor"
]

# Function to preprocess the text and build the Markov chain
def preprocess_text(file_path, depth=2):
    """
    Reads the poet's text file, processes it, and creates a Markov transition matrix
    to generate more coherent lines of poetry.
    
    :param file_path: Path to the text file of the poet
    :param depth: Number of words to use as context for the Markov model (bigram or trigram)
    :return: A dictionary representing the transition probabilities for the Markov chain
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

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
        # Retains words in each line that start with the same letter as the first word
        for i in range(len(lines)):
            words = lines[i].split()
            if words:
                first_letter = words[0][0] if words[0] else ''
                words = [w for w in words if w.startswith(first_letter)]
                lines[i] = " ".join(words) if words else lines[i]

    if "Repetition" in devices and len(lines) > 2:
        # Repeats a phrase from the first line in every second line
        repeated_phrase = lines[0].split()[:3]  # First 3 words of first line
        if repeated_phrase:
            for i in range(1, len(lines), 2):
                lines[i] = lines[i] + " " + " ".join(repeated_phrase)

    if "Rhyme" in devices:
        # Simulates rhyming by repeating the last word in brackets
        for i in range(len(lines) - 1):
            words = lines[i].split()
            if words:
                last_word = words[-1]
                lines[i] = f"{' '.join(words)} ({last_word})"

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
    Generates a poem using a Markov chain to create structured lines.

    :param start_word: Initial word tuple to begin the poem
    :param num_lines: Number of lines to generate
    :param transition_matrix: Precomputed Markov model from the poet's text
    :param devices: List of selected poetic devices
    :param depth: Number of words used as context for generating text
    :return: A formatted poem as a string
    """
    poem = []
    
    for _ in range(num_lines):
        line = list(start_word)
        for _ in range(random.randint(5, 12)):  # More varied word count per line
            key = tuple(line[-depth:])
            next_words = list(transition_matrix[key].keys())
            if not next_words:
                break  
            next_word = random.choices(next_words, weights=[transition_matrix[key][nw] for nw in next_words])[0]
            line.append(next_word)
        poem.append(' '.join(line).capitalize())

        # Choose a new starting phrase for variety
        start_word = random.choice(list(transition_matrix.keys()))

    return apply_poetic_devices("\n".join(poem), devices)

# Function to handle poem generation in the UI
def on_generate():
    """
    Triggers poem generation when the "Generate" button is pressed.
    Retrieves user input, processes text, and displays the output.
    """
    selected_poet = poet_var.get()
    num_lines = int(lines_var.get())
    selected_devices = [device for device, var in device_vars.items() if var.get()]

    if selected_poet and num_lines > 0:
        file_path = poet_files[selected_poet]
        transition_matrix = preprocess_text(file_path)
        start_word = random.choice(list(transition_matrix.keys()))
        poem = generate_poem(start_word, num_lines, transition_matrix, selected_devices)
        text_output.delete("1.0", tk.END)
        text_output.insert(tk.INSERT, poem)

# GUI Setup
root = tk.Tk()
root.title("🌸 Poem Generator 🌸")
root.geometry("650x600")
root.configure(bg="#FFF5E1")

# UI Elements
title_label = tk.Label(root, text="~ Poem Generator ~", font=("Edwardian Script ITC", 24, "bold"), bg="#FFF5E1", fg="#9055A2")
title_label.pack(pady=10)

poet_var = tk.StringVar()
poet_dropdown = ttk.Combobox(root, textvariable=poet_var, values=list(poet_files.keys()), font=("Garamond", 14))
poet_dropdown.pack(pady=5)
poet_dropdown.current(0)

lines_var = tk.StringVar()
lines_entry = ttk.Spinbox(root, from_=1, to=50, textvariable=lines_var, width=5, font=("Garamond", 14))
lines_entry.pack(pady=5)
lines_entry.set(10)

device_vars = {device: tk.BooleanVar() for device in poetic_devices}
for device, var in device_vars.items():
    tk.Checkbutton(root, text=device, variable=var, font=("Garamond", 14), bg="#FFF5E1").pack(anchor="w")

generate_button = tk.Button(root, text="✨ Generate Poem ✨", command=on_generate, font=("Garamond", 12, "bold"), bg="#F3B0C3")
generate_button.pack(pady=15)

text_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10, font=("Courier", 12), bg="#FEF9E7")
text_output.pack(pady=10, fill=tk.BOTH, expand=True)

root.mainloop()
