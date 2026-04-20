pip install -r requirement.txt
python -m venv agentic_clean
.\agentic_clean\Scripts\Activate.ps1
uvicorn app.main:app --reload

deactivate
Remove-Item -Recurse -Force .\agentic_clean
