# scripts\run_example.ps1
# Start the server in a separate terminal:
# cd app; uvicorn main:app --reload --port 8000
$code = Get-Content ../samples/bad.py -Raw
$body = @{
  initial_state = @{
    code = $code
    threshold = 80
  }
  wait_for_completion = $true
} | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri "http://127.0.0.1:8000/graph/run" -Method Post -Body $body -ContentType "application/json" | Format-List
