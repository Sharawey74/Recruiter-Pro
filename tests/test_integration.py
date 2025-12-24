"""
Integration Test: Agent 3 + Agent 4 + Backend
Tests the full pipeline with the new deterministic agents
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent3_extractor import Agent3Extractor
from src.agents.agent4_matcher import Agent4Matcher
import json

def test_full_pipeline():
    """Test complete extraction -> matching pipeline"""
    
    # Sample resume text
    resume_text = """
    Candidate: Ahmed Mohamed
    Email: ahmed@example.com
    Phone: +20 100 123 4567
    Address: Sheikh Zayed City, Giza
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 5 years experience in full-stack development.
    
    TECHNICAL SKILLS
    - Programming: Python, JavaScript, HTML, CSS
    - Databases: MongoDB, SQL
    - DevOps: Docker, Git
    
    EXPERIENCE
    5 years experience in software development
    
    EDUCATION
    B.S. Computer Science
    """
    
    # Load canonical jobs
    jobs_path = Path(__file__).parent.parent / 'data' / 'json' / 'jobs_canonical.json'
    with open(jobs_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"Loaded {len(jobs)} canonical jobs")
    
    # Step 1: Extract candidate data
    extractor = Agent3Extractor()
    candidate = extractor.extract(resume_text)
    
    print("\n=== EXTRACTED CANDIDATE ===")
    print(f"Name: {candidate['name']}")
    print(f"Email: {candidate['email']}")
    print(f"Phone: {candidate['phone']}")
    print(f"Skills: {', '.join(candidate['skills'])}")
    print(f"Experience: {candidate['experience_years']} years")
    
    # Assertions
    assert candidate['name'] == "Ahmed Mohamed", "Name extraction failed"
    assert "zayed" not in candidate['name'].lower(), "Address leaked into name"
    assert candidate['email'] == "ahmed@example.com", "Email extraction failed"
    assert len(candidate['skills']) > 0, "No skills extracted"
    assert candidate['experience_years'] == 5, "Experience extraction failed"
    
    # Step 2: Match against jobs
    matcher = Agent4Matcher()
    matches = matcher.score_all(candidate, jobs)
    
    print("\n=== MATCH RESULTS ===")
    for i, match in enumerate(matches, 1):
        print(f"\n{i}. {match['title']}")
        print(f"   Score: {match['score']}% ({match['match_label']})")
        print(f"   Matched Skills: {', '.join(match['matched_skills'][:3])}...")
        print(f"   Missing Skills: {', '.join(match['missing_skills'][:3])}...")
    
    # Assertions
    assert len(matches) <= 3, "Should return max 3 matches"
    assert all('score' in m for m in matches), "Missing scores"
    assert all('match_label' in m for m in matches), "Missing labels"
    
    # Check sorting
    scores = [m['score'] for m in matches]
    assert scores == sorted(scores, reverse=True), "Results not sorted by score"
    
    print("\n✓ Integration test passed!")

if __name__ == "__main__":
    test_full_pipeline()
