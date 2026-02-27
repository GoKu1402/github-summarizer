# Quick Setup Guide

Follow these steps to get the GitHub Repository Summarizer running in 5 minutes:

## Step 1: Extract the Project

```bash
unzip github-summarizer.zip
cd github-summarizer
```

## Step 2: Set Up Your API Key

### Option A: Using .env file (Recommended)

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file:**
   ```bash
   # On macOS/Linux:
   nano .env
   # or
   vim .env
   
   # On Windows:
   notepad .env
   ```

3. **Add your actual API key:**
   ```bash
   # Replace 'your-nebius-api-key-here' with your actual key
   NEBIUS_API_KEY=sk_your_actual_key_here_12345
   ```

4. **Save and close the file**
   - In nano: Press `Ctrl+X`, then `Y`, then `Enter`
   - In vim: Press `Esc`, type `:wq`, press `Enter`

### Option B: Using Environment Variables

```bash
# On macOS/Linux:
export NEBIUS_API_KEY="your-actual-key-here"

# On Windows (Command Prompt):
set NEBIUS_API_KEY=your-actual-key-here

# On Windows (PowerShell):
$env:NEBIUS_API_KEY="your-actual-key-here"
```

## Step 3: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Step 4: Start the Server

### Easy Way (Using the Script)
```bash
./start.sh
```

### Manual Way
```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Test It

In a new terminal:

```bash
curl -X POST http://localhost:8000/summarize \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/psf/requests"}'
```

Or run the test suite:
```bash
python test_api.py
```

## Getting Your Nebius API Key

1. Go to https://studio.nebius.ai/
2. Sign up for a free account
3. Add billing details (required but you get $1 free, no charge)
4. Navigate to API Keys section
5. Create a new API key
6. Copy it to your `.env` file

## Troubleshooting

### "Module not found"
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### "API key not configured"
```bash
# Check your .env file exists and has the key
cat .env

# Or verify environment variable
echo $NEBIUS_API_KEY
```

### "Connection refused"
- Make sure the server is running
- Check it's on port 8000
- Try: `curl http://localhost:8000/health`

## Need Help?

Check the main [README.md](README.md) for detailed documentation.
