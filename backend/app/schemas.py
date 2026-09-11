"""Pydantic response schemas for the API.

Most endpoints return plain dicts serialised from the services layer; these
models document the key payloads in the OpenAPI schema.
"""

from pydantic import BaseModel, Field


class RegionOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    population: int
    population_density: float


class HealthCenterOut(BaseModel):
    id: int
    name: str
    region_id: int | None
    latitude: float
    longitude: float


class PredictionOut(BaseModel):
    region: str
    region_name: str
    observation_date: str
    prediction_date: str
    probability: float = Field(description="Predicted outbreak risk 0-1")
    probability_lr: float
    risk_category: str
    severity_band: str
    severity_score: float
    priority_score: float


class RouteRequest(BaseModel):
    start: str = Field(description="Region name or graph node id")
    goal: str = Field(description="Region name or graph node id")
    weight: str = Field("time", description="'time' or 'distance'")


class RouteOut(BaseModel):
    start_node: str
    goal_node: str
    dijkstra: dict
    astar: dict
    nodes: list[dict]
    weight: str