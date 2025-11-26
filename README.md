# recipekg-recommender 🍊🧑‍🍳

## Quickstart

```bash
# 1) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment (optional)
cp .env.example .env
# Edit .env to change the Recipe endpoint or secret key

# 4) Run the dev server
make dev
# or if you're not using make
flask --app backend.main run --debug

# Open http://127.0.0.1:5000/
```

## Endpoints

- `/` — renders a Jinja2 template
- `/health` — returns `{ "status": "ok" }`

## Configuration

- `SPARQL_ENDPOINT` — defaults to `http://localhost:3030/recipes/sparql`
- `SECRET_KEY` — defaults to a development key; set your own in `.env`
