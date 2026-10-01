import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    DB_NAME = os.getenv('DB_NAME', 'data/college_pro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 3600
    
    def __init__(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required!")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///data/alumni.db'
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Course Categories and Degrees
COURSE_CATEGORIES = {
    'IT': {
        'label': 'IT / Technology',
        'UG': [
            'BCA – Bachelor of Computer Applications',
            'B.Sc Computer Science',
            'B.Sc Information Technology',
            'B.Tech Computer Science Engineering',
            'B.Tech Information Technology',
            'B.Tech AI & ML',
            'B.Tech Data Science',
            'B.Tech Cyber Security',
            'B.Tech Cloud Computing',
            'B.Tech Software Engineering',
            'B.Tech IoT',
            'B.Tech Computer Engineering',
            'B.Tech Blockchain Technology',
        ],
        'PG': [
            'MCA – Master of Computer Applications',
            'M.Sc Computer Science',
            'M.Sc Information Technology',
            'M.Tech Computer Science',
            'M.Tech Information Technology',
            'M.Tech AI / ML',
            'M.Tech Data Science',
            'M.Tech Cyber Security',
        ],
        'Diploma': [
            'Diploma in Computer Engineering',
            'Diploma in Information Technology',
            'Diploma in Software Engineering',
            'Full Stack Development',
            'Data Science',
            'AI / ML',
            'Cyber Security',
            'Cloud Computing',
        ]
    },
    'Engineering': {
        'label': 'Engineering (Non-IT)',
        'UG': [
            'B.Tech Mechanical Engineering',
            'B.Tech Civil Engineering',
            'B.Tech Electrical Engineering',
            'B.Tech Electronics & Communication (ECE)',
            'B.Tech Electronics & Instrumentation',
            'B.Tech Automobile Engineering',
            'B.Tech Chemical Engineering',
            'B.Tech Aerospace Engineering',
            'B.Tech Biomedical Engineering',
        ],
        'PG': [
            'M.Tech Mechanical Engineering',
            'M.Tech Civil Engineering',
            'M.Tech Electrical Engineering',
            'M.Tech Electronics Engineering',
            'M.Tech Structural Engineering',
            'M.Tech Thermal Engineering',
        ]
    },
    'Science': {
        'label': 'Science',
        'UG': [
            'B.Sc Mathematics',
            'B.Sc Physics',
            'B.Sc Chemistry',
            'B.Sc Biotechnology',
            'B.Sc Microbiology',
            'B.Sc Environmental Science',
        ],
        'PG': [
            'M.Sc Mathematics',
            'M.Sc Physics',
            'M.Sc Chemistry',
            'M.Sc Biotechnology',
            'M.Sc Microbiology',
        ]
    },
    'Commerce': {
        'label': 'Commerce & Management',
        'UG': [
            'B.Com',
            'BBA – Bachelor of Business Administration',
            'BMS – Business Management Studies',
        ],
        'PG': [
            'M.Com',
            'MBA – Master of Business Administration',
            'PGDM',
        ]
    },
    'Arts': {
        'label': 'Arts / Humanities',
        'UG': [
            'BA (History)',
            'BA (Political Science)',
            'BA (English)',
            'BA (Economics)',
            'BA (Sociology)',
            'BJMC – Journalism & Mass Communication',
            'BFA – Fine Arts',
        ],
        'PG': [
            'MA (English)',
            'MA (History)',
            'MA (Political Science)',
            'MA (Economics)',
            'MA (Sociology)',
            'MJMC – Journalism',
        ]
    },
    'Medical': {
        'label': 'Medical & Health Sciences',
        'UG': [
            'MBBS',
            'BDS',
            'B.Pharm',
            'B.Sc Nursing',
            'BPT – Physiotherapy',
            'BAMS',
            'BHMS',
        ],
        'PG': [
            'MD',
            'MS',
            'M.Pharm',
            'M.Sc Nursing',
        ]
    },
    'Law': {
        'label': 'Law / Education / Others',
        'UG': [
            'LLB',
            'BA LLB',
            'B.Ed',
            'Hotel Management (BHM)',
            'Fashion Designing',
            'Interior Designing',
        ],
        'PG': [
            'M.Ed',
            'D.El.Ed',
            'Hotel Management (MHM)',
        ]
    }
}

DEPARTMENTS = [
    'Information Technology',
    'Computer Science',
    'Computer Engineering',
    'Electronics & Communication',
    'Mechanical Engineering',
    'Civil Engineering',
    'Electrical Engineering',
    'Automobile Engineering',
    'Biotechnology',
    'Commerce',
    'Management',
    'Arts',
    'Science',
    'Others'
]

SEMESTERS = [
    ('1', '1st Semester'),
    ('2', '2nd Semester'),
    ('3', '3rd Semester'),
    ('4', '4th Semester'),
    ('5', '5th Semester'),
    ('6', '6th Semester'),
    ('7', '7th Semester'),
    ('8', '8th Semester'),
]
