
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1"

def debug_job():
    print("Triggering generation job...")
    response = requests.post(f"{BASE_URL}/generate", json={"topic": "debug coffee test"})
    if response.status_code != 202:
        print(f"Failed to trigger job: {response.text}")
        return

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Job started: {job_id}")

    while True:
        status_res = requests.get(f"{BASE_URL}/status/{job_id}")
        status_data = status_res.json()
        status = status_data["status"]
        print(f"Job Status: {status}")
        
        if status in ["completed", "failed"]:
            print(f"Final Result: {json.dumps(status_data, indent=2)}")
            break
        
        time.sleep(5)
    
    print("\nChecking articles list...")
    articles_res = requests.get(f"{BASE_URL}/articles")
    print(json.dumps(articles_res.json(), indent=2))

if __name__ == "__main__":
    debug_job()
