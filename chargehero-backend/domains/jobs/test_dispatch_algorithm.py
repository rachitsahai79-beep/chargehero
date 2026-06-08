"""Tests for dispatch algorithm."""

import pytest
import math
from domains.jobs.dispatch_algorithm import DispatchAlgorithm, DispatchScore


@pytest.fixture
def algorithm():
    """Create dispatch algorithm instance."""
    return DispatchAlgorithm()


# ============================================================================
# Distance Calculation Tests
# ============================================================================

class TestDistanceCalculation:
    """Test Haversine distance calculation."""

    def test_same_location(self, algorithm):
        """Distance at same location should be ~0."""
        distance = algorithm.calculate_distance(28.7041, 77.1025, 28.7041, 77.1025)
        assert distance < 0.1  # Less than 100 meters

    def test_known_distance_delhi_to_agra(self, algorithm):
        """Test known distance between Delhi and Agra."""
        # Delhi: 28.7041°N, 77.1025°E
        # Agra: 27.1767°N, 78.0081°E
        # Approximate distance: 192 km
        distance = algorithm.calculate_distance(28.7041, 77.1025, 27.1767, 78.0081)
        assert 185 < distance < 200

    def test_distance_calculation_consistency(self, algorithm):
        """Distance should be same regardless of calculation direction."""
        dist_a_to_b = algorithm.calculate_distance(0, 0, 10, 10)
        dist_b_to_a = algorithm.calculate_distance(10, 10, 0, 0)
        assert abs(dist_a_to_b - dist_b_to_a) < 0.01


# ============================================================================
# Skill Match Score Tests
# ============================================================================

class TestSkillMatchScore:
    """Test skill match scoring."""

    def test_certified_match(self, algorithm):
        """Certified engineer gets maximum score."""
        skills = [
            {'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': True}
        ]
        score, is_certified = algorithm.calculate_skill_match_score(skills, 'ABB', '22kW')
        assert score == 40.0
        assert is_certified is True

    def test_certified_different_type(self, algorithm):
        """Different type gets partial credit."""
        skills = [
            {'charger_brand': 'ABB', 'charger_type': '7.4kW', 'is_certified': True}
        ]
        score, is_certified = algorithm.calculate_skill_match_score(skills, 'ABB', '22kW')
        assert score == 20.0  # Brand match
        assert is_certified is False

    def test_brand_match_no_certification(self, algorithm):
        """Brand match without certification gets 20 points."""
        skills = [
            {'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': False}
        ]
        score, is_certified = algorithm.calculate_skill_match_score(skills, 'ABB', '22kW')
        assert score == 20.0
        assert is_certified is False

    def test_no_match_but_experience(self, algorithm):
        """Engineer with any experience gets 10 points."""
        skills = [
            {'charger_brand': 'Delta', 'charger_type': '7.4kW', 'is_certified': True}
        ]
        score, is_certified = algorithm.calculate_skill_match_score(skills, 'ABB', '22kW')
        assert score == 10.0
        assert is_certified is False

    def test_no_skills(self, algorithm):
        """No skills returns 0."""
        score, is_certified = algorithm.calculate_skill_match_score([], 'ABB', '22kW')
        assert score == 0.0
        assert is_certified is False


# ============================================================================
# Proximity Score Tests
# ============================================================================

class TestProximityScore:
    """Test proximity/distance scoring."""

    def test_very_close(self, algorithm):
        """Engineer within 5km gets 30 points."""
        score = algorithm.calculate_proximity_score(3.0)
        assert score == 30.0

    def test_near(self, algorithm):
        """Engineer 5-15km away gets 25 points."""
        score = algorithm.calculate_proximity_score(10.0)
        assert score == 25.0

    def test_moderate_distance(self, algorithm):
        """Engineer 15-30km away gets 15 points."""
        score = algorithm.calculate_proximity_score(20.0)
        assert score == 15.0

    def test_far_but_acceptable(self, algorithm):
        """Engineer 30-50km away gets 5 points."""
        score = algorithm.calculate_proximity_score(40.0)
        assert score == 5.0

    def test_too_far(self, algorithm):
        """Engineer > 50km away gets 0 points."""
        score = algorithm.calculate_proximity_score(60.0)
        assert score == 0.0

    def test_boundary_5km(self, algorithm):
        """Boundary at 5km."""
        score_at_5 = algorithm.calculate_proximity_score(5.0)
        score_just_over_5 = algorithm.calculate_proximity_score(5.1)
        assert score_at_5 == 30.0
        assert score_just_over_5 == 25.0


# ============================================================================
# Rating Score Tests
# ============================================================================

class TestRatingScore:
    """Test rating/reputation scoring."""

    def test_excellent_rating(self, algorithm):
        """4.8-5.0 rating gets 20 points."""
        score = algorithm.calculate_rating_score(4.9, 10)
        assert score == 20.0

    def test_very_good_rating(self, algorithm):
        """4.5-4.7 rating gets 18 points."""
        score = algorithm.calculate_rating_score(4.6, 10)
        assert score == 18.0

    def test_good_rating(self, algorithm):
        """4.0-4.4 rating gets 15 points."""
        score = algorithm.calculate_rating_score(4.2, 10)
        assert score == 15.0

    def test_acceptable_rating(self, algorithm):
        """3.5-3.9 rating gets 10 points."""
        score = algorithm.calculate_rating_score(3.7, 10)
        assert score == 10.0

    def test_poor_rating(self, algorithm):
        """< 3.5 rating gets 5 points."""
        score = algorithm.calculate_rating_score(3.2, 10)
        assert score == 5.0

    def test_new_engineer(self, algorithm):
        """New engineer (0 completed jobs) gets 12 points."""
        score = algorithm.calculate_rating_score(5.0, 0)
        assert score == 12.0

    def test_new_engineer_regardless_of_rating(self, algorithm):
        """New engineer gets 12 even if rating is low."""
        score = algorithm.calculate_rating_score(2.0, 0)
        assert score == 12.0


# ============================================================================
# Availability Score Tests
# ============================================================================

class TestAvailabilityScore:
    """Test availability scoring."""

    def test_fully_available(self, algorithm):
        """Available with 0 jobs gets 10 points."""
        score = algorithm.calculate_availability_score(True, 0)
        assert score == 10.0

    def test_one_job_assigned(self, algorithm):
        """Available with 1 job gets 7 points."""
        score = algorithm.calculate_availability_score(True, 1)
        assert score == 7.0

    def test_two_jobs_assigned(self, algorithm):
        """Available with 2 jobs gets 3 points."""
        score = algorithm.calculate_availability_score(True, 2)
        assert score == 3.0

    def test_overloaded(self, algorithm):
        """Available with 3+ jobs gets 0 points (overloaded)."""
        score = algorithm.calculate_availability_score(True, 3)
        assert score == 0.0

    def test_not_available(self, algorithm):
        """Unavailable engineer gets 0 regardless of load."""
        score = algorithm.calculate_availability_score(False, 0)
        assert score == 0.0


# ============================================================================
# Complete Score Calculation Tests
# ============================================================================

class TestCompleteScoring:
    """Test full dispatch scoring."""

    def test_ideal_engineer(self, algorithm):
        """Perfect engineer close by with certification."""
        engineer = {
            'id': 'eng-1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'availability': True
        }
        charger = {
            'latitude': 28.7041,
            'longitude': 77.1025,
            'brand': 'ABB',
            'model': '22kW'
        }
        skills = [{'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': True}]

        score = algorithm.score_engineer(engineer, charger, skills, 4.9, 50, 0)

        assert score is not None
        assert score.total_score > 90  # Should be very high
        assert score.is_certified is True
        assert score.is_available is True

    def test_new_engineer_nearby(self, algorithm):
        """New engineer nearby without certification."""
        engineer = {
            'id': 'eng-1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'availability': True
        }
        charger = {
            'latitude': 28.7100,
            'longitude': 77.1100,
            'brand': 'ABB',
            'model': '22kW'
        }
        skills = []

        score = algorithm.score_engineer(engineer, charger, skills, 5.0, 0, 0)

        assert score is not None
        assert score.total_score > 40  # New engineer close by
        assert score.is_certified is False
        assert score.distance_km < 10

    def test_overloaded_engineer(self, algorithm):
        """Overloaded engineer scores lower due to availability penalty."""
        engineer = {
            'id': 'eng-1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'availability': True
        }
        charger = {
            'latitude': 28.7041,
            'longitude': 77.1025,
            'brand': 'ABB',
            'model': '22kW'
        }
        skills = [{'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': True}]

        score = algorithm.score_engineer(engineer, charger, skills, 4.9, 50, 3)  # 3 jobs

        assert score is not None
        assert score.availability_score == 0.0
        # Even certified nearby engineer loses 10 points from max when overloaded
        assert score.total_score == 90.0  # 40 + 30 + 20 + 0

        # Compare with available version
        score_available = algorithm.score_engineer(engineer, charger, skills, 4.9, 50, 0)
        assert score_available.total_score == 100.0  # Full score with availability

    def test_too_far_engineer(self, algorithm):
        """Engineer too far away returns None."""
        engineer = {
            'id': 'eng-1',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'availability': True
        }
        charger = {
            'latitude': 10.0,  # Much further south
            'longitude': 77.1025,
            'brand': 'ABB',
            'model': '22kW'
        }
        skills = [{'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': True}]

        score = algorithm.score_engineer(engineer, charger, skills, 4.9, 50, 0)

        assert score is None  # Too far away


# ============================================================================
# Best Engineers Selection Tests
# ============================================================================

class TestFindBestEngineers:
    """Test finding top engineers for a job."""

    def test_rank_by_score(self, algorithm):
        """Engineers ranked by score."""
        engineers = [
            {
                'id': 'eng-1',
                'latitude': 28.7041,
                'longitude': 77.1025,
                'availability': True
            },
            {
                'id': 'eng-2',
                'latitude': 28.7050,
                'longitude': 77.1050,
                'availability': True
            },
            {
                'id': 'eng-3',
                'latitude': 35.0,
                'longitude': 77.0,
                'availability': True
            }
        ]
        charger = {
            'latitude': 28.7041,
            'longitude': 77.1025,
            'brand': 'ABB',
            'model': '22kW'
        }
        skills_map = {
            'eng-1': [{'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': True}],
            'eng-2': [{'charger_brand': 'ABB', 'charger_type': '22kW', 'is_certified': False}],
            'eng-3': []
        }
        ratings = {'eng-1': 4.9, 'eng-2': 4.0, 'eng-3': 5.0}
        jobs_count = {'eng-1': 0, 'eng-2': 0, 'eng-3': 0}

        scores = algorithm.find_best_engineers(engineers, charger, skills_map, ratings, jobs_count, top_n=3)

        assert len(scores) <= 3
        assert scores[0].engineer_id == 'eng-1'  # Certified engineer at location
        assert scores[0].total_score > scores[1].total_score  # Properly ranked

    def test_top_n_limit(self, algorithm):
        """Respects top_n limit."""
        engineers = [
            {'id': f'eng-{i}', 'latitude': 28.7041 + i*0.001, 'longitude': 77.1025,
             'availability': True}
            for i in range(10)
        ]
        charger = {'latitude': 28.7041, 'longitude': 77.1025, 'brand': 'ABB', 'model': '22kW'}
        skills_map = {eng['id']: [] for eng in engineers}
        ratings = {eng['id']: 5.0 for eng in engineers}
        jobs_count = {eng['id']: 0 for eng in engineers}

        scores = algorithm.find_best_engineers(engineers, charger, skills_map, ratings, jobs_count, top_n=3)

        assert len(scores) == 3


# ============================================================================
# Recommendation Tests
# ============================================================================

class TestAssignmentRecommendation:
    """Test assignment recommendation logic."""

    def test_recommend_certified_engineer(self, algorithm):
        """Prefers certified engineer with good score."""
        scores = [
            DispatchScore('eng-1', 45, 10, 20, 10, 5, 10, is_certified=False),
            DispatchScore('eng-2', 55, 40, 10, 5, 0, 25, is_certified=True),
        ]

        recommendation = algorithm.get_assignment_recommendation(scores)

        assert recommendation is not None
        assert recommendation.engineer_id == 'eng-2'

    def test_recommend_closest_if_skilled(self, algorithm):
        """Prefers very close engineer with good skills."""
        scores = [
            DispatchScore('eng-1', 45, 20, 20, 5, 0, 45, is_certified=False),
            DispatchScore('eng-2', 50, 35, 25, 5, 0, 8, is_certified=False),
        ]

        recommendation = algorithm.get_assignment_recommendation(scores)

        assert recommendation is not None
        assert recommendation.engineer_id == 'eng-2'

    def test_recommend_best_if_no_excellent(self, algorithm):
        """Recommends best overall if no certified/nearby."""
        scores = [
            DispatchScore('eng-1', 42, 10, 20, 10, 2, 20, is_certified=False),
            DispatchScore('eng-2', 30, 5, 15, 10, 0, 40, is_certified=False),
        ]

        recommendation = algorithm.get_assignment_recommendation(scores)

        assert recommendation is not None
        assert recommendation.engineer_id == 'eng-1'

    def test_no_recommendation_if_poor_score(self, algorithm):
        """Returns None if all scores too low."""
        scores = [
            DispatchScore('eng-1', 25, 10, 10, 5, 0, 45, is_certified=False),
        ]

        recommendation = algorithm.get_assignment_recommendation(scores)

        assert recommendation is None

    def test_empty_list(self, algorithm):
        """Returns None for empty list."""
        recommendation = algorithm.get_assignment_recommendation([])

        assert recommendation is None
