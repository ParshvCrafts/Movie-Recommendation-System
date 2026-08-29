# Movie Recommendation System

A content-based movie recommender served as a Flask web application: pick a film, get five similar
titles back with poster art.

---

## How it works

Each movie is reduced to a single "tags" document built from its overview, genres, keywords, cast and
crew. Those documents are vectorised, and similarity between any two films becomes the cosine
distance between their vectors. Recommending is then just: find the row for the selected film, sort
its similarity vector, return the top five.

```
movie  ->  tags document  ->  count vector  ->  cosine similarity matrix  ->  top-5 neighbours
```

This is a deliberate design choice rather than a limitation. A content-based model has no cold-start
problem — a brand new film with no ratings is still recommendable the moment its metadata exists —
whereas collaborative filtering cannot say anything about a film nobody has rated yet.

---

## Stack

`Python` · `Pandas` · `NumPy` · `scikit-learn` · `NLTK` · `Flask`

---

## Repository layout

```
movie_recommendation.ipynb   Data cleaning, feature construction and similarity matrix build
app.py / application.py      Flask application
download_models.py           Fetches the serialised artifacts (kept out of git for size)
movies.csv / movies.pkl      Movie metadata and its processed form
templates/ , static/         Web interface
Procfile                     Process definition for platform deployment
```

---

## Running it locally

```bash
git clone https://github.com/ParshvCrafts/Movie-Recommendation-System.git
cd Movie-Recommendation-System

python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

python download_models.py    # fetch the similarity artifacts
python app.py
```

Open `http://127.0.0.1:5000`, choose a title, and the five nearest neighbours are returned.

The similarity matrix is large enough that it is generated or downloaded rather than committed —
storing a dense N×N float matrix in git is a good way to make a repository unusable.

---

## Known limitations

- **Content-based only.** Recommendations reflect metadata similarity, not what audiences actually
  enjoy together. Two films can be near-identical on paper and land very differently.
- **No personalisation.** The system has no user model, so every user asking about the same film
  receives the same five titles.
- **Metadata-bound.** Quality depends entirely on how well the source dataset describes each film;
  sparse entries produce weak neighbours.

---

## License

MIT
