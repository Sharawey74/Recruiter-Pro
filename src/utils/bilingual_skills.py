"""
Bilingual Skills Database - Arabic-English Mappings
Extends the main skills database with Arabic translations
"""

# Bilingual skills mapping: English skill -> [english_variants, arabic_variants]
BILINGUAL_SKILLS = {
    # Programming Languages
    'python': ['python', 'بايثون', 'بيثون'],
    'java': ['java', 'جافا', 'جاڤا'],
    'javascript': ['javascript', 'js', 'جافا سكريبت', 'جافاسكريبت'],
    'c++': ['c++', 'cpp', 'سي بلس بلس', 'سي++'],
    'c#': ['c#', 'csharp', 'سي شارب', 'سي#'],
    'php': ['php', 'بي اتش بي', 'بي إتش بي'],
    'sql': ['sql', 'إس كيو إل', 'لغة الاستعلام'],
    'typescript': ['typescript', 'ts', 'تايب سكريبت'],
    'go': ['go', 'golang', 'جو', 'لغة جو'],
    'rust': ['rust', 'رست'],
    'kotlin': ['kotlin', 'كوتلن'],
    'swift': ['swift', 'سويفت'],
    'ruby': ['ruby', 'روبي'],
    
    # Web Development
    'html': ['html', 'اتش تي ام ال', 'لغة ترميز النص'],
    'css': ['css', 'سي إس إس', 'أنماط متتالية'],
    'react': ['react', 'reactjs', 'ريأكت', 'ريآكت'],
    'angular': ['angular', 'angularjs', 'أنجولار', 'أنغولار'],
    'vue': ['vue', 'vuejs', 'فيو', 'ڤيو'],
    'node.js': ['nodejs', 'node.js', 'node', 'نود جي إس', 'نود'],
    'django': ['django', 'جانجو', 'دجانجو'],
    'flask': ['flask', 'فلاسك'],
    'spring boot': ['spring boot', 'springboot', 'سبرينج بوت'],
    
    # Databases
    'mysql': ['mysql', 'ماي إس كيو إل', 'قاعدة بيانات ماي'],
    'mongodb': ['mongodb', 'mongo', 'مونجو دي بي', 'مونغو'],
    'postgresql': ['postgresql', 'postgres', 'بوستجر', 'بوستغر'],
    'oracle': ['oracle', 'أوراكل', 'اوراكل'],
    'redis': ['redis', 'ريديس'],
    'elasticsearch': ['elasticsearch', 'إلاستك سيرش'],
    
    # Cloud & DevOps
    'aws': ['aws', 'amazon web services', 'أمازون', 'خدمات أمازون'],
    'azure': ['azure', 'microsoft azure', 'أزور', 'مايكروسوفت أزور'],
    'gcp': ['gcp', 'google cloud', 'جوجل كلاود'],
    'docker': ['docker', 'دوكر', 'حاويات'],
    'kubernetes': ['kubernetes', 'k8s', 'كوبرنيتس', 'كوبيرنيتس'],
    'jenkins': ['jenkins', 'جينكينز'],
    'git': ['git', 'github', 'gitlab', 'جيت', 'جيت هاب'],
    'terraform': ['terraform', 'تيرافورم'],
    'ansible': ['ansible', 'أنسيبل'],
    'ci/cd': ['ci/cd', 'cicd', 'تكامل مستمر', 'نشر مستمر'],
    
    # AI/ML
    'machine learning': ['machine learning', 'ml', 'تعلم الآلة', 'تعلم آلي'],
    'deep learning': ['deep learning', 'تعلم عميق', 'التعلم العميق'],
    'tensorflow': ['tensorflow', 'تنسرفلو', 'تنسور فلو'],
    'pytorch': ['pytorch', 'بايتورش', 'باي تورش'],
    'nlp': ['nlp', 'natural language processing', 'معالجة اللغة الطبيعية'],
    'computer vision': ['computer vision', 'cv', 'رؤية الحاسوب', 'رؤية حاسوبية'],
    'data science': ['data science', 'علم البيانات'],
    'ai': ['ai', 'artificial intelligence', 'ذكاء اصطناعي'],
    
    # Hardware/Embedded
    'vhdl': ['vhdl', 'في اتش دي ال'],
    'verilog': ['verilog', 'فيريلوج'],
    'fpga': ['fpga', 'إف بي جي إيه', 'مصفوفة البوابات'],
    'embedded systems': ['embedded', 'embedded systems', 'أنظمة مدمجة', 'نظام مدمج'],
    'rtos': ['rtos', 'real-time os', 'نظام تشغيل فوري', 'نظام حقيقي'],
    'pcb': ['pcb', 'pcb design', 'تصميم دوائر مطبوعة', 'لوحة دوائر'],
    'arm': ['arm', 'arm cortex', 'معالج ارم'],
    'arduino': ['arduino', 'اردوينو', 'أردوينو'],
    
    # Project Management
    'pmp': ['pmp', 'project management professional', 'إدارة المشاريع الاحترافية'],
    'agile': ['agile', 'اجايل', 'رشيق', 'منهجية رشيقة'],
    'scrum': ['scrum', 'سكرم', 'سكروم'],
    'jira': ['jira', 'جيرا'],
    'ms project': ['ms project', 'microsoft project', 'مشروع مايكروسوفت'],
    'project management': ['project management', 'إدارة المشاريع'],
    
    # Cybersecurity
    'cybersecurity': ['cybersecurity', 'security', 'أمن سيبراني', 'أمن المعلومات'],
    'penetration testing': ['penetration testing', 'pen test', 'اختبار الاختراق'],
    'firewall': ['firewall', 'firewalls', 'جدار ناري', 'جدار الحماية'],
    'siem': ['siem', 'إس آي إي إم'],
    'soc': ['soc', 'security operations center', 'مركز العمليات الأمنية'],
    'ids': ['ids', 'intrusion detection', 'كشف التسلل'],
    'ips': ['ips', 'intrusion prevention', 'منع التسلل'],
    
    # Accounting/Finance
    'accounting': ['accounting', 'محاسبة'],
    'tally': ['tally', 'تالي'],
    'taxation': ['taxation', 'tax', 'ضرائب', 'الضرائب'],
    'financial analysis': ['financial analysis', 'تحليل مالي'],
    'budgeting': ['budgeting', 'budget', 'موازنة', 'ميزانية'],
    'excel': ['excel', 'advanced excel', 'اكسل', 'إكسل'],
    
    # Sales/Marketing
    'digital marketing': ['digital marketing', 'تسويق رقمي', 'تسويق إلكتروني'],
    'seo': ['seo', 'search engine optimization', 'تحسين محركات البحث'],
    'sales': ['sales', 'مبيعات'],
    'crm': ['crm', 'customer relationship', 'إدارة علاقات العملاء'],
    'social media marketing': ['social media marketing', 'smm', 'تسويق عبر وسائل التواصل'],
    
    # Soft Skills
    'communication': ['communication', 'تواصل', 'مهارات التواصل'],
    'leadership': ['leadership', 'قيادة', 'مهارات قيادية'],
    'teamwork': ['teamwork', 'team work', 'عمل جماعي', 'فريق العمل'],
    'problem solving': ['problem solving', 'حل المشكلات', 'حل المشاكل'],
    'time management': ['time management', 'إدارة الوقت'],
    'analytical': ['analytical', 'تحليلي', 'مهارات تحليلية'],
    
    # Mobile Development
    'android': ['android', 'أندرويد', 'اندرويد'],
    'ios': ['ios', 'آي أو إس'],
    'react native': ['react native', 'ريأكت نيتف'],
    'flutter': ['flutter', 'فلاتر'],
    
    # Testing
    'selenium': ['selenium', 'سيلينيوم'],
    'testing': ['testing', 'qa', 'quality assurance', 'اختبار', 'ضمان الجودة'],
    'automation testing': ['automation testing', 'اختبار أتمتة'],
    
    # Networking
    'networking': ['networking', 'الشبكات', 'شبكات'],
    'tcp/ip': ['tcp/ip', 'تي سي بي', 'بروتوكول الإنترنت'],
    'vpn': ['vpn', 'في بي إن', 'شبكة خاصة افتراضية'],
    'linux': ['linux', 'لينكس', 'لينوكس'],
    'windows server': ['windows server', 'ويندوز سيرفر'],
    
    # Design
    'ui/ux': ['ui/ux', 'ui', 'ux', 'تصميم واجهة', 'تجربة المستخدم'],
    'photoshop': ['photoshop', 'فوتوشوب'],
    'figma': ['figma', 'فيجما'],
    'graphic design': ['graphic design', 'تصميم جرافيك'],
    
    # Data & Analytics
    'power bi': ['power bi', 'powerbi', 'باور بي آي'],
    'tableau': ['tableau', 'تابلو'],
    'data analysis': ['data analysis', 'تحليل البيانات'],
    'big data': ['big data', 'البيانات الضخمة'],
    'hadoop': ['hadoop', 'هادوب'],
    'spark': ['spark', 'سبارك'],
    
    # Other Technical
    'rest api': ['rest', 'restful', 'api', 'rest api', 'واجهة برمجية'],
    'microservices': ['microservices', 'خدمات مصغرة'],
    'graphql': ['graphql', 'جراف كيو إل'],
    'json': ['json', 'جي سون'],
    'xml': ['xml', 'إكس إم إل']
}

def get_all_skill_variants():
    """Get all skill variants (English + Arabic) as a flat set"""
    all_variants = set()
    for variants in BILINGUAL_SKILLS.values():
        all_variants.update([v.lower() for v in variants])
    return all_variants

def normalize_skill(skill_text: str) -> str:
    """
    Normalize a skill (Arabic or English) to its canonical English form
    
    Args:
        skill_text: Skill in any language
        
    Returns:
        Canonical English skill name or original if not found
    """
    skill_lower = skill_text.lower().strip()
    
    for canonical, variants in BILINGUAL_SKILLS.items():
        if skill_lower in [v.lower() for v in variants]:
            return canonical
    
    return skill_text
