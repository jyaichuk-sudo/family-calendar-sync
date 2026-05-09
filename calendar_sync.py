name: Hourly Calendar Sync

on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Crucial: gives the worker permission to write to your repo
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install requests icalendar

      - name: Run sync script
        run: python calendar_sync.py

      - name: Commit and push changes
        run: |
          git config --global user.name "GitHub Action"
          git config --global user.email "action@github.com"
          # This forces the file to be added even if git is being finicky
          git add -f family_master.ics 
          # The '|| echo' prevents the action from failing if there are no changes
          git commit -m "Automated Calendar Update" || echo "No changes to commit"
          git push origin main
