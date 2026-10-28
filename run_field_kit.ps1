# Field kit server: serves the Outbreak Navigator to every phone/laptop on the kit's local Wi-Fi. No internet needed.
#   powershell -ExecutionPolicy Bypass -File .\run_field_kit.ps1
# First run: allow "Python" through the Windows firewall on PRIVATE networks when asked.
# To start it automatically when the box boots: Task Scheduler -> "At startup" -> run this script.
Set-Location $PSScriptRoot
$env:HF_HUB_OFFLINE = "1"          # never try to reach the internet for the model
& .\.venv\Scripts\python.exe -m streamlit run navigator.py --server.address 0.0.0.0 --server.port 8501
