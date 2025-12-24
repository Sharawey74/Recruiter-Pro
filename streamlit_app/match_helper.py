"""
Helper function to save match results to history
"""

def save_matches_to_history(result, history_manager):
    """Save match results to history file"""
    try:
        candidate_name = result.get('candidate_name', 'Unknown')
        matches = result.get('top_matches', [])
        
        for match in matches:
            match_data = {
                'candidate_name': candidate_name,
                'job_title': match.get('job_title', 'Unknown'),
                'job_id': match.get('job_id', 'N/A'),
                'decision': match.get('decision', 'REVIEW'),
                'confidence': match.get('confidence', 0.0),
                'match_label': match.get('match_label', 'Medium'),
                'matched_skills': match.get('skill_match', {}).get('matched_skills', []),
                'missing_skills': match.get('skill_match', {}).get('missing_skills', []),
                'experience_match_score': match.get('experience_match_score', 0.0),
                'skill_match_score': match.get('skill_match', {}).get('skill_match_score', 0.0),
                'explanation': match.get('explanation', '')
            }
            history_manager.save_match(match_data)
    except Exception as e:
        print(f"Error saving match history: {e}")
