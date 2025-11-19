# Setup Instructions

## Quick Setup

1. **Clone this repository**:
   ```bash
   git clone <your-repo-url>
   cd get
   ```

2. **Initialize the Glider submodule** (required):
   ```bash
   git submodule update --init --recursive
   ```
   
   This pulls the maintained fork at [doing-work/glider_tasklet_crawler](https://github.com/doing-work/glider_tasklet_crawler) into the `glider/` directory so the crawler can import it.

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_lg
   ```

4. **Run setup script**:
   ```bash
   python setup_glider.py
   ```

5. **You're ready!** Run the crawler:
   ```bash
   python financial_crawler.py merck.com "Merck"
   ```

## Why is Glider a submodule?

Glider is a large dependency with its own release cadence. Keeping it as a git submodule means:
- The repository always references a known-good commit of the fork at `doing-work/glider_tasklet_crawler`
- Users can update to newer Glider versions by running `git submodule update --remote`
- The crawler code and Glider framework remain decoupled but versioned together

## Troubleshooting

### "glider directory not found"

Make sure you've initialized the submodule:
```bash
git submodule update --init --recursive
```

### "Cannot import from glider"

1. Verify the glider directory exists
2. Check that `glider/src/` contains the Python modules
3. Run `python setup_glider.py` to verify the setup

### Git warning about embedded repository

If you see a warning about embedded git repository when adding files:
- The `glider/` directory is already in `.gitignore`
- It's normal - Glider should be cloned separately
- The warning won't affect functionality

