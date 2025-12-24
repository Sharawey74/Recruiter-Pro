"""
Arabic-English Mappings for Job Titles and Skills
Used to match Arabic CVs to English job database
"""

# Arabic to English Job Title Mappings
JOB_TITLE_MAPPING = {
    # Software Engineering
    'مهندس برمجيات': 'Software Engineer',
    'مطور برمجيات': 'Software Developer',
    'مطور ويب': 'Web Developer',
    'مطور تطبيقات': 'Application Developer',
    'مطور فول ستاك': 'Full Stack Developer',
    'مطور واجهات أمامية': 'Frontend Developer',
    'مطور واجهات خلفية': 'Backend Developer',
    'مهندس برمجيات أول': 'Senior Software Engineer',
    'مهندس برمجيات رئيسي': 'Lead Software Engineer',
    
    # Data Science/AI
    'عالم بيانات': 'Data Scientist',
    'مهندس تعلم آلي': 'Machine Learning Engineer',
    'مهندس ذكاء اصطناعي': 'AI Engineer',
    'محلل بيانات': 'Data Analyst',
    'مهندس بيانات': 'Data Engineer',
    'باحث ذكاء اصطناعي': 'AI Researcher',
    
    # Cybersecurity
    'محلل أمن سيبراني': 'Security Analyst',
    'مهندس أمن المعلومات': 'Information Security Engineer',
    'مختبر اختراق': 'Penetration Tester',
    'محلل أمني': 'Security Analyst',
    'مهندس أمن': 'Security Engineer',
    'محلل مركز العمليات الأمنية': 'SOC Analyst',
    
    # Hardware/Embedded
    'مهندس أجهزة': 'Hardware Engineer',
    'مهندس أنظمة مدمجة': 'Embedded Systems Engineer',
    'مهندس دوائر': 'Circuit Design Engineer',
    'مهندس إلكترونيات': 'Electronics Engineer',
    'مهندس FPGA': 'FPGA Engineer',
    
    # Cloud/DevOps
    'مهندس سحابة': 'Cloud Engineer',
    'مهندس DevOps': 'DevOps Engineer',
    'مهندس موثوقية الموقع': 'Site Reliability Engineer',
    'مدير أنظمة': 'System Administrator',
    'مهندس بنية تحتية': 'Infrastructure Engineer',
    
    # Mobile Development
    'مطور أندرويد': 'Android Developer',
    'مطور iOS': 'iOS Developer',
    'مطور تطبيقات موبايل': 'Mobile App Developer',
    'مطور تطبيقات جوال': 'Mobile Developer',
    
    # Project Management
    'مدير مشروع': 'Project Manager',
    'مدير مشاريع تقنية': 'IT Project Manager',
    'مدير برنامج': 'Program Manager',
    'مدير منتج': 'Product Manager',
    'مالك منتج': 'Product Owner',
    'سكرم ماستر': 'Scrum Master',
    
    # QA/Testing
    'مهندس ضمان الجودة': 'QA Engineer',
    'مختبر برمجيات': 'Software Tester',
    'مهندس اختبار': 'Test Engineer',
    'مختبر أتمتة': 'Automation Tester',
    
    # Database
    'مدير قواعد بيانات': 'Database Administrator',
    'مهندس قواعد بيانات': 'Database Engineer',
    'مطور قواعد بيانات': 'Database Developer',
    
    # Network
    'مهندس شبكات': 'Network Engineer',
    'مدير شبكات': 'Network Administrator',
    'مهندس أمن شبكات': 'Network Security Engineer',
    
    # Business/Analytics
    'محلل أعمال': 'Business Analyst',
    'محلل نظم': 'Systems Analyst',
    'مطور ذكاء الأعمال': 'BI Developer',
    'محلل ذكاء الأعمال': 'Business Intelligence Analyst',
    
    # Marketing/Sales
    'مدير تسويق': 'Marketing Manager',
    'مسوق رقمي': 'Digital Marketing Manager',
    'مدير مبيعات': 'Sales Manager',
    'تنفيذي مبيعات': 'Sales Executive',
    'مدير تسويق رقمي': 'Digital Marketing Manager',
    'أخصائي تحسين محركات البحث': 'SEO Specialist',
    
    # Finance/Accounting
    'محاسب': 'Accountant',
    'محلل مالي': 'Financial Analyst',
    'مدير مالي': 'Finance Manager',
    'مراجع حسابات': 'Auditor',
    'محاسب قانوني': 'Chartered Accountant',
    
    # Design
    'مصمم واجهة مستخدم': 'UI Designer',
    'مصمم تجربة مستخدم': 'UX Designer',
    'مصمم UI/UX': 'UI/UX Designer',
    'مصمم جرافيك': 'Graphic Designer',
    'مصمم منتج': 'Product Designer',
    
    # Support
    'مهندس دعم تقني': 'IT Support Engineer',
    'فني دعم': 'Support Technician',
    'أخصائي دعم تقني': 'Technical Support Specialist'
}

def translate_job_title(arabic_title: str) -> str:
    """
    Translate Arabic job title to English
    
    Args:
        arabic_title: Job title in Arabic
        
    Returns:
        English job title or original if not found
    """
    return JOB_TITLE_MAPPING.get(arabic_title.strip(), arabic_title)

def get_all_arabic_titles():
    """Get list of all Arabic job titles"""
    return list(JOB_TITLE_MAPPING.keys())

def get_all_english_titles():
    """Get list of all English job titles"""
    return list(JOB_TITLE_MAPPING.values())
