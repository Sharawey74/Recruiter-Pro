"""
Test script for Agent 1 parser.
"""
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent1_parser import ProfileJobParser

def test_parser():
    """Test the parser with sample data."""
    print("=" * 60)
    print("Testing Agent 1: Profile & Job Parser")
    print("=" * 60)
    
    # Initialize parser
    parser = ProfileJobParser()
    
    # Test profile parsing
    sample_profile = """
    John Doe
    Email: john.doe@example.com
    Phone: +1-555-123-4567
    
    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8 years of experience in full-stack development.
    
    SKILLS
    Python, Java, JavaScript, React, Node.js, SQL, AWS, Docker, Kubernetes
    
    EXPERIENCE
    Senior Software Engineer - Tech Corp (2018-2023)
    - Led development of microservices architecture
    - Managed team of 5 developers
    
    Software Engineer - StartupXYZ (2015-2018)
    - Developed web applications using React and Node.js
    
    EDUCATION
    Bachelor of Science in Computer Science - MIT (2015)
    """
    
    print("\n1. Testing profile parsing...")
    parsed_profile = parser.parse_profile(sample_profile, "test_profile_001")
    print(f"\n✓ Profile parsed successfully!")
    print(f"  - Skills found: {len(parsed_profile['skills'])}")
    print(f"  - Experience: {parsed_profile['experience_years']} years")
    print(f"  - Seniority: {parsed_profile['seniority']}")
    print(f"  - Education: {parsed_profile['education']}")
    print(f"\n  Sample skills: {parsed_profile['skills'][:5]}")
    
    # Test job parsing
    sample_job = {
        'Job Id': '12345',
        'Job Title': 'Senior Python Developer',
        'Experience': '5 - 8 yrs',
        'Qualifications': 'Strong Python skills, experience with Django/Flask, AWS knowledge required',
        'skills': 'python|django|flask|aws|sql|docker',
        'Role Category': 'Software Development',
        'Location': 'San Francisco, CA'
    }
    
    print("\n2. Testing job parsing...")
    parsed_job = parser.parse_job(sample_job)
    print(f"\n✓ Job parsed successfully!")
    print(f"  - Job Title: {parsed_job['job_title']}")
    print(f"  - Experience Range: {parsed_job['experience']['min_years']}-{parsed_job['experience']['max_years']} years")
    print(f"  - Skills: {parsed_job['skills']}")
    print(f"  - Location: {parsed_job['location']}")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
    return parsed_profile, parsed_job


if __name__ == "__main__":
    test_parser()
