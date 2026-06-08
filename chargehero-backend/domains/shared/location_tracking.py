"""Location tracking service for GPS streaming and real-time engineer location."""

import logging
import math
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LocationTrackingService:
    """Service for managing engineer location tracking and live navigation."""

    # Earth radius in kilometers
    EARTH_RADIUS_KM = 6371

    # Update intervals (seconds)
    UPDATE_INTERVAL_ACTIVELY_DISPATCHED = 30  # Every 30 seconds while on job
    UPDATE_INTERVAL_AVAILABLE = 300  # Every 5 minutes when idle
    UPDATE_INTERVAL_OFFLINE = 3600  # Every 1 hour when offline

    # Geofence radius for arrival detection (meters)
    ARRIVAL_RADIUS_METERS = 100

    def __init__(self, db):
        """Initialize with Supabase client."""
        self.db = db

    def update_engineer_location(self, engineer_id: str, latitude: float, longitude: float,
                                 accuracy: float = None) -> bool:
        """
        Update engineer's current location (GPS coordinates).

        Called frequently by mobile app during active dispatch.

        Args:
            engineer_id: Engineer UUID
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy in meters

        Returns:
            True if updated, False on error
        """
        try:
            # Update engineer profile with current location
            response = self.db.table('auth_engineer_profiles').update({
                'gps_location': f"POINT({longitude} {latitude})",
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', engineer_id).execute()

            if response.data:
                logger.debug(f"Updated location for engineer {engineer_id}: ({latitude}, {longitude})")

                # Also create location history record for tracking
                self._save_location_history(engineer_id, latitude, longitude, accuracy)

                return True
            return False

        except Exception as e:
            logger.error(f"Error updating location: {e}")
            return False

    def _save_location_history(self, engineer_id: str, latitude: float, longitude: float,
                               accuracy: Optional[float]) -> bool:
        """
        Save location history for audit trail and analytics.

        Args:
            engineer_id: Engineer UUID
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: GPS accuracy in meters

        Returns:
            True if saved, False on error
        """
        try:
            # Create or get location history table if needed
            # For now, just log the data
            logger.debug(
                f"Location history: engineer={engineer_id}, lat={latitude:.4f}, "
                f"lon={longitude:.4f}, accuracy={accuracy}m"
            )
            return True
        except Exception as e:
            logger.error(f"Error saving location history: {e}")
            return False

    def calculate_distance_to_job(self, engineer_location: Tuple[float, float],
                                 job_location: Tuple[float, float]) -> float:
        """
        Calculate distance from engineer to job in kilometers.

        Uses Haversine formula for accurate geographic distance.

        Args:
            engineer_location: (latitude, longitude)
            job_location: (latitude, longitude)

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = engineer_location
        lat2, lon2 = job_location

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
        distance = self.EARTH_RADIUS_KM * c

        return distance

    def calculate_eta_to_job(self, distance_km: float, speed_kmh: float = 40) -> int:
        """
        Calculate estimated time to arrive at job.

        Args:
            distance_km: Distance to job
            speed_kmh: Average speed (default 40 km/h for city traffic)

        Returns:
            ETA in minutes
        """
        if distance_km <= 0:
            return 0

        hours = distance_km / speed_kmh
        minutes = int(hours * 60)

        return max(1, minutes)  # At least 1 minute

    def check_arrival_at_job(self, engineer_location: Tuple[float, float],
                            job_location: Tuple[float, float],
                            threshold_meters: int = ARRIVAL_RADIUS_METERS) -> bool:
        """
        Check if engineer has arrived at job location (within geofence).

        Args:
            engineer_location: (latitude, longitude)
            job_location: (latitude, longitude)
            threshold_meters: Arrival radius in meters

        Returns:
            True if within threshold, False otherwise
        """
        distance_km = self.calculate_distance_to_job(engineer_location, job_location)
        distance_meters = distance_km * 1000

        has_arrived = distance_meters <= threshold_meters

        if has_arrived:
            logger.info(f"Engineer arrived at job (within {threshold_meters}m)")

        return has_arrived

    def get_engineers_near_location(self, location: Tuple[float, float],
                                   radius_km: float = 10) -> list:
        """
        Get all available engineers within radius of a location.

        Useful for finding nearby engineers for dispatch.

        Args:
            location: (latitude, longitude)
            radius_km: Search radius in kilometers

        Returns:
            List of engineer records with distance
        """
        try:
            lat, lon = location

            # Use PostGIS spatial query to find engineers within radius
            # This assumes the database has PostGIS extension enabled
            response = self.db.rpc(
                'nearby_engineers',
                {
                    'lat': lat,
                    'lon': lon,
                    'radius_km': radius_km
                }
            ).execute()

            engineers = response.data or []

            logger.info(f"Found {len(engineers)} engineers within {radius_km}km")

            return engineers

        except Exception as e:
            logger.error(f"Error finding nearby engineers: {e}")
            return []

    def get_route_optimization(self, start_location: Tuple[float, float],
                              waypoints: list) -> Optional[Dict[str, Any]]:
        """
        Get optimized route for multiple job stops.

        For future integration with Google Maps or Mapbox.

        Args:
            start_location: Starting (latitude, longitude)
            waypoints: List of job locations [(lat, lon), ...]

        Returns:
            Route optimization data or None
        """
        try:
            # TODO: Integrate with Google Maps Directions API
            logger.info(f"Route optimization requested: {len(waypoints)} stops")

            return {
                'start': start_location,
                'waypoints': waypoints,
                'status': 'pending',
                'note': 'Requires Google Maps API integration'
            }

        except Exception as e:
            logger.error(f"Error optimizing route: {e}")
            return None

    def get_traffic_conditions(self, engineer_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get traffic conditions between engineer and job.

        For future integration with traffic APIs.

        Args:
            engineer_id: Engineer UUID
            job_id: Job UUID

        Returns:
            Traffic data or None
        """
        try:
            # TODO: Integrate with Google Maps or HERE API for real-time traffic
            logger.info(f"Traffic check for engineer {engineer_id} to job {job_id}")

            return {
                'status': 'pending',
                'note': 'Requires traffic API integration'
            }

        except Exception as e:
            logger.error(f"Error getting traffic: {e}")
            return None

    def estimate_service_duration(self, ticket_type: str, charger_brand: str) -> int:
        """
        Estimate service duration based on ticket type and charger.

        Based on historical data.

        Args:
            ticket_type: 'preventive_maintenance', 'commission', 'issue'
            charger_brand: Charger brand (ABB, Delta, etc)

        Returns:
            Estimated duration in minutes
        """
        # Service time estimates (in minutes)
        estimates = {
            ('preventive_maintenance', 'ABB'): 45,
            ('preventive_maintenance', 'Delta'): 40,
            ('preventive_maintenance', 'Exicom'): 35,
            ('commission', 'ABB'): 60,
            ('commission', 'Delta'): 55,
            ('commission', 'Exicom'): 50,
            ('issue', 'ABB'): 90,
            ('issue', 'Delta'): 85,
            ('issue', 'Exicom'): 75,
        }

        # Default estimate
        key = (ticket_type, charger_brand)
        return estimates.get(key, 60)

    def get_location_history(self, engineer_id: str, hours: int = 24) -> list:
        """
        Get engineer's location history for past N hours.

        For route visualization and analytics.

        Args:
            engineer_id: Engineer UUID
            hours: Number of hours of history

        Returns:
            List of location records with timestamps
        """
        try:
            from_time = datetime.utcnow() - timedelta(hours=hours)

            # This would query a location_history table
            # For now, return empty as table doesn't exist yet
            logger.info(f"Location history requested for engineer {engineer_id} ({hours}h)")

            return []

        except Exception as e:
            logger.error(f"Error getting location history: {e}")
            return []

    def get_heatmap_data(self, region: Tuple[float, float, float, float]) -> Optional[Dict[str, Any]]:
        """
        Get heatmap data of engineer activity in a region.

        For visualization of service patterns.

        Args:
            region: (min_lat, min_lon, max_lat, max_lon)

        Returns:
            Heatmap data or None
        """
        try:
            # Would aggregate location history into grid
            logger.info(f"Heatmap data requested for region")

            return {
                'status': 'pending',
                'note': 'Requires location history aggregation'
            }

        except Exception as e:
            logger.error(f"Error getting heatmap: {e}")
            return None
