from search_functions import load_posts
import networkx as nx
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import string
import matplotlib.pyplot as plt
import random
import re
from nltk import ngrams
from collections import Counter
import List_of_compounds

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Constants for weighting
POST_WEIGHT = 20
COMMENT_WEIGHT = 2
UPVOTE_WEIGHT = 0.01


class Subject:
    def __init__(self, name):
        self.name = name
        self.posts = []
        self.total_upvotes = 0
        self.total_comments = 0


class User:
    def __init__(self, id):
        self.id = id
        self.subject_interactions = defaultdict(lambda: {'posts': 0, 'comments': 0, 'upvotes': 0})


def preprocess_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    return tokens


# New function for topic modeling preprocessing
def preprocess_for_topic_modeling(text):
    # If text is already a list of tokens
    if isinstance(text, list):
        # Convert each token to lowercase and remove non-alphabetic characters
        tokens = [re.sub(r'[^a-zA-Z]', '', token.lower()) for token in text]
    else:
        # If it's a string, process it as before
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        tokens = word_tokenize(text)

    # Remove stopwords and short words
    stop_words = set(stopwords.words('english'))
    custom_stop_words = {'would', 'also', 'get', 'im', 'ive', 'take', 'taking', 'day', 'deleted', 'removed', 'yes',
                         'no', 'dont', 'like'}
    stop_words.update(custom_stop_words)
    tokens = [token for token in tokens if token not in stop_words and len(token) > 2]

    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]

    return tokens


def create_bigrams(corpus, min_count=5):
    # Flatten the corpus to create bigrams across all documents
    all_tokens = [token for doc in corpus for token in doc]

    # Create bigrams
    bigrams = list(ngrams(all_tokens, 2))

    # Count bigram frequencies
    bigram_freq = Counter(bigrams)

    # Filter bigrams by frequency
    frequent_bigrams = {b: c for b, c in bigram_freq.items() if c >= min_count}

    # Create a set of frequent bigrams for faster lookup
    frequent_bigram_set = set(frequent_bigrams.keys())

    # Function to add bigrams to a document
    def add_bigrams_to_doc(doc):
        result = []
        i = 0
        while i < len(doc) - 1:
            if (doc[i], doc[i + 1]) in frequent_bigram_set:
                result.append(f"{doc[i]}_{doc[i + 1]}")
                i += 2
            else:
                result.append(doc[i])
                i += 1
        if i == len(doc) - 1:
            result.append(doc[-1])
        return result

    # Apply bigram creation to each document
    corpus_with_bigrams = [add_bigrams_to_doc(doc) for doc in corpus]

    return corpus_with_bigrams, frequent_bigrams


# New function for sentiment analysis preprocessing
def preprocess_for_sentiment(text):
    # If text is a list of tokens
    if isinstance(text, list):
        # Convert each token to lowercase and remove non-alphabetic characters
        cleaned_tokens = [re.sub(r'[^a-zA-Z]', '', token.lower()) for token in text]
        # Join the cleaned tokens back into a single string
        text = ' '.join(cleaned_tokens)
    elif isinstance(text, str):
        # If it's a string, process it as before
        text = re.sub(r'[^a-zA-Z\s]', '', text.lower())

    return text


# Create dictionaries for each list
peptides_dict = {item: 'Peptides' for item in List_of_compounds.peptides}
nootropics_dict = {item: 'Nootropics' for item in List_of_compounds.nootropics}
genres_dict = {item: 'Genres' for item in List_of_compounds.genres}
other_nootropics_dict = {item: 'other_nootropics' for item in List_of_compounds.other_nootropics}
vitamins_minerals_dict = {item: 'vitamins_minerals' for item in List_of_compounds.vitamins_minerals}
herbal_extracts_dict = {item: 'herbal_extracts' for item in List_of_compounds.herbal_extracts}
amino_acids_dict = {item: 'amino_acids' for item in List_of_compounds.amino_acids}
stimulants_dict = {item: 'stimulants' for item in List_of_compounds.stimulants}
adaptogens_dict = {item: 'adaptogens' for item in List_of_compounds.adaptogens}
cholinergics_dict = {item: 'Genres' for item in List_of_compounds.cholinergics}
racetams_dict = {item: 'racetams' for item in List_of_compounds.racetams}
# Combine dictionaries into a single dictionary
combined_dict = {**peptides_dict, **nootropics_dict, **genres_dict, **other_nootropics_dict, **vitamins_minerals_dict,
                 **herbal_extracts_dict, **amino_acids_dict, **stimulants_dict, **adaptogens_dict, **cholinergics_dict,
                 **racetams_dict}


def find_list_name(item, lookup_dict):
    return lookup_dict.get(item, None)


def create_sna_graph(data):
    G = nx.Graph()
    subjects = {}
    users = {}

    for subject_name, posts in data.items():
        subject = Subject(subject_name)
        subjects[subject_name] = subject
        G.add_node(subject_name, nootropic_type=find_list_name(subject_name, combined_dict))

        for post in posts:
            subject.posts.append(post)
            subject.total_upvotes += post.upvotes
            subject.total_comments += len(post.comments)

            if post.author not in users:
                users[post.author] = User(post.author)
            users[post.author].subject_interactions[subject_name]['posts'] += 1

            # Randomly select one comment if there are any
            available_comments = post.comments.copy()

            for _ in range(min(3, len(available_comments))):
                if available_comments:
                    # Randomly select a comment
                    comment_author, comment_text = random.choice(available_comments)

                    # Remove the selected comment from the available pool
                    available_comments.remove((comment_author, comment_text))

                    if comment_author not in users:
                        users[comment_author] = User(comment_author)
                    users[comment_author].subject_interactions[subject_name]['comments'] += 1
                else:
                    # No more comments available, break the loop
                    break
            # without random:
            # if not available_comments:
            #     print("No comments available.")
            # else:
            #     for comment_author, comment_text in available_comments:
            #         if comment_author not in users:
            #             users[comment_author] = User(comment_author)
            #         users[comment_author].subject_interactions[subject_name]['comments'] += 1

    edge_count = 0
    for user in users.values():
        # Limit to maximum 100 different posts per user
        limited_interactions = dict(sorted(user.subject_interactions.items(),
                                           key=lambda x: x[1]['posts'] + x[1]['comments'],
                                           reverse=True))

        subjects_interacted = list(limited_interactions.keys())
        for i in range(len(subjects_interacted)):
            for j in range(i + 1, len(subjects_interacted)):
                subject1, subject2 = subjects_interacted[i], subjects_interacted[j]
                weight = (
                        limited_interactions[subject1]['posts'] * POST_WEIGHT +
                        limited_interactions[subject1]['comments'] * COMMENT_WEIGHT +
                        limited_interactions[subject2]['posts'] * POST_WEIGHT +
                        limited_interactions[subject2]['comments'] * COMMENT_WEIGHT
                )
                if G.has_edge(subject1, subject2):
                    G[subject1][subject2]['weight'] += weight
                else:
                    G.add_edge(subject1, subject2, weight=weight)
                    edge_count += 1

    print(f"Total edges created: {edge_count}")
    print(f"Graph edges after creation: {G.number_of_edges()}")

    # Check for isolated nodes
    isolated_nodes = list(nx.isolates(G))
    print(f"Number of isolated nodes: {len(isolated_nodes)}")
    if isolated_nodes:
        print(f"Isolated nodes: {isolated_nodes[:5]} ... (showing first 5)")

    # Check degree distribution
    degrees = [d for n, d in G.degree()]
    print(f"Degree distribution: min={min(degrees)}, max={max(degrees)}, avg={sum(degrees) / len(degrees):.2f}")
    print_edge_list(G)
    return G, subjects, users


def print_edge_list(G, limit=None):
    print("\nEdge List:")
    print("Subject 1\tSubject 2\tWeight")
    print("-" * 40)

    # Sort edges by weight in descending order
    sorted_edges = sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)

    # Print edges (limited if specified)
    for i, (node1, node2, data) in enumerate(sorted_edges):
        if limit and i >= limit:
            break
        print(f"{node1}\t{node2}\t{data['weight']:.2f}")

    if limit and len(sorted_edges) > limit:
        print(f"... (showing top {limit} out of {len(sorted_edges)} edges)")


def load_and_preprocess_data(file_path):
    data = load_posts(file_path)
    graph, subjects, users = create_sna_graph(data)

    preprocessed_data = {}
    for subject_name, posts in data.items():
        preprocessed_data[subject_name] = []
        for post in posts:
            preprocessed_post = post._replace(
                query=preprocess_text(post.query),
                title=preprocess_text(post.title),
                comments=[(author, preprocess_text(comment)) for author, comment in post.comments]
            )
            preprocessed_data[subject_name].append(preprocessed_post)

    print(f"Graph created with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print(f"Preprocessed data for {len(preprocessed_data)} subjects")

    return graph, preprocessed_data


# Usage
if __name__ == "__main__":
    graph, preprocessed_data = load_and_preprocess_data("data_collected/posts.pkl")
    nx.write_graphml(graph, "graph.graphml")
