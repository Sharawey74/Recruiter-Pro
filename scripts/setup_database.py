"""
Database Setup and Migration Script
Initialize database schema and optionally seed with test data
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import get_database
from src.core.config import get_config


def setup_database(clear_existing: bool = False):
    """
    Setup database with proper schema
    
    Args:
        clear_existing: Clear all existing data before setup
    """
    print("🔧 Starting Database Setup...")
    print("-" * 50)
    
    # Get configuration
    config = get_config()
    print(f"📁 Database Type: {config.database.type}")
    print(f"📁 Database Path: {config.database.connection_string}")
    print()
    
    # Initialize database
    db = get_database(reload=True)
    print("✅ Database connection established")
    
    # Clear existing data if requested
    if clear_existing:
        print("⚠️  Clearing existing data...")
        count = db.clear_all_matches()
        print(f"   Deleted {count} existing records")
        print()
    
    # Initialize schema
    print("📊 Creating database schema...")
    db.initialize_schema()
    print("✅ Schema initialized successfully")
    print()
    
    # Verify tables
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = [row['name'] for row in cursor.fetchall()]
    
    print("📋 Created Tables:")
    for table in tables:
        print(f"   - {table}")
    print()
    
    # Show statistics
    stats = db.get_statistics()
    print("📈 Database Statistics:")
    print(f"   Total Matches: {stats['total_matches']}")
    print(f"   Recent (24h): {stats['recent_24h']}")
    print()
    
    print("✅ DATABASE SETUP COMPLETE!")
    print("-" * 50)


def seed_test_data():
    """Seed database with test data for development"""
    from src.storage.models import (
        MatchResult, ScoreBreakdown, MatchDecision, DecisionType
    )
    
    print("🌱 Seeding Test Data...")
    print("-" * 50)
    
    db = get_database()
    
    # Sample test matches
    test_matches = [
        {
            "match_id": "test_match_001",
            "cv_id": "test_cv_001",
            "job_id": "test_job_001",
            "candidate_name": "Alice Johnson",
            "job_title": "Senior Python Developer",
            "final_score": 0.92,
            "decision": DecisionType.SHORTLIST,
            "confidence": 0.95,
            "reason": "Exceptional skill match with strong experience"
        },
        {
            "match_id": "test_match_002",
            "cv_id": "test_cv_002",
            "job_id": "test_job_001",
            "candidate_name": "Bob Smith",
            "job_title": "Senior Python Developer",
            "final_score": 0.68,
            "decision": DecisionType.REVIEW,
            "confidence": 0.72,
            "reason": "Good technical skills but lacks senior experience"
        },
        {
            "match_id": "test_match_003",
            "cv_id": "test_cv_003",
            "job_id": "test_job_002",
            "candidate_name": "Carol White",
            "job_title": "Data Engineer",
            "final_score": 0.85,
            "decision": DecisionType.SHORTLIST,
            "confidence": 0.88,
            "reason": "Strong data engineering background"
        }
    ]
    
    for test_data in test_matches:
        score_breakdown = ScoreBreakdown(
            skill_score=test_data["final_score"],
            experience_score=test_data["final_score"] - 0.05,
            education_score=0.8,
            keyword_score=0.7,
            rule_based_score=test_data["final_score"] - 0.02,
            hybrid_score=test_data["final_score"],
            matched_skills=["Python", "FastAPI", "SQL"],
            missing_skills=["Docker", "Kubernetes"]
        )
        
        decision = MatchDecision(
            decision=test_data["decision"],
            confidence=test_data["confidence"],
            reason=test_data["reason"]
        )
        
        match = MatchResult(
            match_id=test_data["match_id"],
            cv_id=test_data["cv_id"],
            job_id=test_data["job_id"],
            candidate_name=test_data["candidate_name"],
            job_title=test_data["job_title"],
            score_breakdown=score_breakdown,
            final_score=test_data["final_score"],
            decision=decision,
            processing_time_ms=120.5
        )
        
        db.save_match(match)
        print(f"✅ Created: {test_data['match_id']} - {test_data['candidate_name']}")
    
    print()
    print(f"✅ Seeded {len(test_matches)} test records")
    print("-" * 50)


def verify_database():
    """Verify database integrity"""
    print("🔍 Verifying Database...")
    print("-" * 50)
    
    db = get_database()
    stats = db.get_statistics()
    
    print("📊 Database Health Check:")
    print(f"   ✓ Total Records: {stats['total_matches']}")
    print(f"   ✓ Shortlisted: {stats['decision_counts'].get('shortlist', 0)}")
    print(f"   ✓ Under Review: {stats['decision_counts'].get('review', 0)}")
    print(f"   ✓ Rejected: {stats['decision_counts'].get('reject', 0)}")
    
    if stats['averages']['avg_score']:
        print(f"   ✓ Average Score: {stats['averages']['avg_score']:.3f}")
    
    if stats['averages']['avg_time']:
        print(f"   ✓ Average Processing Time: {stats['averages']['avg_time']:.1f}ms")
    
    print()
    print("✅ Database verification complete")
    print("-" * 50)


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup the Recruiter Pro database")
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all existing data'
    )
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Seed with test data'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database integrity'
    )
    
    args = parser.parse_args()
    
    # Always setup schema
    setup_database(clear_existing=args.clear)
    
    # Optional seeding
    if args.seed:
        seed_test_data()
    
    # Optional verification
    if args.verify:
        verify_database()
    
    print()
    print("🎉 All operations completed successfully!")


if __name__ == "__main__":
    main()
