"""
Environmental Monitoring Module
Integrates various environmental sensors and data sources
for multi-agent AI orchestration system
"""

import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class EnvironmentalData:
    """Environmental sensor data structure"""
    timestamp: datetime
    sensor_id: str
    data_type: str
    value: float
    unit: str
    location: Dict[str, float]
    
class EnvironmentalMonitor:
    """
    Main environmental monitoring class that collects and processes
    data from various environmental sensors
    """
    
    def __init__(self):
        self.sensors = {}
        self.data_buffer = []
        self.alert_thresholds = {
            "temperature": {"min": -10, "max": 50, "unit": "celsius"},
            "co2": {"min": 0, "max": 1000, "unit": "ppm"},
            "humidity": {"min": 20, "max": 80, "unit": "percent"},
            "water_quality": {"min": 6.5, "max": 8.5, "unit": "pH"}
        }
    
    async def add_sensor(self, sensor_id: str, sensor_type: str, location: Dict[str, float]):
        """Register a new environmental sensor"""
        self.sensors[sensor_id] = {
            "type": sensor_type,
            "location": location,
            "status": "active",
            "last_reading": None
        }
        print(f"Sensor {sensor_id} registered: {sensor_type} at {location}")
    
    async def collect_data(self, sensor_id: str) -> EnvironmentalData:
        """Simulate data collection from a sensor"""
        if sensor_id not in self.sensors:
            raise ValueError(f"Sensor {sensor_id} not found")
        
        sensor = self.sensors[sensor_id]
        
        # Simulate sensor readings based on type
        if sensor["type"] == "temperature":
            value = np.random.normal(20, 5)
            unit = "celsius"
        elif sensor["type"] == "co2":
            value = np.random.normal(400, 50)
            unit = "ppm"
        elif sensor["type"] == "humidity":
            value = np.random.normal(50, 10)
            unit = "percent"
        elif sensor["type"] == "water_quality":
            value = np.random.normal(7.0, 0.5)
            unit = "pH"
        else:
            value = np.random.random() * 100
            unit = "unknown"
        
        data = EnvironmentalData(
            timestamp=datetime.now(),
            sensor_id=sensor_id,
            data_type=sensor["type"],
            value=value,
            unit=unit,
            location=sensor["location"]
        )
        
        self.sensors[sensor_id]["last_reading"] = data
        self.data_buffer.append(data)
        
        return data
    
    async def check_alerts(self, data: EnvironmentalData) -> List[str]:
        """Check if sensor data triggers any alerts"""
        alerts = []
        
        if data.data_type in self.alert_thresholds:
            thresholds = self.alert_thresholds[data.data_type]
            
            if data.value < thresholds["min"]:
                alerts.append(f"LOW {data.data_type}: {data.value:.2f} {data.unit}")
            elif data.value > thresholds["max"]:
                alerts.append(f"HIGH {data.data_type}: {data.value:.2f} {data.unit}")
        
        return alerts
    
    async def monitor_environment(self, duration_seconds: int = 60):
        """Main monitoring loop"""
        print(f"Starting environmental monitoring for {duration_seconds} seconds...")
        
        # Add some example sensors
        await self.add_sensor("TEMP_001", "temperature", {"lat": 37.7749, "lon": -122.4194})
        await self.add_sensor("CO2_001", "co2", {"lat": 37.7749, "lon": -122.4194})
        await self.add_sensor("HUM_001", "humidity", {"lat": 37.7749, "lon": -122.4194})
        await self.add_sensor("WQ_001", "water_quality", {"lat": 37.7749, "lon": -122.4194})
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < duration_seconds:
            for sensor_id in self.sensors:
                try:
                    data = await self.collect_data(sensor_id)
                    alerts = await self.check_alerts(data)
                    
                    if alerts:
                        print(f"⚠️  ALERT from {sensor_id}: {', '.join(alerts)}")
                    else:
                        print(f"✓ {sensor_id}: {data.value:.2f} {data.unit}")
                    
                except Exception as e:
                    print(f"Error reading sensor {sensor_id}: {e}")
            
            await asyncio.sleep(5)  # Collect data every 5 seconds
        
        print(f"Monitoring complete. Collected {len(self.data_buffer)} data points.")
        return self.data_buffer

class BiodiversityTracker:
    """Track and analyze biodiversity metrics"""
    
    def __init__(self):
        self.species_data = {}
        self.habitat_health = {}
        
    async def record_species_observation(self, species: str, location: Dict[str, float], count: int):
        """Record a species observation"""
        if species not in self.species_data:
            self.species_data[species] = []
        
        self.species_data[species].append({
            "timestamp": datetime.now(),
            "location": location,
            "count": count
        })
        
        print(f"Recorded: {count} {species} at ({location['lat']:.4f}, {location['lon']:.4f})")
    
    async def calculate_diversity_index(self) -> float:
        """Calculate Shannon diversity index"""
        if not self.species_data:
            return 0.0
        
        total_count = sum(len(observations) for observations in self.species_data.values())
        diversity_index = 0.0
        
        for species, observations in self.species_data.items():
            proportion = len(observations) / total_count
            if proportion > 0:
                diversity_index -= proportion * np.log(proportion)
        
        return diversity_index
    
    async def assess_habitat_health(self, habitat_id: str, metrics: Dict[str, float]) -> str:
        """Assess habitat health based on various metrics"""
        health_score = 0.0
        max_score = 0.0
        
        # Simple scoring based on metrics
        for metric, value in metrics.items():
            max_score += 1.0
            if metric == "vegetation_coverage" and value > 0.7:
                health_score += 1.0
            elif metric == "water_quality" and 6.5 <= value <= 8.5:
                health_score += 1.0
            elif metric == "species_diversity" and value > 2.0:
                health_score += 1.0
        
        health_percentage = (health_score / max_score) * 100 if max_score > 0 else 0
        
        if health_percentage >= 80:
            status = "Excellent"
        elif health_percentage >= 60:
            status = "Good"
        elif health_percentage >= 40:
            status = "Fair"
        else:
            status = "Poor"
        
        self.habitat_health[habitat_id] = {
            "score": health_percentage,
            "status": status,
            "timestamp": datetime.now()
        }
        
        return status

# Example usage
async def main():
    # Initialize environmental monitor
    monitor = EnvironmentalMonitor()
    
    # Initialize biodiversity tracker
    bio_tracker = BiodiversityTracker()
    
    # Record some species observations
    await bio_tracker.record_species_observation("Pacific Salmon", {"lat": 37.7749, "lon": -122.4194}, 15)
    await bio_tracker.record_species_observation("Sea Otter", {"lat": 37.7749, "lon": -122.4194}, 3)
    await bio_tracker.record_species_observation("Harbor Seal", {"lat": 37.7749, "lon": -122.4194}, 7)
    
    # Calculate diversity
    diversity = await bio_tracker.calculate_diversity_index()
    print(f"Biodiversity Index: {diversity:.3f}")
    
    # Assess habitat health
    habitat_metrics = {
        "vegetation_coverage": 0.75,
        "water_quality": 7.2,
        "species_diversity": diversity
    }
    
    health_status = await bio_tracker.assess_habitat_health("HABITAT_001", habitat_metrics)
    print(f"Habitat Health: {health_status}")
    
    # Run environmental monitoring for 30 seconds
    await monitor.monitor_environment(30)

if __name__ == "__main__":
    asyncio.run(main())