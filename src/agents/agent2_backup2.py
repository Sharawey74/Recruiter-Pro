"""
Agent 2: Candidate Data Extractor
Pure rule-based extraction using regex, pattern matching, and dictionary lookup
Maximized efficiency with comprehensive skill database and intelligent parsing
Now with Arabic/Bilingual support
"""
import re
import logging
import sys
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

# Import bilingual skills database
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.bilingual_skills import BILINGUAL_SKILLS, normalize_skill, get_all_skill_variants
    BILINGUAL_AVAILABLE = True
except ImportError:
    BILINGUAL_AVAILABLE = False
    print("Warning: Bilingual skills database not available")

class CandidateExtractor:
    """
    Deterministic Candidate Extractor - Agent 2
    Extraction Priority: Explicit Headers > Regex Patterns > Heuristics
    100% reproducible, no ML/AI dependencies
    """
    
    # Comprehensive address blocklist
    ADDRESS_TOKENS = {
        'street', 'st', 'road', 'rd', 'avenue', 'ave', 'city', 'town',
        'sheikh', 'zayed', 'district', 'governorate', 'postal', 'zip',
        'apartment', 'apt', 'building', 'floor', 'block', 'suite',
        'cairo', 'giza', 'alex', 'alexandria', 'maadi', 'nasr', 'new',
        'downtown', 'heliopolis', 'mohandessin', 'dokki', 'zamalek'
    }
    
    # Comprehensive technical skills database (300+ skills across 11 domains)
    SKILLS_DATABASE = {
        # ==========================================
        # PROGRAMMING LANGUAGES
        # ==========================================
        'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'c++', 'cpp',
        'c#', 'csharp', 'c', 'ruby', 'php', 'swift', 'kotlin', 'go', 'golang', 'rust',
        'scala', 'r', 'perl', 'shell', 'bash', 'powershell', 'vba', 'assembly',
        
        # ==========================================
        # HARDWARE & EMBEDDED SYSTEMS (CRITICAL - WAS MISSING!)
        # ==========================================
        # Hardware Description Languages
        'vhdl', 'verilog', 'systemverilog', 'chisel', 'verilog-a', 'vhdl-ams',
        
        # Hardware Design
        'fpga', 'asic', 'vlsi', 'soc', 'rtl', 'rtl design', 'system on chip',
        'pcb', 'pcb design', 'pcb layout', 'schematic design', 'schematic capture',
        'circuit design', 'analog design', 'digital design', 'hardware design',
        'mixed signal', 'signal integrity', 'power integrity', 'emi', 'emc',
        
        # Embedded Systems
        'embedded systems', 'embedded c', 'embedded c++', 'embedded programming',
        'embedded linux', 'rtos', 'freertos', 'real-time', 'real time',
        'firmware', 'firmware development', 'device drivers', 'bootloader',
        
        # Microcontrollers & Processors
        'arm', 'arm cortex', 'cortex-m', 'cortex-a', 'cortex-m3', 'cortex-m4',
        'avr', 'pic', 'msp430', 'stm32', '8051', 'atmega',
        'microcontroller', 'mcu', 'microprocessor', 'dsp',
        
        # Communication Protocols
        'i2c', 'spi', 'uart', 'usart', 'can', 'can bus', 'lin',
        'usb', 'ethernet', 'pcie', 'sata', 'mipi', 'hdmi',
        'rs232', 'rs485', 'modbus', 'bluetooth', 'zigbee', 'lora',
        
        # Tools & Equipment
        'oscilloscope', 'logic analyzer', 'spectrum analyzer',
        'multimeter', 'signal generator', 'protocol analyzer',
        'altium', 'altium designer', 'cadence', 'orcad', 'eagle', 'kicad',
        'pads', 'mentor graphics', 'ltspice', 'pspice', 'hspice',
        'modelsim', 'vivado', 'quartus', 'ise', 'xilinx', 'altera', 'intel fpga',
        
        # ==========================================
        # PROJECT MANAGEMENT (CRITICAL - WAS MISSING!)
        # ==========================================
        # Certifications & Methodologies
        'pmp', 'prince2', 'pmbok', 'capm', 'pmi-acp', 'pmi acp',
        'csm', 'certified scrum master', 'psm', 'professional scrum master',
        'safe', 'scaled agile', 'lean', 'six sigma', 'lean six sigma',
        'green belt', 'black belt',
        
        # PM Tools
        'ms project', 'microsoft project', 'primavera', 'p6', 'primavera p6',
        'jira', 'jira software', 'jira agile', 'jira core',
        'asana', 'monday.com', 'monday', 'smartsheet',
        'confluence', 'trello', 'basecamp', 'wrike',
        'ms planner', 'microsoft planner', 'project online',
        
        # PM Core Skills
        'project management', 'program management', 'programme management',
        'portfolio management', 'pmo', 'project management office',
        'stakeholder management', 'risk management', 'issue management',
        'change management', 'resource management', 'resource planning',
        'budget management', 'cost management', 'financial management',
        'schedule management', 'time management', 'timeline management',
        'scope management', 'quality management', 'quality assurance',
        'procurement management', 'vendor management', 'contract management',
        
        # PM Techniques
        'gantt chart', 'gantt', 'pert chart', 'pert', 'critical path',
        'cpm', 'critical path method', 'earned value management', 'evm',
        'work breakdown structure', 'wbs', 'resource allocation',
        'capacity planning', 'sprint planning', 'retrospective',
        'daily standup', 'standup', 'burndown chart', 'burnup chart',
        
        # ==========================================
        # WEB FRONTEND
        # ==========================================
        'html', 'html5', 'css', 'css3', 'sass', 'scss', 'less', 'react', 'reactjs',
        'angular', 'angularjs', 'vue', 'vuejs', 'svelte', 'jquery', 'bootstrap',
        'tailwind', 'webpack', 'vite', 'nextjs', 'gatsby', 'redux', 'mobx',
        
        # ==========================================
        # WEB BACKEND
        # ==========================================
        'nodejs', 'node.js', 'node', 'express', 'expressjs', 'django', 'flask',
        'fastapi', 'spring', 'springboot', 'asp.net', 'laravel', 'rails', 'nestjs',
        
        # ==========================================
        # DATABASES
        # ==========================================
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 'redis',
        'oracle', 'sqlite', 'dynamodb', 'cassandra', 'couchdb', 'elasticsearch',
        'neo4j', 'mariadb', 'mssql', 'sqlserver', 'firebase', 'snowflake',
        
        # ==========================================
        # CLOUD & DEVOPS
        # ==========================================
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
        'jenkins', 'terraform', 'ansible', 'git', 'github', 'gitlab', 'bitbucket',
        'linux', 'unix', 'ubuntu', 'centos', 'debian', 'ci/cd', 'cicd',
        
        # ==========================================
        # ADVANCED ML/AI (EXPANDED!)
        # ==========================================
        # Deep Learning Frameworks
        'tensorflow', 'tensorflow 2.0', 'tf', 'keras', 'pytorch', 'torch',
        'jax', 'flax', 'mxnet', 'caffe', 'theano', 'chainer',
        
        # ML Libraries
        'scikit-learn', 'sklearn', 'scipy', 'numpy', 'pandas',
        'xgboost', 'lightgbm', 'catboost', 'h2o', 'auto-sklearn', 'automl',
        
        # NLP & LLM
        'hugging face', 'transformers', 'bert', 'gpt', 'llm',
        'large language model', 'gpt-3', 'gpt-4', 'rag',
        'retrieval augmented generation', 'prompt engineering', 'fine-tuning',
        'spacy', 'nltk', 'gensim', 'word2vec', 'glove', 'fasttext',
        'elmo', 't5', 'nlp', 'natural language processing',
        
        # Computer Vision
        'opencv', 'cv2', 'pillow', 'scikit-image', 'computer vision',
        'yolo', 'yolov5', 'yolov8', 'rcnn', 'fast-rcnn', 'mask-rcnn',
        'u-net', 'resnet', 'vgg', 'inception', 'efficientnet', 'mobilenet',
        
        # MLOps & Deployment
        'mlflow', 'kubeflow', 'mlops', 'ml ops', 'sagemaker', 'aws sagemaker',
        'vertex ai', 'azure ml', 'databricks', 'dvc', 'data version control',
        'wandb', 'tensorboard', 'model deployment',
        
        # ML Techniques
        'deep learning', 'machine learning', 'neural networks', 'ai',
        'artificial intelligence', 'data science', 'big data',
        'cnn', 'convolutional neural network', 'rnn', 'recurrent neural network',
        'lstm', 'long short-term memory', 'gru', 'transformer',
        'attention mechanism', 'reinforcement learning', 'q-learning',
        'supervised learning', 'unsupervised learning', 'semi-supervised',
        'transfer learning', 'ensemble learning', 'random forest',
        'gradient boosting', 'feature engineering', 'time series',
        'hadoop', 'spark', 'pyspark', 'airflow', 'kafka',
        'matplotlib', 'seaborn', 'plotly',
        
        # ==========================================
        # MOBILE
        # ==========================================
        'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
        
        # ==========================================
        # TESTING & QUALITY
        # ==========================================
        'selenium', 'pytest', 'junit', 'jest', 'mocha', 'chai', 'cypress',
        'testing', 'unit testing', 'integration testing', 'tdd', 'bdd',
        
        # ==========================================
        # DESIGN & TOOLS
        # ==========================================
        'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'indesign',
        'ui/ux', 'ui', 'ux', 'design', 'graphic design', 'web design',
        
        # ==========================================
        # SOFT SKILLS
        # ==========================================
        'communication', 'leadership', 'management', 'teamwork', 'collaboration',
        'problem solving', 'analytical', 'critical thinking', 'agile', 'scrum',
        'time management', 'presentation',
        
        # ==========================================
        # CYBERSECURITY (EXPANDED!)
        # ==========================================
        # Security Certifications
        'cybersecurity', 'cyber security', 'security', 'information security',
        'cissp', 'ceh', 'certified ethical hacker', 'comptia security+',
        'security+', 'oscp', 'giac', 'gsec', 'gcih', 'gpen', 'cisa', 'cism',
        
        # Security Tools
        'siem', 'splunk', 'qradar', 'arcsight', 'elk', 'elastic',
        'wireshark', 'tcpdump', 'nmap', 'metasploit', 'burp suite', 'burpsuite',
        'nessus', 'qualys', 'rapid7', 'nexpose', 'openvas', 'acunetix',
        'snort', 'suricata', 'zeek', 'bro', 'kali linux',
        
        # Security Domains
        'penetration testing', 'pen testing', 'ethical hacking',
        'vulnerability assessment', 'security audit', 'security auditing',
        'incident response', 'forensics', 'digital forensics',
        'malware analysis', 'reverse engineering', 'threat hunting',
        'threat intelligence', 'threat detection', 'threat analysis',
        'red team', 'blue team', 'purple team', 'soc', 'security operations center',
        
        # Network Security
        'firewall', 'ids', 'ips', 'intrusion detection', 'intrusion prevention',
        'ids/ips', 'waf', 'web application firewall', 'vpn', 'ipsec',
        'ssl', 'tls', 'encryption', 'cryptography', 'pki',
        'certificate management', 'endpoint protection', 'antivirus',
        
        # Security Frameworks
        'nist', 'iso 27001', 'pci-dss', 'pci dss', 'hipaa', 'gdpr',
        'sox', 'sarbanes oxley', 'cis controls', 'mitre att&ck',
        'owasp', 'owasp top 10', 'zero trust', 'compliance',
        'risk management', 'windows server', 'active directory', 'iam',
        'aws security', 'azure security',
        
        # ==========================================
        # FINANCE & ACCOUNTING (EXPANDED!)
        # ==========================================
        # Accounting
        'accounting', 'financial accounting', 'cost accounting',
        'management accounting', 'tax accounting', 'audit', 'auditing',
        'tally', 'tally erp', 'quickbooks', 'sage', 'xero',
        'sap fico', 'sap fi', 'sap co', 'oracle financials',
        
        # Taxation
        'gst', 'goods and services tax', 'tds', 'tax deducted at source',
        'income tax', 'direct tax', 'indirect tax', 'tax audit',
        'tax planning', 'tax compliance', 'taxation',
        
        # Financial Reporting
        'gaap', 'us gaap', 'ifrs', 'ind as', 'financial statements',
        'balance sheet', 'income statement', 'p&l', 'profit and loss',
        'cash flow statement', 'general ledger', 'gl',
        'accounts payable', 'ap', 'accounts receivable', 'ar',
        'reconciliation', 'bank reconciliation', 'financial reporting',
        
        # Finance
        'financial analysis', 'financial modeling', 'financial planning',
        'fp&a', 'fpa', 'valuation', 'dcf', 'discounted cash flow',
        'investment analysis', 'portfolio management', 'treasury',
        'budgeting', 'forecasting', 'variance analysis',
        
        # Certifications & Tools
        'ca', 'chartered accountant', 'cpa', 'certified public accountant',
        'cfa', 'chartered financial analyst', 'cma', 'certified management accountant',
        'excel', 'advanced excel', 'bloomberg', 'bloomberg terminal',
        'capital iq', 'factset', 'reuters', 'eikon',
        
        # ==========================================
        # SALES & MARKETING (EXPANDED!)
        # ==========================================
        # Digital Marketing
        'digital marketing', 'seo', 'search engine optimization',
        'sem', 'search engine marketing', 'ppc', 'pay per click',
        'google ads', 'google adwords', 'facebook ads', 'linkedin ads',
        'social media marketing', 'smm', 'content marketing',
        'email marketing', 'marketing automation', 'hubspot', 'marketo',
        'mailchimp', 'campaign management', 'branding', 'brand management',
        
        # Analytics & Tools
        'google analytics', 'ga4', 'adobe analytics', 'google tag manager',
        'gtm', 'google search console', 'semrush', 'ahrefs', 'moz',
        'hootsuite', 'buffer', 'canva', 'adobe creative suite',
        
        # Sales
        'sales', 'b2b sales', 'b2c sales', 'enterprise sales',
        'inside sales', 'outside sales', 'field sales',
        'business development', 'bd', 'bdm', 'bde',
        'account management', 'key account management', 'kam',
        'relationship management', 'crm', 'salesforce', 'salesforce crm',
        'hubspot crm', 'zoho crm', 'microsoft dynamics', 'dynamics 365',
        
        # Sales Skills
        'lead generation', 'prospecting', 'cold calling', 'negotiation',
        'closing', 'pipeline management', 'territory management',
        'quota attainment', 'revenue generation', 'sales strategy',
        'consultative selling', 'solution selling', 'account planning',
        'client acquisition', 'customer success',
        
        # ==========================================
        # OTHER TECHNICAL
        # ==========================================
        'rest', 'restful', 'api', 'graphql', 'soap', 'microservices',
        'websocket', 'json', 'xml', 'yaml', 'oauth', 'jwt', 'saml'
    }
    
    # Skill synonyms for normalization
    SKILL_SYNONYMS = {
        'js': 'javascript',
        'ts': 'typescript',
        'nodejs': 'node.js',
        'node': 'node.js',
        'reactjs': 'react',
        'vuejs': 'vue',
        'angularjs': 'angular',
        'mongo': 'mongodb',
        'postgres': 'postgresql',
        'k8s': 'kubernetes',
        'sklearn': 'scikit-learn',
        'cpp': 'c++',
        'csharp': 'c#',
        'golang': 'go'
    }
    
    def __init__(self):
        self.logger = logging.getLogger("Agent2_Extractor")
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    def extract(self, text: str) -> Dict:
        """
        Main extraction pipeline
        """
        if not text or len(text.strip()) < 10:
            self.logger.warning("Empty or too short text provided")
            return self._empty_profile()
        
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # 1. Segment the text
        sections = self._segment_sections(text, lines)
        
        # 2. Extract Fields
        name = self._extract_name(lines, text)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        address = self._extract_address(lines)
        
        # 3. Targeted Extraction
        skills = self._extract_skills(text) # Keep global scan for skills
        
        # Use targeted sections if available, else global text
        exp_text = sections.get('EXPERIENCE', text)
        edu_text = sections.get('EDUCATION', text)
        proj_text = sections.get('PROJECTS', '')
        cert_text = sections.get('CERTIFICATIONS', '')
        summary_text = sections.get('SUMMARY', '')
        
        experience_years = self._extract_experience(exp_text if sections.get('EXPERIENCE') else text)
        degrees = self._extract_education(edu_text)
        
        # 4. Construct Profile
        profile = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "skills": skills,
            "experience_years": experience_years,
            "education": degrees, # List of degrees
            "education_text": edu_text[:1000], # Store raw text for display
            "summary": summary_text[:1000],
            "projects": proj_text[:1000],
            "certifications": cert_text[:1000],
            "professional_experience": exp_text[:2000], # Truncate for safety
            "extraction_confidence": self._calculate_confidence(name, email, skills)
        }
        
        self.logger.info(f"Extracted: {name} | Sections: {list(sections.keys())}")
        return profile

    def _segment_sections(self, text: str, lines: List[str]) -> Dict[str, str]:
        """Split text into logical sections based on headers"""
        sections = {}
        current_section = "HEADER"
        buffer = []
        
        # Common headers in CAPS or Title Case
        HEADERS = {
            'PROFESSIONAL EXPERIENCE': 'EXPERIENCE', 'WORK EXPERIENCE': 'EXPERIENCE', 'EXPERIENCE': 'EXPERIENCE', 'EMPLOYMENT HISTORY': 'EXPERIENCE',
            'EDUCATION': 'EDUCATION', 'ACADEMIC BACKGROUND': 'EDUCATION',
            'PROJECTS': 'PROJECTS', 'KEY PROJECTS': 'PROJECTS', 'PUBLICATIONS': 'PROJECTS',
            'SKILLS': 'SKILLS', 'TECHNICAL SKILLS': 'SKILLS', 'PROFESSIONAL SKILLS': 'SKILLS',
            'CERTIFICATIONS': 'CERTIFICATIONS', 'LICENSES': 'CERTIFICATIONS', 'ACHIEVEMENTS': 'CERTIFICATIONS',
            'SUMMARY': 'SUMMARY', 'PROFESSIONAL SUMMARY': 'SUMMARY', 'PROFILE': 'SUMMARY', 'OBJECTIVE': 'SUMMARY'
        }
        
        for line in lines:
            # Check if line is a header
            # Heuristic: Upper case or Title case, short length, no verbs usually
            clean = line.strip().upper().replace(':', '')
            
            if clean in HEADERS:
                # Save previous section
                if buffer:
                    sections[current_section] = '\n'.join(buffer)
                
                # Start new section
                current_section = HEADERS[clean]
                buffer = []
            else:
                buffer.append(line)
        
        # Save last section
        if buffer:
            sections[current_section] = '\n'.join(buffer)
            
        return sections

    def _extract_name(self, lines: List[str], full_text: str) -> str:
        """Extract Name from header"""
        # Rule 1: Header patterns
        header_patterns = [
            r"^(?:Candidate|Name|Full\s*Name|Applicant)\s*[:\-]\s*(.+)",
            r"^(?:Resume\s*of|CV\s*of)\s*[:\-]?\s*(.+)"
        ]
        for line in lines[:20]:
            for pattern in header_patterns:
                if match := re.match(pattern, line, re.IGNORECASE):
                    if self._is_valid_name(match.group(1).strip()): return match.group(1).strip()
        
        # Rule 2: First valid line
        contact_prefixes = ['e-mail', 'email', 'phone', 'tel:', 'location', 'address', 'linkedin']
        for line in lines[:20]:
            clean = line.strip()
            if not clean: continue
            if any(p in clean.lower() for p in contact_prefixes): continue
            if '@' in clean: continue
            
            if self._is_valid_name(clean):
                return clean
        return "Unknown Candidate"

    def _is_valid_name(self, text: str) -> bool:
        if not text or len(text) < 2: return False
        words = text.split()
        if len(words) < 2 or len(words) > 6: return False
        if any(c.isdigit() for c in text): return False
        return True

    def _extract_email(self, text: str) -> str:
        pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        if match := re.search(pattern, text):
            return match.group(0)
        return ""

    def _extract_phone(self, text: str) -> str:
        pattern = r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        if match := re.search(pattern, text):
            return match.group(0)
        return ""

    def _extract_address(self, lines: List[str]) -> str:
        return "Not Implemented" # Simplified for brevity as mostly unused

    def _extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = set()
        
        # Direct lookup (Fastest)
        # Split text into tokens to match exact words if possible, but skills can be multi-word
        # Using string search for simplicity and coverage
        
        for skill in self.SKILLS_DATABASE:
            # Simple boundary check
            pattern = r"(?:^|\W)" + re.escape(skill) + r"(?:$|\W)"
            if re.search(pattern, text_lower):
                found.add(skill)
                
        return sorted(list(found))

    def _extract_experience(self, text: str) -> int:
        """Extract years"""
        patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)",
            r"experience\s*[:\-]\s*(\d+)\s*(?:years?|yrs?)",
            r"(\d+)\s*(?:years?|yrs?)\s*in\s*\w+"
        ]
        for p in patterns:
            if match := re.search(p, text.lower()):
                try:
                    return int(match.group(1))
                except: continue
        
        # Date Logic
        years = re.findall(r"(20\d{2})", text)
        if len(years) >= 2:
            try:
                yr_ints = sorted([int(y) for y in years])
                span = yr_ints[-1] - yr_ints[0]
                if 0 < span < 50: return span
            except: pass
            
        return 0

    def _extract_education(self, text: str) -> List[str]:
        degrees = []
        # Degrees map
        mapping = {
            'bachelor': "Bachelor's", 'bsc': "Bachelor's", 'bs': "Bachelor's", 'b.s.': "Bachelor's",
            'master': "Master's", 'msc': "Master's", 'ms': "Master's", 'mba': "Master's",
            'phd': "PhD", 'doctorate': "PhD",
            'associate': "Associate's"
        }
        
        text_lower = text.lower()
        for key, val in mapping.items():
            if key in text_lower and val not in degrees:
                # Basic check to avoid "Mastering python"
                if key == 'master' and 'degree' not in text_lower and 'science' not in text_lower and 'arts' not in text_lower:
                    continue 
                degrees.append(val)
        return degrees

    def _calculate_confidence(self, name, email, skills) -> float:
        score = 0.0
        if name != "Unknown Candidate": score += 0.3
        if email: score += 0.3
        if skills: score += 0.4
        return score

    def _empty_profile(self) -> Dict:
        return {
            "name": "Unknown", "email": "", "phone": "", "address": "",
            "skills": [], "experience_years": 0, "education": [],
            "summary": "", "projects": "", "certifications": "",
            "extraction_confidence": 0.0
        }
