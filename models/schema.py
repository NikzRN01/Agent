from dataclasses import dataclass
from typing import List


@dataclass
class Recipe:
    id: str
    title: str
    ingredients: List[str]
    steps: List[str]
