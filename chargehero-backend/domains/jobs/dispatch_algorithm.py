"""Dispatch algorithm for intelligent job assignment to engineers.

Scoring factors:
1. Skill match (certified for this charger brand/type) - 40%
2. Proximity (distance to job location) - 30%
3. Rating (engineer reputation) - 20%
4. Availability (not currently on a job) - 10%
"""

import logging
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Earth radius in kilometers
EARTH_RADIUS_KM = 6371


@dataclass
class DispatchScore:
    """Score breakdown for engineer assignment."""
    engineer_id: str
    total_score: float
    skill_match_score: float  # 0-40
    proximity_score: float  # 0-30
    rating_score: float  # 0-20
    availability_score: float  # 0-10
    distance_km: Optional[float] = None
    is_certified: bool = False
    is_available: bool = True


class DispatchAlgorithm:
    """Algorithm for intelligent job dispatch to engineers."""

    # Maximum distance to consider engineer (in kilometers)
    MAX_DISTANCE_KM = 50

    # Minimum proximity score to be eligible (before skill/rating filters)
    MIN_PROXIMITY_SCORE = 5  # Engineer must be within ~45km

    def __init__(self, db=None):
        """Initialize dispatch algorithm."""
        self.db = db

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula.

        Args:
            lat1, lon1: Charger location
            lat2, lon2: Engineer location

        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        distance = EARTH_RADIUS_KM * c

        return distance

    def calculate_skill_match_score(self, engineer_skills: List[Dict], charger_brand: str, charger_type: str) -> Tuple[float, bool]:
        """
        Calculate skill match score based on certifications.

        Score breakdown:
        - Has matching certification: 40 points
        - Has experience with same brand: 20 points
        - Has experience with any charger: 10 points
        - No experience: 0 points

        Args:
            engineer_skills: List of engineer skill records
            charger_brand: Brand of charger for the job
            charger_type: Type/model of charger for the job

        Returns:
            (score: 0-40, is_certified: bool)
        """
        if not engineer_skills:
            return 0.0, False

        is_certified = False
        has_brand_match = False

        for skill in engineer_skills:
            if (skill.get('charger_brand') == charger_brand and
                skill.get('charger_type') == charger_type and
                skill.get('is_certified')):
                is_certified = True
                return 40.0, True

            if skill.get('charger_brand') == charger_brand:
                has_brand_match = True

        # Brand match but not certified
        if has_brand_match:
            return 20.0, False

        # Has some charger experience
        if engineer_skills:
            return 10.0, False

        return 0.0, False

    def calculate_proximity_score(self, distance_km: float) -> float:
        """
        Calculate proximity score based on distance.

        Scoring:
        - < 5km: 30 points
        - 5-15km: 25 points
        - 15-30km: 15 points
        - 30-50km: 5 points
        - > 50km: 0 points (ineligible)

        Args:
            distance_km: Distance to job in kilometers

        Returns:
            Score 0-30
        """
        if distance_km <= 5:
            return 30.0
        elif distance_km <= 15:
            return 25.0
        elif distance_km <= 30:
            return 15.0
        elif distance_km <= self.MAX_DISTANCE_KM:
            return 5.0
        else:
            return 0.0

    def calculate_rating_score(self, engineer_rating: float, completed_jobs: int) -> float:
        """
        Calculate rating score based on engineer reputation.

        Scoring:
        - 4.8-5.0 stars: 20 points
        - 4.5-4.7 stars: 18 points
        - 4.0-4.4 stars: 15 points
        - 3.5-3.9 stars: 10 points
        - < 3.5 stars: 5 points
        - New engineer (no jobs): 12 points

        Args:
            engineer_rating: Average rating (0-5)
            completed_jobs: Number of completed jobs

        Returns:
            Score 0-20
        """
        if completed_jobs == 0:
            return 12.0  # New engineers get moderate score

        if engineer_rating >= 4.8:
            return 20.0
        elif engineer_rating >= 4.5:
            return 18.0
        elif engineer_rating >= 4.0:
            return 15.0
        elif engineer_rating >= 3.5:
            return 10.0
        else:
            return 5.0

    def calculate_availability_score(self, is_available: bool, current_jobs_count: int) -> float:
        """
        Calculate availability score.

        Scoring:
        - Fully available (0 jobs): 10 points
        - 1 job assigned: 7 points
        - 2 jobs assigned: 3 points
        - 3+ jobs assigned: 0 points (overloaded)

        Args:
            is_available: Whether engineer marked themselves available
            current_jobs_count: Current number of assigned jobs

        Returns:
            Score 0-10
        """
        if not is_available:
            return 0.0

        if current_jobs_count == 0:
            return 10.0
        elif current_jobs_count == 1:
            return 7.0
        elif current_jobs_count == 2:
            return 3.0
        else:
            return 0.0

    def score_engineer(self, engineer: Dict, charger: Dict, engineer_skills: List[Dict],
                       engineer_rating: float = 5.0, completed_jobs: int = 0,
                       current_jobs_count: int = 0) -> Optional[DispatchScore]:
        """
        Calculate comprehensive dispatch score for an engineer.

        Args:
            engineer: Engineer data with location and availability
            charger: Charger data with location and brand/type
            engineer_skills: Engineer's skills/certifications
            engineer_rating: Engineer's average rating (0-5)
            completed_jobs: Number of completed jobs
            current_jobs_count: Number of currently assigned jobs

        Returns:
            DispatchScore with breakdown, or None if engineer ineligible
        """
        try:
            engineer_id = engineer.get('id')
            engineer_lat = engineer.get('latitude')
            engineer_lon = engineer.get('longitude')
            is_available = engineer.get('availability', True)

            charger_lat = charger.get('latitude')
            charger_lon = charger.get('longitude')
            charger_brand = charger.get('brand')
            charger_type = charger.get('model')

            # Validate data
            if not all([engineer_id, engineer_lat, engineer_lon, charger_lat, charger_lon]):
                logger.warning(f"Missing location data for engineer {engineer_id} or charger")
                return None

            # Calculate distance
            distance_km = self.calculate_distance(charger_lat, charger_lon, engineer_lat, engineer_lon)

            # Check basic eligibility: within service area and minimum proximity
            if distance_km > self.MAX_DISTANCE_KM:
                logger.debug(f"Engineer {engineer_id} too far: {distance_km:.1f}km")
                return None

            # Calculate component scores
            skill_score, is_certified = self.calculate_skill_match_score(
                engineer_skills, charger_brand, charger_type
            )
            proximity_score = self.calculate_proximity_score(distance_km)
            rating_score = self.calculate_rating_score(engineer_rating, completed_jobs)
            availability_score = self.calculate_availability_score(is_available, current_jobs_count)

            # Total score (sum of all components)
            total_score = skill_score + proximity_score + rating_score + availability_score

            return DispatchScore(
                engineer_id=engineer_id,
                total_score=total_score,
                skill_match_score=skill_score,
                proximity_score=proximity_score,
                rating_score=rating_score,
                availability_score=availability_score,
                distance_km=distance_km,
                is_certified=is_certified,
                is_available=is_available
            )

        except Exception as e:
            logger.error(f"Error scoring engineer: {e}")
            return None

    def find_best_engineers(self, engineers_list: List[Dict], charger: Dict,
                           skills_map: Dict[str, List[Dict]],
                           ratings_map: Dict[str, float],
                           jobs_count_map: Dict[str, int],
                           top_n: int = 5) -> List[DispatchScore]:
        """
        Find top N best engineers for a job.

        Args:
            engineers_list: List of available engineers
            charger: Charger for the job
            skills_map: Map of engineer_id -> skills list
            ratings_map: Map of engineer_id -> average rating
            jobs_count_map: Map of engineer_id -> current job count
            top_n: Number of top engineers to return

        Returns:
            List of DispatchScore objects, sorted by score (highest first)
        """
        scores = []

        for engineer in engineers_list:
            engineer_id = engineer.get('id')
            skills = skills_map.get(engineer_id, [])
            rating = ratings_map.get(engineer_id, 5.0)
            completed_jobs = len([j for j in skills if j.get('is_certified')])
            current_jobs = jobs_count_map.get(engineer_id, 0)

            score = self.score_engineer(
                engineer, charger, skills,
                engineer_rating=rating,
                completed_jobs=completed_jobs,
                current_jobs_count=current_jobs
            )

            if score:
                scores.append(score)

        # Sort by total score descending
        scores.sort(key=lambda s: s.total_score, reverse=True)

        return scores[:top_n]

    def get_assignment_recommendation(self, scores: List[DispatchScore]) -> Optional[DispatchScore]:
        """
        Get recommended engineer for assignment.

        Recommendation logic:
        1. Certified engineer with high score (> 50) is top choice
        2. Very close engineer (< 10km) with good skill (> 30) is good
        3. Highest scorer overall if score > 40

        Args:
            scores: List of DispatchScore objects

        Returns:
            Recommended DispatchScore or None if no good match
        """
        if not scores:
            return None

        best = scores[0]

        # Certified engineer with decent total score
        for score in scores:
            if score.is_certified and score.total_score > 50:
                return score

        # Very close engineer with good skills
        for score in scores:
            if score.distance_km and score.distance_km < 10 and score.skill_match_score > 30:
                return score

        # Best overall if acceptable score
        if best.total_score > 40:
            return best

        # No good recommendation
        return None
