Running tests
===============

To run the test-suite locally:

1. Create a virtual environment and activate it.

   python3 -m venv .venv
   source .venv/bin/activate

2. Install runtime and dev dependencies:

   pip install -r requirements.txt
   pip install -r requirements-dev.txt

3. Run pytest:

   pytest -q

Notes:
- CI is configured in .github/workflows/ci.yml and will run tests on push and pull requests.
- Many tests mock external services (ComfyUI, Ollama, PixVerse) so they do not require those services to be running locally.
