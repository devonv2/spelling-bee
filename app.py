from flask import Flask, request, render_template, session, jsonify
import random
from pip._vendor import requests
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'boobies'

found = []
points = 0
pairs = {}
hints = False
pangrams = [0,0]
tpoints = 0
lengths = defaultdict(lambda:defaultdict(lambda: 0))


def read_words(file):
    words = []
    try:
        with open(file, 'r') as f:
            for line in f:
                s = set()
                for char in line:
                    s.add(char)
                if len(line) > 4 and len(s) <= 7:
                    words.append(line.strip().upper())
    except FileNotFoundError:
        print(f"Error: {file} not found.")
    return words

def is_valid_word(word, letters, mandatory_letter):
    word = word.upper()
    if len(word) < 4:
        return (False, f"'{word.capitalize()}' is too short. Valid words are at least 4 letters.")
    if mandatory_letter not in word:
        return (False, f"'{word.capitalize()}' does not contain {mandatory_letter}.")
    for char in word:
        if char not in letters:
            return (False, f"'{word.capitalize()}' does not only use the given letters.")
    wordlist = read_words("words.txt")
    if word not in wordlist:
        return (False, f"'{word.capitalize()}' is not in the dictionary.")
    if check_pangram(word):
        return True, f"'{word.capitalize()}' is a pangram!"
    return True, f"'{word.capitalize()}' is a valid word!"

def clean_pairs(pairs):
    clean = {}
    for key in pairs:
        if pairs[key] == 0:
            continue
        else:
            clean[key] = pairs[key]
    if not bool(clean):
        clean = "You have found all the words!"
    return clean

def clean_lengths(lengths):
    #lengths is a nested default dict
    clean = defaultdict(lambda:defaultdict(lambda:0))
    for key in lengths:
        for key1 in lengths[key]:
            if lengths[key][key1] != 0:
                clean[key][key1] = lengths[key][key1]
    return clean

def check_pangram(word):
    #check if word is pangram
    s = set()
    for char in word:
        s.add(char)
    if len(s) < 7:
        return False
    return True

def generate_letters():
    words = read_words("words.txt")
    seven = []
    for word in words:
        if len(word) == 7 and check_pangram(word):
            seven.append(word)
    l_list = list(random.choice(seven))
    m = random.choice(l_list)
    random.shuffle(l_list)
    l = ''.join(l_list)
    return l, m

def find_words(letters, mandatory_letter):
    words = read_words("words.txt")
    finding = []
    for word in words:
        if is_valid_word(word, letters, mandatory_letter)[0]:
            finding.append(word)
    return finding

def add_points(word, pangram):
    points = 0
    if len(word) == 4: 
        points += 1
    else:
        points += len(word)
    if pangram:
        points += 7
    return points

def get_nyt_words():
    url = 'https://www.nytimes.com/puzzles/spelling-bee'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
    start_index = data.find("validLetters")
    #start_index = 22708
    #print(start_index)
    letters =  data[start_index + 14: start_index + 43]
    letters_list = [letters[2], letters[6], letters[10], letters[14], letters[18], letters[22], letters[26]]
    l = ''.join(letters_list)
    m = l[0]
    return l.upper(), m.upper()

def get_hints(l, m):
    pairs = defaultdict(lambda: 0)
    allwords = find_words(l, m)
    for word in allwords:
        word = word.capitalize()
        if word not in found:
            pair = word[0:2]
            pairs[pair] += 1
    pairs = dict(pairs)
    if not bool(pairs):
        pairs = "You have found all the words!"
    #return jsonify({'pairs':pairs})
    return pairs

@app.route('/')
def home():
    #session['found'] = []
    #session['points'] = 0
    #session['pairs'] = {}
    return render_template('index.html')#, found=sorted(found), points = points, pairs=session['pairs'])

@app.route('/shuffle', methods=['POST'])
def shuffle():
    word = session.get('l')
    shuffled = ''.join(random.sample(word, len(word)))
    #m = session.get('m')
    return jsonify({'letters': shuffled})

@app.route('/submit_letters', methods=['GET'])
def letters():
    global found, points
    found = []
    points = 0
    l = request.args.get('letters').upper()
    m = l[0].upper()
    if l == '0':
        l, m = generate_letters()
    elif l == '1':
        l, m = get_nyt_words()
    elif len(l) != 7:
        result = "Please submit 7 letters"
        return render_template('index.html', error=result)
    elif len(l) > len(set(l)):
        result = "Please make sure all letters are unique"
        return render_template('index.html', error=result)
    session['l'], session['m'] = l, m
    return render_template('index.html', l=l, m=m, found=found, points=points)


@app.route('/submit_word', methods=['POST'])
def submit_word():
    global points, hints, pairs, pangrams, lengths
    word = request.form['word'].capitalize()
    l = session.get('l')
    m = session.get('m')
    pangram = check_pangram(word)
    erm = is_valid_word(word, l, m)
    wp = word + '*'
    if word in found or wp in found:
        result = f"'{word}' was already found. Try something new, won't you?"
    elif erm[0]:
        result = erm[1]
        pair = word[0:2]
        lengths[pair][len(word)] -= 1
        lengths = clean_lengths(lengths)
        if pangram: 
            found.append(word + '*')
            pangrams[0] -= 1
            if len(word) == 7:
                pangrams[1] -= 1
        else:
            found.append(word)
        points += add_points(word, pangram)
        if hints:
            pairs[word[0:2]] -= 1
            pairs = clean_pairs(pairs)
    else:
        result = erm[1]
    return render_template('index.html', result=result, l=l, m=m, found=sorted(found), points=points, pairs=pairs, pangrams=pangrams, lengths=lengths)



@app.route('/get_hints', methods=['POST'])
def display_hints():
    global pairs, hints, pangrams, lengths
    lengths = defaultdict(lambda:defaultdict(lambda: 0))
    pangrams = [0,0]
    #lengths["Co"][4] = 5 -> 5 words that start with "Co" are 4 letters long
    #lengths["co"][4] = how many co words are 4 letters
    hints = True
    l = session.get('l')
    m = session.get('m')
    pairs = defaultdict(lambda: 0)
    allwords = find_words(l, m)
    for word in allwords:
        word = word.capitalize()
        wp = word + '*'
        if word not in found and wp not in found:
            pair = word[0:2]
            lengths[pair][len(word)] += 1
            pairs[pair] += 1
            if len(word) >= 7 and check_pangram(word):
                pangrams[0] += 1
                print(word)
                if len(word) == 7:
                    pangrams[1] += 1
    pairs = dict(pairs)
    #lengths = dict(lengths)
    if not bool(pairs):
        pairs = "You have found all the words!"
    
    #return jsonify({'pairs':pairs})
    return render_template('index.html', l=l, m=m, found=sorted(found), points=points, pairs=pairs, pangrams=pangrams, lengths = lengths)

@app.route('/reveal_words', methods=['POST'])
def reveal_words():
    global found, points
    l = session.get('l')
    m = session.get('m')
    words = []
    allwords = find_words(l, m)
    for word in allwords:
        word = word.capitalize()
        wp = word + '*'
        if word not in found and wp not in found:
            words.append(word)
    
    return render_template('index.html', l=l, m=m, allwords=words, found=found, points=points)

if __name__ == '__main__':
    app.run(debug=True)