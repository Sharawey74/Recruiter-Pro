"""
Enhance jobs_cleaned.json with comprehensive, professional technical skills
"""
import json
from pathlib import Path

# Define comprehensive skill mappings for different job roles
SKILL_ENHANCEMENTS = {
    "PHP Developer": {
        "required": [
            "PHP", "MySQL", "Laravel", "CodeIgniter", "MVC Framework",
            "RESTful API", "AJAX", "jQuery", "JavaScript", "HTML5",
            "CSS3", "Bootstrap", "Git", "Composer", "SQL", "JSON", "XML"
        ],
        "preferred": [
            "Symfony", "Yii", "Zend Framework", "WordPress", "Drupal",
            "Joomla", "Redis", "MongoDB", "Docker", "Linux", "Apache",
            "Nginx", "PHPUnit", "OOP", "Design Patterns", "Microservices"
        ]
    },
    "React Native Developer": {
        "required": [
            "React Native", "JavaScript", "TypeScript", "React", "Redux",
            "React Hooks", "REST API", "JSON", "Git", "npm", "Yarn",
            "Mobile UI/UX", "iOS Development", "Android Development",
            "Expo", "React Navigation", "AsyncStorage"
        ],
        "preferred": [
            "GraphQL", "Apollo Client", "MobX", "Firebase", "Push Notifications",
            "Geolocation", "Camera Integration", "WebSockets", "Jest",
            "Detox", "Fastlane", "App Store", "Google Play", "CI/CD"
        ]
    },
    "Software Testing": {
        "required": [
            "Manual Testing", "Test Case Design", "Test Execution",
            "Bug Reporting", "JIRA", "Test Planning", "Regression Testing",
            "Smoke Testing", "Sanity Testing", "UAT", "SDLC", "STLC",
            "Defect Life Cycle", "Agile", "Scrum"
        ],
        "preferred": [
            "Selenium", "Automation Testing", "API Testing", "Postman",
            "Performance Testing", "Load Testing", "JMeter", "TestNG",
            "Cucumber", "BDD", "TDD", "SQL", "Python", "Java", "CI/CD"
        ]
    },
    "QA Engineer": {
        "required": [
            "Manual Testing", "Automation Testing", "Selenium", "Test Planning",
            "Test Cases", "Bug Tracking", "JIRA", "Regression Testing",
            "Smoke Testing", "Integration Testing", "API Testing", "Postman"
        ],
        "preferred": [
            "Java", "Python", "JavaScript", "TestNG", "JUnit", "Cucumber",
            "BDD", "CI/CD", "Jenkins", "Git", "Appium", "Mobile Testing",
            "Performance Testing", "Load Testing", "Security Testing"
        ]
    },
    "Full Stack Developer": {
        "required": [
            "JavaScript", "Node.js", "React", "Express.js", "MongoDB",
            "REST API", "HTML5", "CSS3", "Git", "npm", "Responsive Design",
            "Bootstrap", "Tailwind CSS", "SQL", "NoSQL"
        ],
        "preferred": [
            "TypeScript", "Next.js", "Vue.js", "Angular", "PostgreSQL",
            "Redis", "Docker", "Kubernetes", "AWS", "Azure", "GraphQL",
            "Microservices", "WebSockets", "Jest", "CI/CD"
        ]
    },
    "Backend Developer": {
        "required": [
            "Node.js", "Express.js", "REST API", "MongoDB", "MySQL",
            "PostgreSQL", "Git", "npm", "Authentication", "Authorization",
            "JWT", "Database Design", "SQL"
        ],
        "preferred": [
            "TypeScript", "GraphQL", "Redis", "Microservices", "Docker",
            "Kubernetes", "AWS", "Azure", "GCP", "Message Queues",
            "RabbitMQ", "Kafka", "ElasticSearch", "CI/CD", "Testing"
        ]
    },
    "Frontend Developer": {
        "required": [
            "JavaScript", "React", "HTML5", "CSS3", "Responsive Design",
            "Bootstrap", "Tailwind CSS", "Git", "npm", "Webpack",
            "REST API Integration", "State Management"
        ],
        "preferred": [
            "TypeScript", "Next.js", "Vue.js", "Angular", "Redux",
            "MobX", "GraphQL", "SASS", "LESS", "Figma", "Adobe XD",
            "Jest", "React Testing Library", "Accessibility", "SEO"
        ]
    },
    "Java Developer": {
        "required": [
            "Java", "Spring Boot", "Spring Framework", "Hibernate", "JPA",
            "REST API", "MySQL", "PostgreSQL", "Maven", "Gradle", "Git",
            "OOP", "Design Patterns", "JDBC"
        ],
        "preferred": [
            "Microservices", "Spring Cloud", "Docker", "Kubernetes",
            "Apache Kafka", "Redis", "MongoDB", "JUnit", "Mockito",
            "AWS", "Azure", "CI/CD", "Jenkins", "SonarQube"
        ]
    },
    "Python Developer": {
        "required": [
            "Python", "Django", "Flask", "FastAPI", "REST API", "PostgreSQL",
            "MySQL", "Git", "pip", "Virtual Environments", "OOP",
            "Data Structures", "Algorithms"
        ],
        "preferred": [
            "Celery", "Redis", "MongoDB", "Docker", "Kubernetes", "AWS",
            "Azure", "pandas", "NumPy", "SQLAlchemy", "pytest", "unittest",
            "GraphQL", "Microservices", "CI/CD"
        ]
    },
    ".NET Developer": {
        "required": [
            ".NET Core", "C#", "ASP.NET", "Entity Framework", "SQL Server",
            "REST API", "MVC", "LINQ", "Git", "NuGet", "OOP",
            "Design Patterns"
        ],
        "preferred": [
            "Azure", "Microservices", "Docker", "Kubernetes", "Angular",
            "React", "Blazor", "SignalR", "xUnit", "MSTest", "CI/CD",
            "Azure DevOps", "Redis", "MongoDB"
        ]
    },
    "DevOps Engineer": {
        "required": [
            "Linux", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Git",
            "Shell Scripting", "Python", "Terraform", "Ansible", "AWS",
            "Monitoring", "Logging"
        ],
        "preferred": [
            "Azure", "GCP", "GitLab CI", "GitHub Actions", "Prometheus",
            "Grafana", "ELK Stack", "CloudFormation", "Helm", "ArgoCD",
            "Service Mesh", "Istio", "Security", "Networking"
        ]
    },
    "Data Analyst": {
        "required": [
            "SQL", "Excel", "Data Visualization", "Python", "pandas",
            "Data Cleaning", "Statistical Analysis", "Reporting",
            "Dashboard Creation", "Business Intelligence"
        ],
        "preferred": [
            "Power BI", "Tableau", "Looker", "R", "NumPy", "Matplotlib",
            "Seaborn", "Jupyter", "Google Analytics", "A/B Testing",
            "Machine Learning", "ETL", "Big Data", "Spark"
        ]
    },
    "Data Scientist": {
        "required": [
            "Python", "Machine Learning", "Statistics", "pandas", "NumPy",
            "scikit-learn", "SQL", "Data Visualization", "Feature Engineering",
            "Model Evaluation"
        ],
        "preferred": [
            "TensorFlow", "PyTorch", "Keras", "Deep Learning", "NLP",
            "Computer Vision", "Big Data", "Spark", "Hadoop", "AWS",
            "Azure", "MLOps", "Docker", "A/B Testing", "Tableau"
        ]
    },
    "UI/UX Designer": {
        "required": [
            "Figma", "Adobe XD", "Sketch", "UI Design", "UX Design",
            "Wireframing", "Prototyping", "User Research", "Usability Testing",
            "Design Systems", "Typography", "Color Theory"
        ],
        "preferred": [
            "Adobe Photoshop", "Adobe Illustrator", "InVision", "Zeplin",
            "HTML", "CSS", "JavaScript", "React", "Animation", "Microinteractions",
            "Accessibility", "Responsive Design", "A/B Testing"
        ]
    },
    "Mobile Developer": {
        "required": [
            "Mobile Development", "iOS", "Android", "Swift", "Kotlin",
            "Java", "REST API", "JSON", "Git", "App Store", "Google Play",
            "Mobile UI/UX"
        ],
        "preferred": [
            "React Native", "Flutter", "Xamarin", "Firebase", "SQLite",
            "Realm", "Push Notifications", "In-App Purchases", "Analytics",
            "Crashlytics", "CI/CD", "Fastlane", "Unit Testing"
        ]
    }
}


def enhance_job_skills(job):
    """Enhance a job's skills based on its title"""
    title = job.get("title", "")
    
    # Find matching skill enhancement
    for role_pattern, skills in SKILL_ENHANCEMENTS.items():
        if role_pattern.lower() in title.lower():
            # Replace with enhanced skills
            job["required_skills"] = skills["required"]
            job["preferred_skills"] = skills["preferred"]
            
            # Update description to match skills
            job["description"] = (
                f"We are seeking a {job.get('seniority_level', 'mid')}-level {title} "
                f"with {job.get('min_experience_years', 1)}+ years of experience. "
                f"The ideal candidate should have strong expertise in {', '.join(skills['required'][:5])}. "
                "This role involves working on challenging projects, collaborating with "
                "cross-functional teams, and contributing to innovative solutions. "
                "Strong problem-solving skills and excellent communication abilities are essential."
            )
            return True
    
    return False


def main():
    """Main function to enhance jobs"""
    jobs_path = Path("data/json/jobs_cleaned.json")
    
    if not jobs_path.exists():
        print(f"Error: {jobs_path} not found")
        return
    
    print("Loading jobs...")
    with open(jobs_path, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"Loaded {len(jobs)} jobs")
    
    # Enhance jobs
    enhanced_count = 0
    for job in jobs:
        if enhance_job_skills(job):
            enhanced_count += 1
    
    print(f"Enhanced {enhanced_count} jobs")
    
    # Save back
    print("Saving enhanced jobs...")
    with open(jobs_path, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print("✓ Jobs enhanced successfully!")
    print("\nSummary:")
    print(f"  Total jobs: {len(jobs)}")
    print(f"  Enhanced: {enhanced_count}")
    print(f"  Unchanged: {len(jobs) - enhanced_count}")


if __name__ == "__main__":
    main()
