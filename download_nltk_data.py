"""
Download all required NLTK data for the HR Project.
"""
import nltk
import ssl

# Fix SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print("Downloading NLTK data packages...")

# Download required packages
packages = [
    'punkt',           # Sentence tokenizer
    'stopwords',       # Stop words
    'wordnet',         # WordNet lexical database
    'averaged_perceptron_tagger',  # POS tagger
    'punkt_tab',       # Additional punkt data
]

for package in packages:
    try:
        print(f"\nDownloading {package}...")
        nltk.download(package, quiet=False)
        print(f"✓ {package} downloaded successfully")
    except Exception as e:
        print(f"✗ Error downloading {package}: {e}")

print("\n" + "="*60)
print("NLTK data download complete!")
print("="*60)
