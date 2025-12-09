"""
Script to prepare training data from CSV and create JSON files for jobs and sample resumes.
"""
import pandas as pd
import json
import random
from pathlib import Path

def prepare_jobs_json():
    """
    Load training dataset and create jobs.json file.
    """
    # Load the training dataset
    data_path = Path("data/raw/final_training_dataset_v2.csv")
    
    if not data_path.exists():
        print(f"Error: Dataset not found at {data_path}")
        return []
    
    print(f"Loading dataset from {data_path}...")
    df = pd.read_csv(data_path)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # The CSV has these columns:
    # profile_id, profile_text, target_job_id, job_title, job_skills, 
    # job_experience, match_score, match_label, role_category, data_source
    
    # Get unique jobs by target_job_id
    job_columns = ['target_job_id', 'job_title', 'job_skills', 'job_experience', 'role_category']
    
    # Check which columns exist
    existing_cols = [col for col in job_columns if col in df.columns]
    print(f"Using columns: {existing_cols}")
    
    # Get unique jobs
    jobs_df = df[existing_cols].drop_duplicates(subset=['target_job_id'])
    
    # Fill NaN values with empty strings BEFORE renaming
    jobs_df = jobs_df.fillna('')
    
    # Filter out jobs with empty job titles
    jobs_df = jobs_df[jobs_df['job_title'].str.strip() != '']
    
    # Rename columns to match expected format
    jobs_df = jobs_df.rename(columns={
        'target_job_id': 'Job Id',
        'job_title': 'Job Title',
        'job_skills': 'skills',
        'job_experience': 'Experience',
        'role_category': 'Role Category'
    })
    
    # Add missing columns with defaults
    jobs_df['Location'] = 'Remote'
    jobs_df['Qualifications'] = jobs_df['Job Title'] + ' position requiring ' + jobs_df['skills']
    
    # Convert to list of dictionaries
    jobs = jobs_df.to_dict('records')
    
    # Save to JSON
    output_path = Path("data/json/jobs.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created {output_path} with {len(jobs)} jobs")
    print(f"  (Filtered out jobs with missing titles)")
    
    return jobs



def create_sample_resumes():
    """
    Create sample resume texts for testing.
    """
    sample_resumes = [
        {
            "resume_id": "resume_001",
            "text": """
JOHN DOE
Email: john.doe@email.com | Phone: +1-555-0101
LinkedIn: linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Senior Software Engineer with 8+ years of experience in full-stack development, 
specializing in Python, Java, and cloud technologies. Proven track record of 
leading teams and delivering scalable solutions.

SKILLS
Programming: Python, Java, JavaScript, TypeScript, SQL
Frameworks: Django, Flask, Spring Boot, React, Node.js
Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins, CI/CD
Databases: PostgreSQL, MongoDB, Redis
Tools: Git, JIRA, Agile/Scrum

PROFESSIONAL EXPERIENCE

Senior Software Engineer | Tech Solutions Inc. | 2020 - Present
• Led development of microservices architecture serving 1M+ users
• Managed team of 5 engineers, conducted code reviews
• Implemented CI/CD pipelines reducing deployment time by 60%
• Technologies: Python, Django, AWS, Docker, Kubernetes

Software Engineer | StartupXYZ | 2017 - 2020
• Developed RESTful APIs and web applications
• Collaborated with cross-functional teams
• Technologies: Java, Spring Boot, PostgreSQL

Junior Developer | WebDev Co. | 2015 - 2017
• Built responsive web applications using React and Node.js
• Participated in agile development processes

EDUCATION
Bachelor of Science in Computer Science
Massachusetts Institute of Technology | 2015
GPA: 3.8/4.0

CERTIFICATIONS
• AWS Certified Solutions Architect
• Certified Kubernetes Administrator (CKA)
            """,
            "expected_skills": ["python", "java", "javascript", "aws", "docker", "kubernetes"],
            "expected_experience": 8,
            "expected_seniority": "senior"
        },
        {
            "resume_id": "resume_002",
            "text": """
JANE SMITH
jane.smith@email.com | (555) 123-4567

SUMMARY
Data Scientist with 5 years of experience in machine learning, statistical analysis,
and data visualization. Expert in Python, R, and big data technologies.

TECHNICAL SKILLS
Languages: Python, R, SQL, Java
ML/AI: TensorFlow, PyTorch, Scikit-learn, Keras
Data: Pandas, NumPy, Matplotlib, Seaborn, Tableau
Big Data: Spark, Hadoop, Hive
Cloud: AWS (SageMaker, S3, EC2), GCP

WORK EXPERIENCE

Data Scientist | DataCorp | 2021 - Present (3 years)
• Developed ML models for customer churn prediction (92% accuracy)
• Built recommendation systems using collaborative filtering
• Created dashboards and visualizations for stakeholders
• Tech stack: Python, TensorFlow, AWS, Tableau

Junior Data Analyst | Analytics Inc. | 2019 - 2021 (2 years)
• Performed statistical analysis on large datasets
• Created reports and visualizations
• Tools: Python, SQL, Excel, Power BI

EDUCATION
Master of Science in Data Science | Stanford University | 2019
Bachelor of Science in Statistics | UC Berkeley | 2017

PROJECTS
• Sentiment Analysis Tool: NLP project using BERT for social media analysis
• Sales Forecasting: Time series forecasting using LSTM networks
            """,
            "expected_skills": ["python", "machine learning", "tensorflow", "aws", "sql"],
            "expected_experience": 5,
            "expected_seniority": "mid-level"
        },
        {
            "resume_id": "resume_003",
            "text": """
ALEX JOHNSON
alex.johnson@email.com | 555-9876

OBJECTIVE
Entry-level software developer seeking opportunities to apply programming skills
and learn from experienced professionals.

SKILLS
• Programming Languages: Python, JavaScript, HTML, CSS
• Frameworks: React, Node.js, Express
• Databases: MySQL, MongoDB
• Tools: Git, GitHub, VS Code
• Soft Skills: Problem-solving, teamwork, communication

EDUCATION
Bachelor of Science in Computer Science | State University | 2023
Relevant Coursework: Data Structures, Algorithms, Web Development, Databases

INTERNSHIP EXPERIENCE

Software Development Intern | Tech Startup | Summer 2022 (3 months)
• Developed features for web application using React and Node.js
• Fixed bugs and wrote unit tests
• Participated in daily stand-ups and sprint planning

PROJECTS

E-commerce Website (Personal Project)
• Built full-stack web app using MERN stack
• Implemented user authentication and payment processing
• Deployed on Heroku

Task Management App
• Created React-based todo application
• Used Redux for state management

CERTIFICATIONS
• FreeCodeCamp Responsive Web Design
• Udemy - Complete Web Developer Bootcamp
            """,
            "expected_skills": ["python", "javascript", "react", "node.js", "mongodb"],
            "expected_experience": 0,
            "expected_seniority": "entry-level"
        },
        {
            "resume_id": "resume_004",
            "text": """
MICHAEL CHEN
michael.chen@email.com | +1-555-7890

PROFESSIONAL PROFILE
DevOps Engineer with 6 years of experience in cloud infrastructure, automation,
and continuous integration/deployment. AWS and Kubernetes expert.

CORE COMPETENCIES
Cloud Platforms: AWS (EC2, S3, Lambda, RDS, CloudFormation), Azure, GCP
Containers & Orchestration: Docker, Kubernetes, ECS, Helm
CI/CD: Jenkins, GitLab CI, GitHub Actions, CircleCI
Infrastructure as Code: Terraform, Ansible, CloudFormation
Monitoring: Prometheus, Grafana, ELK Stack, Datadog
Scripting: Python, Bash, PowerShell

PROFESSIONAL EXPERIENCE

Senior DevOps Engineer | CloudTech Solutions | 2020 - Present
• Architected and maintained AWS infrastructure for 50+ microservices
• Implemented GitOps workflows using ArgoCD and Flux
• Reduced infrastructure costs by 40% through optimization
• Led migration from monolith to microservices architecture

DevOps Engineer | Digital Services Inc. | 2018 - 2020
• Built CI/CD pipelines for automated testing and deployment
• Managed Kubernetes clusters serving production traffic
• Implemented monitoring and alerting systems

System Administrator | IT Corp | 2017 - 2018
• Maintained Linux servers and network infrastructure
• Automated routine tasks using Python and Bash scripts

EDUCATION
Bachelor of Engineering in Information Technology | 2017

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional
• Certified Kubernetes Administrator (CKA)
• HashiCorp Certified: Terraform Associate
            """,
            "expected_skills": ["aws", "kubernetes", "docker", "terraform", "python"],
            "expected_experience": 6,
            "expected_seniority": "senior"
        },
        {
            "resume_id": "resume_005",
            "text": """
SARAH WILLIAMS
sarah.williams@email.com | (555) 246-8101

SUMMARY
Full-Stack Developer with 4 years of experience building modern web applications.
Proficient in JavaScript ecosystem and cloud technologies.

TECHNICAL SKILLS
Frontend: React, Vue.js, Angular, TypeScript, HTML5, CSS3, Tailwind
Backend: Node.js, Express, NestJS, Python, Django
Databases: PostgreSQL, MySQL, MongoDB, Redis
Cloud & Tools: AWS, Docker, Git, REST APIs, GraphQL
Testing: Jest, Mocha, Cypress, Selenium

EXPERIENCE

Full-Stack Developer | WebApp Solutions | 2021 - Present (3 years)
• Developed responsive web applications using React and Node.js
• Designed and implemented RESTful APIs
• Integrated third-party services (Stripe, SendGrid, Auth0)
• Optimized application performance and SEO

Junior Web Developer | Digital Agency | 2020 - 2021 (1 year)
• Created landing pages and marketing websites
• Worked with designers to implement UI/UX designs
• Technologies: HTML, CSS, JavaScript, WordPress

EDUCATION
Bachelor of Science in Web Development | Online University | 2020

SIDE PROJECTS
• Open-source contributor to React ecosystem
• Built SaaS application with 500+ active users
• Tech blog with 10K+ monthly readers
            """,
            "expected_skills": ["javascript", "react", "node.js", "python", "aws"],
            "expected_experience": 4,
            "expected_seniority": "mid-level"
        }
    ]
    
    # Save to JSON
    output_path = Path("data/json/resumes_sample.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_resumes, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created {output_path} with {len(sample_resumes)} sample resumes")
    
    return sample_resumes


def main():
    """Main function to prepare all data."""
    print("=" * 60)
    print("Preparing Training Data")
    print("=" * 60)
    
    # Create jobs.json
    print("\n1. Creating jobs.json...")
    jobs = prepare_jobs_json()
    
    # Create sample resumes
    print("\n2. Creating sample resumes...")
    resumes = create_sample_resumes()
    
    print("\n" + "=" * 60)
    print("Data Preparation Complete!")
    print("=" * 60)
    print(f"\nCreated files:")
    print(f"  • data/json/jobs.json ({len(jobs)} jobs)")
    print(f"  • data/json/resumes_sample.json ({len(resumes)} resumes)")
    print(f"\nNext steps:")
    print(f"  1. Run: python src/agents/agent1_parser.py (to test parser)")
    print(f"  2. Run: pytest tests/test_agent1_parser.py (to run tests)")


if __name__ == "__main__":
    main()
