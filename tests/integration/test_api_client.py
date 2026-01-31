"""
Simple API Client Example
Test the Recruiter Pro AI API
"""
import requests
from pathlib import Path

# API endpoint
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_jobs(limit=5):
    """Get available jobs"""
    print("=" * 60)
    print(f"Testing /jobs endpoint (limit={limit})...")
    response = requests.get(f"{BASE_URL}/jobs", params={"limit": limit})
    data = response.json()
    print(f"Total jobs: {data['total']}")
    print(f"\nShowing {data['count']} jobs:")
    for job in data['jobs']:
        print(f"  - {job['title']} ({job['company']})")
        print(f"    Skills: {', '.join(job['required_skills'][:3])}")
    print()

def test_upload(cv_path):
    """Upload and parse CV"""
    print("=" * 60)
    print(f"Testing /upload endpoint...")
    print(f"Uploading: {cv_path}")
    
    with open(cv_path, 'rb') as f:
        files = {'file': (Path(cv_path).name, f)}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Upload successful!")
        print(f"Extracted data:")
        print(f"  Name: {data['extracted_data']['name']}")
        print(f"  Email: {data['extracted_data']['email']}")
        print(f"  Skills: {', '.join(data['extracted_data']['skills'][:5])}")
        print(f"  Experience: {data['extracted_data']['experience_years']} years")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
    print()

def test_match(cv_path, top_k=5):
    """Match CV to jobs"""
    print("=" * 60)
    print(f"Testing /match endpoint (top_k={top_k})...")
    print(f"Matching: {cv_path}")
    
    with open(cv_path, 'rb') as f:
        files = {'file': (Path(cv_path).name, f)}
        params = {'top_k': top_k, 'explain': False}
        response = requests.post(f"{BASE_URL}/match", files=files, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Matching complete!")
        print(f"Analyzed {data['total_jobs_analyzed']} jobs")
        print(f"\nTop {len(data['matches'])} matches:")
        
        for i, match in enumerate(data['matches'], 1):
            print(f"\n  {i}. {match['job_title']} - {match['company']}")
            print(f"     Score: {match['score']}% | Decision: {match['decision']}")
            print(f"     Confidence: {match['confidence']}%")
            print(f"     Skills matched: {', '.join(match['matched_skills'][:3])}")
            if match['missing_skills']:
                print(f"     Missing: {', '.join(match['missing_skills'][:2])}")
    else:
        print(f"❌ Matching failed: {response.status_code}")
        print(response.text)
    print()

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("RECRUITER PRO AI - API CLIENT TEST")
    print("=" * 60)
    
    # Test health
    test_health()
    
    # Test jobs
    test_jobs(limit=5)
    
    # Test upload (if you have a test CV)
    # Note: Add your own test CV file here
    test_cv = "path/to/your/cv.pdf"  # Change to your CV path
    if Path(test_cv).exists():
        test_upload(test_cv)
        test_match(test_cv, top_k=5)
    else:
        print(f"⚠️  No test CV provided")
        print("To test CV upload/matching, update test_cv path to an actual CV file")
        print("Example: test_cv = 'resume.pdf'")
    
    print("=" * 60)
    print("✅ API Client Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
