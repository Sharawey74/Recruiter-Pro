"""
Data Cleaning Script for Jobs.json
Transforms unreliable job data into the minimal realistic structure
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import random


class JobDataCleaner:
    """Cleans and transforms job data to minimal realistic structure"""
    
    # Common unreliable patterns to remove from job titles
    TITLE_NOISE_PATTERNS = [
        r"(?i)urgent(?:ly)?\s*(?:hiring|requirement|required|need)?\s*(?:for|of)?\s*",  # Urgent hiring/requirement
        r"(?i)(?:an\s+)?urgent\s+",  # "An Urgent", "Urgent"
        r"(?i)immediate(?:ly)?\s+(?:hiring|requirement|required|need|openings?)?\s*(?:for|of)?\s*",  # Immediate
        r"(?i)opening(?:s)?\s+for\s+",  # Openings for
        r"(?i)walk-in\s*(?:available|interview)?\s*",  # Walk-in
        r"(?i)interview\s*",  # Interview
        r"@\.Net|@\s*\w+",  # @.Net, @ Location
        r"\s*-\s*\d+\s*\w+",  # - 2 July
        r"(?i)fresher\s*",  # Fresher
        r"(?i)\(\s*only\s+(?:male|female)\s*(?:candidates?)?\s*\)",  # (Only Male/Female Candidates)
        r"(?i)\(\s*only\s+(?:male|female)\s*\)",  # (Only Male/Female)
        r"(?i)only\s+(?:male|female)\s*(?:candidates?)?\s*(?:-|:)?",  # Only Male/Female -
        r"(?i)in\s+(?:java|python|\.net|php)\s+developer",  # In Java Developer (typo)
        r"(?i)mca\s*/\s*b\.tech\s*",  # MCA / B.Tech
        r"\s+_\s+|_(?:mnc|gurgaon|pune|mumbai|bangalore|hyderabad|chennai)",  # underscore patterns
        r"(?i)//\s*\(\s*only\s+(?:male|female)\s*\)",  # // (Only Male/Female)
        r"\.{3,}",  # Multiple dots ....
        r"\|\|",  # Double pipes ||
        r":\s*0\s*\(",  # : 0 (
        r"\(\s*\)\s*",  # Empty parentheses
    ]
    
    # Seniority keywords
    SENIORITY_KEYWORDS = {
        "entry": ["fresher", "junior", "trainee", "intern", "entry", "graduate"],
        "mid": ["mid", "intermediate", "developer", "engineer", "analyst"],
        "senior": ["senior", "sr", "lead", "principal"],
        "lead": ["lead", "team lead", "tech lead", "technical lead"],
        "manager": ["manager", "head", "director"],
        "executive": ["vp", "vice president", "chief", "cto", "cio", "ceo"]
    }
    
    # Common worldwide tech hub cities with their countries (EQUAL DISTRIBUTION, NO ISRAEL)
    GLOBAL_CITIES = [
        # USA (9 cities)
        ("San Francisco", "USA"), ("New York", "USA"), ("Seattle", "USA"), 
        ("Austin", "USA"), ("Boston", "USA"), ("Los Angeles", "USA"),
        ("Chicago", "USA"), ("Denver", "USA"), ("Portland", "USA"),
        # Canada (5 cities)
        ("Toronto", "Canada"), ("Vancouver", "Canada"), ("Montreal", "Canada"),
        ("Calgary", "Canada"), ("Ottawa", "Canada"),
        # Europe (15 cities)
        ("London", "UK"), ("Berlin", "Germany"), ("Amsterdam", "Netherlands"),
        ("Paris", "France"), ("Dublin", "Ireland"), ("Stockholm", "Sweden"),
        ("Munich", "Germany"), ("Barcelona", "Spain"), ("Zurich", "Switzerland"),
        ("Madrid", "Spain"), ("Copenhagen", "Denmark"), ("Oslo", "Norway"),
        ("Vienna", "Austria"), ("Brussels", "Belgium"), ("Milan", "Italy"),
        # Asia (9 cities)
        ("Singapore", "Singapore"), ("Tokyo", "Japan"), ("Seoul", "South Korea"),
        ("Hong Kong", "Hong Kong"), ("Bangalore", "India"), ("Mumbai", "India"),
        ("Shanghai", "China"), ("Beijing", "China"), ("Taipei", "Taiwan"),
        # Australia (5 cities)
        ("Sydney", "Australia"), ("Melbourne", "Australia"), ("Brisbane", "Australia"),
        ("Perth", "Australia"), ("Auckland", "New Zealand"),
        # Africa (5 cities)
        ("Cape Town", "South Africa"), ("Lagos", "Nigeria"), ("Nairobi", "Kenya"),
        ("Cairo", "Egypt"), ("Johannesburg", "South Africa"),
        # Middle East (5 cities - NO ISRAEL)
        ("Dubai", "UAE"), ("Abu Dhabi", "UAE"), ("Riyadh", "Saudi Arabia"),
        ("Doha", "Qatar"), ("Kuwait City", "Kuwait")
    ]
    
    # Tech/Engineering/Marketing related keywords for filtering
    TECH_KEYWORDS = [
        # Computer Science & Software
        "software", "developer", "engineer", "programmer", "coding", "full stack",
        "backend", "frontend", "devops", "cloud", "web", "mobile", "app",
        # AI & Data
        "ai", "artificial intelligence", "machine learning", "ml", "data scientist",
        "data engineer", "data analyst", "nlp", "deep learning", "neural",
        # Cybersecurity
        "security", "cyber", "infosec", "penetration", "ethical hacker", "soc",
        "firewall", "threat", "vulnerability", "incident response",
        # Engineering disciplines
        "engineering", "technical", "systems", "network", "infrastructure",
        "architect", "site reliability", "sre", "platform engineer",
        # Marketing
        "marketing", "digital marketing", "growth", "product marketing", 
        "content", "seo", "sem", "social media", "brand", "campaign"
    ]
    
    # Tech skills that indicate relevant jobs
    TECH_SKILLS = [
        "python", "java", "javascript", "react", "node", "angular", "vue",
        "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "mongodb", "postgresql", "redis", "elasticsearch",
        "machine learning", "tensorflow", "pytorch", "scikit", "pandas",
        "cybersecurity", "penetration testing", "firewall", "encryption",
        "marketing automation", "analytics", "seo", "google analytics"
    ]
    
    # Remote type based on location
    REMOTE_TYPES = ["on-site", "hybrid", "remote"]
    
    # Sample company names for missing data
    SAMPLE_COMPANIES = [
        "Tech Solutions Pvt Ltd", "Digital Innovations", "Smart Systems Inc",
        "Global IT Services", "Enterprise Solutions", "Cloud Technologies",
        "Data Dynamics", "Agile Ventures", "Innovation Labs", "Future Tech"
    ]
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.stats = {
            "total": 0,
            "cleaned": 0,
            "skipped": 0,
            "errors": []
        }
    
    def clean_title(self, title: str) -> str:
        """Clean job title by removing noise patterns"""
        if not title:
            return ""
        
        cleaned = title
        
        # Apply all noise removal patterns
        for pattern in self.TITLE_NOISE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Remove gender specifications at the end (more aggressive)
        cleaned = re.sub(r"(?i)\(\s*(?:male|female)\s*$", "", cleaned)  # (Male at end
        cleaned = re.sub(r"(?i)\s+\(\s*(?:male|female)\s*$", "", cleaned)  # (Male at end with space
        cleaned = re.sub(r"(?i)\s*\(\s*(?:only\s+)?(?:male|female)\s*\)\s*$", "", cleaned)
        
        # Remove "An" or "The" at the beginning
        cleaned = re.sub(r"^(?:An|The)\s+", "", cleaned, flags=re.IGNORECASE)
        
        # Remove trailing incomplete parentheses with job type info
        cleaned = re.sub(r"\(\s*(?:contract|permanent|temporary|part[- ]time|full[- ]time)\s*(?:to\s+hire)?\s*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\(\s*\w+\s+operation\s*$", "", cleaned, flags=re.IGNORECASE)  # (Banking Operation
        cleaned = re.sub(r"\(\s*[^)]*$", "", cleaned)  # Any unclosed parenthesis at end
        
        # Remove extra whitespace and dashes/underscores at start/end
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = re.sub(r"^[-_\s]+|[-_\s]+$", "", cleaned).strip()
        
        # Remove trailing hyphens, pipes, parentheses, dots
        cleaned = re.sub(r"[-|().]+$", "", cleaned).strip()
        
        # Remove location suffixes (city names at end)
        location_suffixes = [
            "gurgaon", "pune", "mumbai", "bangalore", "hyderabad", "chennai",
            "delhi", "kolkata", "ahmedabad", "noida", "ghaziabad"
        ]
        for loc in location_suffixes:
            cleaned = re.sub(rf"(?i)[-_,\s]*{loc}\s*$", "", cleaned).strip()
        
        # Remove MNC suffix
        cleaned = re.sub(r"(?i)[-_,\s]*mnc\s*$", "", cleaned).strip()
        
        # Remove trailing location indicators
        cleaned = re.sub(r"(?i)\s*-\s*(?:for\s+)?\w+\s+location\s*$", "", cleaned).strip()
        
        # Remove "Call Now" and similar
        cleaned = re.sub(r"(?i):\s*call\s+now\s*$", "", cleaned).strip()
        
        # Final cleanup
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        
        # Skip if too short after cleaning
        if len(cleaned) < 5:
            return ""
        
        # Capitalize properly (title case)
        cleaned = cleaned.title()
        
        # Fix common acronyms to uppercase
        acronyms = ["Sql", "Api", "Aws", "Gcp", "Php", "Seo", "Sap", "Crm", "Erp", "Dba", "Qa", "It", "Ui", "Ux", 
                    "Html", "Css", "Xml", "Json", "Rest", "Http", "Ssl", "Tcp", "Ip", "Vpn"]
        for acronym in acronyms:
            cleaned = re.sub(rf"\b{acronym}\b", acronym.upper(), cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def parse_experience_range(self, exp_str: str) -> tuple:
        """Parse experience string into min/max years"""
        if not exp_str:
            return 0, 0
        
        # Extract numbers
        numbers = re.findall(r"\d+", exp_str)
        
        if not numbers:
            return 0, 2  # Default for fresher
        
        if len(numbers) == 1:
            years = int(numbers[0])
            return years, years
        
        return int(numbers[0]), int(numbers[1])
    
    def determine_seniority(self, title: str, min_exp: int) -> str:
        """Determine seniority level from title and experience"""
        title_lower = title.lower()
        
        # Check keywords first
        for level, keywords in self.SENIORITY_KEYWORDS.items():
            if any(kw in title_lower for kw in keywords):
                return level
        
        # Fallback to experience
        if min_exp == 0:
            return "entry"
        elif min_exp <= 2:
            return "mid"
        elif min_exp <= 5:
            return "senior"
        elif min_exp <= 8:
            return "lead"
        else:
            return "manager"
    
    def extract_location(self, location_str: str, title: str) -> tuple:
        """Extract city, country and determine remote type with realistic distribution"""
        if not location_str:
            location_str = ""
        
        location_lower = location_str.lower()
        title_lower = title.lower()
        
        # Assign random global city first
        city, country = random.choice(self.GLOBAL_CITIES)
        
        # Check if remote is mentioned
        if "remote" in location_lower:
            # 50% remote, 30% hybrid, 20% on-site even if marked as remote
            remote_type = random.choices(["remote", "hybrid", "on-site"], weights=[50, 30, 20])[0]
            return city, country, remote_type
        
        # Try to extract specific city from location string
        for check_city, check_country in self.GLOBAL_CITIES:
            if check_city.lower() in location_lower:
                city, country = check_city, check_country
                # Determine remote type based on keywords
                if any(word in location_lower for word in ["hybrid", "flexible"]):
                    return city, country, "hybrid"
                # If city is mentioned, likely on-site or hybrid
                remote_type = random.choices(["on-site", "hybrid", "remote"], weights=[50, 30, 20])[0]
                return city, country, remote_type
        
        # Try to extract city from title
        for check_city, check_country in self.GLOBAL_CITIES:
            if check_city.lower() in title_lower:
                city, country = check_city, check_country
                remote_type = random.choices(["on-site", "hybrid"], weights=[70, 30])[0]
                return city, country, remote_type
        
        # Default: random global city with realistic distribution
        # Tech jobs: 40% on-site, 35% hybrid, 25% remote
        remote_type = random.choices(["on-site", "hybrid", "remote"], weights=[40, 35, 25])[0]
        return city, country, remote_type
    
    def clean_skills(self, skills_str: str) -> tuple:
        """Clean and categorize skills into required and preferred"""
        if not skills_str:
            return [], []
        
        # Split by | or ,
        skills = re.split(r"[|,]", skills_str)
        
        # Clean each skill
        cleaned = []
        for skill in skills:
            skill = skill.strip()
            if skill and len(skill) > 1:
                # Proper case for common skills
                skill = skill.lower()
                # Capitalize known acronyms
                if skill.upper() in ["SQL", "HTML", "CSS", "API", "REST", "JSON", "XML", "AWS", "GCP"]:
                    skill = skill.upper()
                else:
                    skill = skill.capitalize()
                cleaned.append(skill)
        
        # Remove duplicates
        cleaned = list(set(cleaned))
        
        # Split into required (first 60%) and preferred (rest)
        split_point = max(1, int(len(cleaned) * 0.6))
        required = cleaned[:split_point]
        preferred = cleaned[split_point:]
        
        return required, preferred
    
    def generate_description(self, title: str, required_skills: List[str], 
                            min_exp: int, seniority: str) -> str:
        """Generate a realistic job description"""
        exp_text = f"{min_exp}+ years" if min_exp > 0 else "0-2 years"
        skills_text = ", ".join(required_skills[:5]) if required_skills else "relevant technical skills"
        
        description = (
            f"We are seeking a {seniority}-level {title} with {exp_text} of experience. "
            f"The ideal candidate should have strong expertise in {skills_text}. "
            f"This role involves working on challenging projects, collaborating with cross-functional teams, "
            f"and contributing to innovative solutions. Strong problem-solving skills and excellent communication "
            f"abilities are essential."
        )
        
        return description
    
    def determine_employment_type(self, title: str) -> str:
        """Determine employment type from title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ["intern", "internship", "trainee"]):
            return "internship"
        if any(word in title_lower for word in ["contract", "freelance", "consultant"]):
            return "contract"
        if "part time" in title_lower or "part-time" in title_lower:
            return "part-time"
        
        return "full-time"
    
    def generate_posted_date(self, index: int, total: int) -> str:
        """Generate realistic posted dates (spread over last 90 days)"""
        days_ago = int((index / total) * 90)
        posted_date = datetime.now() - timedelta(days=days_ago)
        return posted_date.strftime("%Y-%m-%d")
    
    def is_relevant_job(self, title: str, skills: List[str]) -> bool:
        """Check if job is related to tech/engineering/marketing"""
        title_lower = title.lower()
        skills_lower = [s.lower() for s in skills]
        
        # Check title for tech keywords
        if any(keyword in title_lower for keyword in self.TECH_KEYWORDS):
            return True
        
        # Check skills for tech skills
        for skill in skills_lower:
            if any(tech_skill in skill for tech_skill in self.TECH_SKILLS):
                return True
        
        return False
    
    def clean_job(self, job_dict: Dict[str, Any], index: int, total: int) -> Optional[Dict[str, Any]]:
        """Transform a single job to the new structure"""
        try:
            # Extract original fields
            job_id = job_dict.get("Job Id") or job_dict.get("job_id", f"job_{index}")
            title_raw = job_dict.get("Job Title") or job_dict.get("title", "")
            skills_raw = job_dict.get("skills", "")
            experience_raw = job_dict.get("Experience", "0 - 0 yrs")
            location_raw = job_dict.get("Location", "")
            
            # Skip if no title
            if not title_raw:
                return None
            
            # Clean title
            title = self.clean_title(title_raw)
            if not title or len(title) < 3:
                return None
            
            # Parse experience
            min_exp, max_exp = self.parse_experience_range(experience_raw)
            
            # Determine seniority
            seniority = self.determine_seniority(title, min_exp)
            
            # Extract location
            city, country, remote_type = self.extract_location(location_raw, title_raw)
            
            # Clean skills
            required_skills, preferred_skills = self.clean_skills(skills_raw)
            
            # Skip if no skills
            if not required_skills:
                return None
            
            # Filter: Only keep tech/engineering/marketing jobs
            if not self.is_relevant_job(title, required_skills):
                return None
            
            # Generate description
            description = self.generate_description(title, required_skills, min_exp, seniority)
            
            # Determine employment type
            employment_type = self.determine_employment_type(title)
            
            # Assign company (use original if exists, else random)
            company_name = job_dict.get("company") or random.choice(self.SAMPLE_COMPANIES)
            
            # Generate posted date
            posted_date = self.generate_posted_date(index, total)
            
            # Create cleaned job
            cleaned_job = {
                "job_id": job_id,
                "title": title,
                "company_name": company_name,
                "location_city": city,
                "location_country": country,
                "remote_type": remote_type,
                "employment_type": employment_type,
                "seniority_level": seniority,
                "min_experience_years": min_exp,
                "max_experience_years": max_exp,
                "description": description,
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
                "posted_date": posted_date
            }
            
            return cleaned_job
            
        except Exception as e:
            self.stats["errors"].append(f"Error processing job {job_dict.get('Job Id', 'unknown')}: {str(e)}")
            return None
    
    def clean_all(self):
        """Clean all jobs from input file and save to output file"""
        print(f"🔄 Loading jobs from {self.input_path}...")
        
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load input file: {e}")
            return
        
        self.stats["total"] = len(jobs_data)
        print(f"📊 Found {self.stats['total']} jobs to clean")
        
        cleaned_jobs = []
        
        for idx, job in enumerate(jobs_data):
            if idx % 1000 == 0 and idx > 0:
                print(f"   Processed {idx}/{self.stats['total']}...")
            
            cleaned = self.clean_job(job, idx, self.stats["total"])
            
            if cleaned:
                cleaned_jobs.append(cleaned)
                self.stats["cleaned"] += 1
            else:
                self.stats["skipped"] += 1
        
        # Save cleaned jobs
        print(f"\n💾 Saving {len(cleaned_jobs)} cleaned jobs to {self.output_path}...")
        
        try:
            # Ensure output directory exists
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_jobs, f, indent=2, ensure_ascii=False)
            
            print("✅ Successfully saved cleaned jobs!")
            
        except Exception as e:
            print(f"❌ Failed to save output file: {e}")
            return
        
        # Print statistics
        print("\n" + "=" * 60)
        print("📊 CLEANING STATISTICS")
        print("=" * 60)
        print(f"Total jobs processed: {self.stats['total']}")
        print(f"Successfully cleaned: {self.stats['cleaned']} ({self.stats['cleaned']/self.stats['total']*100:.1f}%)")
        print(f"Skipped (invalid):    {self.stats['skipped']} ({self.stats['skipped']/self.stats['total']*100:.1f}%)")
        
        if self.stats["errors"]:
            print(f"\n⚠️  {len(self.stats['errors'])} errors occurred (showing first 10):")
            for error in self.stats["errors"][:10]:
                print(f"   - {error}")
        
        print("=" * 60)
        
        # Show sample cleaned jobs
        print("\n📋 Sample cleaned jobs (first 3):")
        for i, job in enumerate(cleaned_jobs[:3], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company_name']}")
            print(f"   Location: {job['location_city']} ({job['remote_type']})")
            print(f"   Experience: {job['min_experience_years']}-{job['max_experience_years']} years ({job['seniority_level']})")
            print(f"   Skills: {', '.join(job['required_skills'][:5])}")
            print(f"   Type: {job['employment_type']}")


def main():
    """Main entry point"""
    import sys
    
    # Default paths
    input_path = "data/json/jobs.json"
    output_path = "data/json/jobs_cleaned.json"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    print("🚀 Job Data Cleaning Script")
    print("=" * 60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print("=" * 60 + "\n")
    
    cleaner = JobDataCleaner(input_path, output_path)
    cleaner.clean_all()
    
    print("\n✨ Cleaning complete!")


if __name__ == "__main__":
    main()
