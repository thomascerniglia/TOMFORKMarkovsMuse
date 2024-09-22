import random
import re
from collections import defaultdict

# Step 1: Data Collection
corpus = # replace with actual file path

# Step 2: Text Preprocessing
# Open the text file and read its contents
with open(corpus, 'r') as f:
    text = f.read()
    
    # Split the text into individual words using regular expressions
    # The regular expression \W+ matches one or more non-word characters (e.g., spaces, punctuation)
    words = re.split(r'\W+', text.lower())
    
    # Define a set of stop words to ignore in the analysis
    stop_words = set(["a", "an", "the", "and", "or", "but", "is", "in", "on", "at", "by", "with"])
    
    # Remove stop words from the list of words
    words = [word for word in words if word not in stop_words]

# Step 3: Building the Markov Chain Model
# Create a transition matrix to store the word-to-word probabilities
transition_matrix = defaultdict(dict)
for i in range(len(words) - 1):
    # Get the current word and the next word in the sequence
    word = words[i]
    next_word = words[i + 1]
    
    # If the next word is not already in the transition matrix, add it with a count of 1
    if next_word not in transition_matrix[word]:
        transition_matrix[word][next_word] = 1
    # Otherwise, increment the count for the next word
    else:
        transition_matrix[word][next_word] += 1

# Step 4: Generating Text
def generate_text(start_word, length):
    # Initialize the generated text with the starting word
    text = [start_word]
    
    # Generate the specified number of words
    for i in range(length):
        # Get the last word in the generated text
        word = text[-1]
        
        # Get the list of possible next words and their probabilities
        next_words = list(transition_matrix[word].keys())
        probs = [transition_matrix[word][next_word] / sum(transition_matrix[word].values()) for next_word in next_words]
        
        # Generate a random number between 0 and 1
        rand_num = random.random()
        
        # Select a random next word based on the transition matrix probabilities
        cum_prob = 0.0
        for j, next_word in enumerate(next_words):
            cum_prob += probs[j]
            if rand_num < cum_prob:
                text.append(next_word)
                break
        
        # If the random number is greater than the cumulative probability, choose a different word
        else:
            next_word = random.choice(list(transition_matrix[word].keys()))
            text.append(next_word)
    
    # Join the generated words into a single string
    return ' '.join(text)

# Example usage:
print(generate_text("once", 20))
