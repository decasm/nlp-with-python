import os
import sys
import json
import nltk
from nltk.stem.porter import *
from collections import Counter

try:
    directory = sys.args[1]
except:
    directory = '../review_json/'

def load_reviews(directory):
    file_names = os.listdir(directory)
    reviews = [json.loads(open(directory+fn, 'r').read()) for fn in file_names]
    reviews.sort(key=lambda r:len(r['text'])) # sort by length of review
    reviews = reviews[5:] # get rid of 5 shortest reviews
    for r in reviews:
        r.pop('by') # remove 'by' field in each review
    return reviews

reviews = load_reviews(directory)
reviews.sort(key=lambda r:r['release_year']) # sort by release_year
titles = {r['title']:r for r in reviews} # dict of reviews by title

####

# Corpus level analysis with set of reviews
# let's remember what we're working with:
len(reviews) # 7734 star-rated reviews
reviews.sort(key=lambda x:len(x['text']))
reviews[0] # shortest
reviews[-1] # longest

grammar = r"""
NP: {<JJ>*<NNS?>+}
    {<NNPS?>+}
"""
chunk_parser = nltk.RegexpParser(grammar)

# parse reviews and store results in review object
def parse_review(r, parser):
    try:
        print(r['title'])
        r['sentences'] = nltk.sent_tokenize(r['text'])
        r['tokens'] = nltk.word_tokenize(r['text'])
        r['pos_tags'] = nltk.pos_tag(r['tokens'])
        text_wrapper = nltk.Text(r['tokens'])
        text_wrapper.collocations(50) # prints collocations
        r['collocations'] = text_wrapper._collocations
        r['noun_chunks'] = [
            str(c) for c in parser.parse(r['pos_tags'])
            if type(c)==nltk.tree.Tree
        ]
        print(len(r['noun_chunks']))
        print('')
    except Exception as error:
        print(error)
        print('')

# could use a subset of reviews:
westerns = [r for r in reviews if r['genres'] and 'Western' in r['genres']]
for r in westerns:
    parse_review(r, chunk_parser)

all_collos = []
for r in westerns:
    all_collos.extend(r['collocations'])

Counter(all_collos).most_common(50)

# westerns related to John Wayne
for r in westerns:
    if ('John', 'Wayne') in r['collocations']:
        print(r['title'])

# westerns with bad guys
for r in westerns:
    if ('bad', 'guys') in r['collocations']:
        print(r['title'])


"""
# can generate tags by looking at common vocab not in stopwords list!
from nltk.corpus import stopwords
stopwords.words('english')

for tok in mr_tokens:
     ...:     if tok.lower() not in stopwords.words('english') and tok.isalpha():
     ...:         print(tok)
"""

# let's join the Ebert corpus into a single block of text
reviews.sort(key=lambda x:x['date_published'])
review_texts = [r['text'] for r in reviews]
all_text = '\n\n\n\n'.join(review_texts)

# demonstrate stemming on "fall"?
all_text.count('fell in love') # the limitation of stemming! fell !> fall
all_text.count('falling in love')
all_text.count('fall in love')
all_text.count('falls in love')
# all_text.count('fall out of love')

# we need to tokenize to go deeper
all_tokens = nltk.word_tokenize(all_text) # this will take a moment

# let's find all _falling in love_ phrases with a stemmer
stemmer = PorterStemmer()
romances = []
trigrams = nltk.ngrams(all_tokens, n=3)
for tri in trigrams:
    if ' '.join([stemmer.stem(tri[0]),tri[1],tri[2]]) == 'fall in love':
        print(tri)
        romances.append(tri)

len(romances) # 862

# token frequencies: tf-idf
# formula may differ--could log some of these values
# also n+1 for some of these values?
all_tokens_count = len(all_tokens)
all_counts = Counter(all_tokens)
all_freqs = {tok:all_counts[tok]/all_tokens_count for tok in all_tokens}

mr = titles['Minority Report (2002)']
mr_tokens = nltk.word_tokenize(mr['text'])
mr_token_count = len(mr_tokens)
mr_counts = Counter(mr_tokens)
mr_counts.most_common(50)
mr_freqs = {tok:mr_counts[tok]/mr_token_count for tok in mr_tokens}

tf_idf_scores = [(tok, mr_freqs[tok]/all_freqs[tok]) for tok in set(mr_tokens)]
tf_idf_scores.sort(key=lambda s:s[1], reverse=True)
tf_idf_scores # most to least uniquely characteristic tokens of Minority Report
# consider how to extend this to other reviews across the corpus

# now let's use the nltk.Text wrapper to explore the whole corpus more
all_wrapper = nltk.Text(all_tokens)
all_fdist = nltk.FreqDist(all_wrapper) # unique tokens with their frequencies
all_fdist.most_common(50)
'aphrodisiac' in all_fdist # True
all_fdist['aphrodisiac'] # 12

# actors
# Freeman, Poitier, Gooding, Glover, Snipes
# consider comparison of female actors / actresses
all_wrapper.dispersion_plot(
    ['Eastwood','Brando','Niro','Schwarzenegger','Hanks','Depp',
    'Pitt','Spacey','DiCaprio','Clooney','Osment','Gosling'])

all_wrapper.concordance('laugh', lines=50)
all_wrapper.concordance('cry', lines=50)
all_wrapper.concordance('fight', lines=50)

# takes a moment to do the first one
all_wrapper.similar('scene') # noun
all_wrapper.similar('actor') # noun
all_wrapper.similar('woman') # noun
all_wrapper.similar('pleasant') # adjective
all_wrapper.similar('hideous') # adjective
all_wrapper.similar('entertaining') # adjective
all_wrapper.similar('foreign') # adjective
all_wrapper.similar('intimately') # adverb
all_wrapper.similar('slay') # verb
all_wrapper.similar('pray') # verb

all_wrapper.common_contexts(['good','bad'])
all_wrapper.common_contexts(['good','evil'])
all_wrapper.common_contexts(['man','woman'])
all_wrapper.common_contexts(['boy','girl'])
all_wrapper.common_contexts(['little','small'])
all_wrapper.common_contexts(['big','huge'])
all_wrapper.common_contexts(['short','long'])
all_wrapper.common_contexts(['true','false'])
all_wrapper.common_contexts(['very','extremely'])
all_wrapper.common_contexts(['emotion','feeling'])

# Visualizing our data
import matplotlib.pyplot as pyplot

# date_published (histogram)
pub_dates = [int(r['date_published'].split('-')[0]) for r in reviews] # year
pub_date_range = max(pub_dates)+1 - min(pub_dates)
pyplot.hist(pub_dates, bins=pub_date_range)
pyplot.show() # early outlier in 1960
reviews[0] # mistake--Le Petit Soldat (1960) was clearly not reviewed in 1960

# release_year (histogram)
release_dates = [r['release_year'] for r in reviews]
release_date_range = max(release_dates)+1 - min(release_dates)
pyplot.hist(release_dates, bins=pub_date_range)
pyplot.show()

# character count of text (histogram)
char_counts = [len(r['text']) for r in reviews]
char_counts_range = max(char_counts)+1 - min(char_counts)
pyplot.hist(char_counts, bins=int(char_counts_range/10))
pyplot.show()

# word count of text (histogram())
review_tokens = [nltk.word_tokenize(r['text']) for r in reviews]
review_words = [[tok for tok in tokens if tok.isalpha()] for tokens in review_tokens]
word_counts = [len(words) for words in review_words]
word_count_range = max(word_counts)+1 - min(word_counts)
pyplot.hist(word_counts, bins=int(word_count_range/10))
pyplot.show() # bimodal distribution--indicates varying formats
# did Ebert work under 1000-word and 1500-word limits?

# genre (pie chart)
genre_instances = [inst for r in reviews if r['genres'] for inst in r['genres']]
#from collections import Counter
genre_counts = Counter(genre_instances)
genre_counts
#genres, counts = zip(*sorted(genre_counts.items()))
genres, counts = zip(*sorted([gc for gc in genre_counts.items() if gc[1]>50], key=lambda gc:gc[1]))
pyplot.pie(counts, labels=genres)
pyplot.show()

# running_time (histogram)
running_times = [r['running_time']/60 for r in reviews if r['running_time']]
running_times_range = max(running_times)+1 - min(running_times)
pyplot.hist(running_times, bins=int(running_times_range*20))
pyplot.show() # mass is between 1 and 2.5 hours with long tail to the right

# mpaa_rating (pie chart)
# from collections import Counter
mpaa_ratings = [r['mpaa_rating'] for r in reviews if r['mpaa_rating']]
rating_counts = Counter(mpaa_ratings)
rating_counts
ratings, counts = zip(*sorted([r for r in rating_counts.items() if r[1]>10], key=lambda r:r[1]))
pyplot.pie(counts, labels=ratings)
pyplot.show() # vast minority R

# star_rating (hist)
star_ratings = [r['star_rating'] for r in reviews]
Counter(star_ratings)
#star_range = max(star_ratings)+1 - min(star_ratings)
pyplot.hist(star_ratings, bins=8)
pyplot.show() # displays funny--how to fix?
# note the dip in 2.5 star ratings--a sign of irrationality?


# NEXT: let's brainstorm some of operations over the whole corpus!


# means and medians:
# stars on mpaa_rating
# stars on genre

# regression:
# http://stackoverflow.com/questions/3949226/calculating-pearson-correlation-and-significance-in-python
# stars on release year post 1967
# stars on review year
# stars on review length
# stars on running_time

# OPTIONAL: DOCUMENT CLASSIFICATION
# http://www.nltk.org/book/ch06.html#document-classification
# train on mpaa ratng and star rating
