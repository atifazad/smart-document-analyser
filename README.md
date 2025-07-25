# Smart Document Assistant

## Setup Instructions

1. **Create and activate the virtual environment using [uv](https://github.com/astral-sh/uv):**
   ```sh
   uv venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```sh
   uv pip install -r requirements.txt  # or use pyproject.toml if using poetry/uv
   ```

3. **Environment Variables:**
   - Copy `.env.example` to `.env` and fill in your configuration and secrets.
   - **Never commit your `.env` file to version control.**

4. **Security:**
   - Follow secure coding practices: validate all inputs, keep dependencies up-to-date, and never expose secrets.

---

For more details, see `CURSOR.local.md`. 