"""
SAGPT Backend - Seed Data Script
Run this to populate your database with sample experts for testing.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.models import Expert

# Sample expert data matching your website
demo_experts = [
    {
        "name": "Wei-Ming Chen",
        "company": "Chen & Associates Law Firm",
        "country": "Singapore",
        "country_code": "SG",
        "photo_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Legal Services", "Compliance", "Company Registration"],
        "languages": ["English", "Mandarin", "Malay"],
        "bio": "Leading corporate lawyer in Southeast Asia with 18 years of experience helping Chinese enterprises establish operations in Singapore and ASEAN markets.",
        "rating": 4.9,
        "experience_years": 18,
        "projects_count": 234,
        "membership_tier": "vip",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Aisha Al-Rashidi",
        "company": "Gulf Business Advisory Group",
        "country": "UAE",
        "country_code": "AE",
        "photo_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Tax & Finance", "Market Entry", "Government Relations"],
        "languages": ["Arabic", "English", "Hindi"],
        "bio": "Tax advisor and market entry specialist for GCC region. Expert in UAE corporate tax, VAT compliance, and SAGIA licensing.",
        "rating": 4.8,
        "experience_years": 12,
        "projects_count": 178,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Thomas Müller",
        "company": "Munich Financial Advisory GmbH",
        "country": "Germany",
        "country_code": "DE",
        "photo_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Tax & Finance", "Accounting", "M&A"],
        "languages": ["German", "English", "Mandarin"],
        "bio": "German tax and M&A specialist with expertise in cross-border transactions between China and EU markets.",
        "rating": 4.9,
        "experience_years": 20,
        "projects_count": 156,
        "membership_tier": "vip",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Priya Sharma",
        "company": "South Asia HR Solutions",
        "country": "India",
        "country_code": "IN",
        "photo_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Human Resources", "Compensation & Benefits", "Training"],
        "languages": ["English", "Hindi", "Tamil"],
        "bio": "HR consulting expert specializing in Indian labor law compliance, talent acquisition, and cross-cultural team management for Chinese companies.",
        "rating": 4.7,
        "experience_years": 15,
        "projects_count": 203,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Mohammed Al-Farsi",
        "company": "Riyadh Business Development Center",
        "country": "Saudi Arabia",
        "country_code": "SA",
        "photo_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Government Relations", "Market Entry", "Compliance"],
        "languages": ["Arabic", "English"],
        "bio": "Saudi government relations expert with deep connections in SAGIA, MISA, and local chambers. Specializes in helping Chinese firms navigate Saudi Vision 2030 opportunities.",
        "rating": 4.9,
        "experience_years": 19,
        "projects_count": 201,
        "membership_tier": "vip",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Sophie Laurent",
        "company": "Laurent & Picard Law Paris",
        "country": "France",
        "country_code": "FR",
        "photo_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Legal Services", "Intellectual Property", "Compliance"],
        "languages": ["French", "English", "Mandarin"],
        "bio": "Paris-based IP and compliance lawyer. Expert in EU GDPR, trademark registration, and French corporate law for Asian tech companies.",
        "rating": 4.9,
        "experience_years": 15,
        "projects_count": 142,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Kenji Tanaka",
        "company": "Tokyo Business Strategy Consulting K.K.",
        "country": "Japan",
        "country_code": "JP",
        "photo_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Market Entry", "Marketing", "Government Relations"],
        "languages": ["Japanese", "English", "Mandarin"],
        "bio": "Japan market entry strategist with 22 years helping Chinese brands localize for Japanese consumers. Expert in JETRO programs and Keiretsu partnerships.",
        "rating": 4.8,
        "experience_years": 22,
        "projects_count": 118,
        "membership_tier": "vip",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Budi Santoso",
        "company": "Jakarta Cross-Border Business Advisors",
        "country": "Indonesia",
        "country_code": "ID",
        "photo_url": "https://images.unsplash.com/photo-1504257432389-52343af06ae3?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Company Registration", "Tax & Finance", "Market Entry"],
        "languages": ["Indonesian", "English", "Mandarin"],
        "bio": "Indonesia company formation and tax specialist. Helps Chinese e-commerce and manufacturing firms navigate BKPM regulations and local partnership structures.",
        "rating": 4.7,
        "experience_years": 13,
        "projects_count": 156,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Carlos Mendoza",
        "company": "LatAm Digital Marketing Institute",
        "country": "Mexico",
        "country_code": "MX",
        "photo_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Marketing", "E-commerce", "Brand Strategy"],
        "languages": ["Spanish", "English", "Portuguese"],
        "bio": "Latin America digital marketing expert. Specializes in TikTok, Instagram, and local e-commerce platform strategies for Chinese brands entering Mexico and Brazil.",
        "rating": 4.8,
        "experience_years": 13,
        "projects_count": 167,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Jennifer Walsh",
        "company": "SF Tech Marketing Consulting",
        "country": "United States",
        "country_code": "US",
        "photo_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Marketing", "Brand Strategy", "E-commerce"],
        "languages": ["English", "Mandarin"],
        "bio": "Silicon Valley marketing strategist helping Chinese SaaS and hardware companies launch in US market. Expert in product-market fit and GTM strategy.",
        "rating": 4.8,
        "experience_years": 14,
        "projects_count": 189,
        "membership_tier": "vip",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Ana Kovačević",
        "company": "Eastern Europe Logistics & Supply Chain Institute",
        "country": "Serbia",
        "country_code": "RS",
        "photo_url": "https://images.unsplash.com/photo-1607746882042-944635dfe10e?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Logistics & Supply Chain", "Compliance", "Market Entry"],
        "languages": ["Serbian", "English", "Russian"],
        "bio": "Balkans logistics and supply chain expert. Specializes in cross-border warehousing, customs clearance, and EU-Asia trade corridor optimization.",
        "rating": 4.6,
        "experience_years": 11,
        "projects_count": 89,
        "membership_tier": "basic",
        "is_verified": True,
        "is_active": True
    },
    {
        "name": "Oluwaseun Adeyemi",
        "company": "West Africa Business Consulting Group",
        "country": "Nigeria",
        "country_code": "NG",
        "photo_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=200&h=200&fit=crop&crop=face",
        "specialties": ["Cross-border Payments", "Tax & Finance", "Market Entry"],
        "languages": ["English", "Yoruba", "French"],
        "bio": "Nigeria and West Africa business consultant. Expert in Naira currency hedging, local distributor networks, and AFCFTA trade compliance.",
        "rating": 4.7,
        "experience_years": 16,
        "projects_count": 145,
        "membership_tier": "pro",
        "is_verified": True,
        "is_active": True
    }
]

def seed_experts():
    db = SessionLocal()
    try:
        # Clear existing
        db.query(Expert).delete()
        db.commit()
        
        for expert_data in demo_experts:
            expert = Expert(**expert_data)
            db.add(expert)
        
        db.commit()
        print(f"Seeded {len(demo_experts)} experts successfully!")
        
        # List them
        experts = db.query(Expert).all()
        for e in experts:
            print(f"  - {e.name} ({e.country}): {', '.join(e.specialties[:2])}")
    
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Create tables first
    Base.metadata.create_all(bind=engine)
    seed_experts()
