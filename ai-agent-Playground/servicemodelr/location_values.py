import random

# Fixed location multiplier per ortId (deterministic, 100–1000)
LOCATION_VALUES: dict[int, int] = {
    ort_id: random.Random(ort_id).randint(100, 1000) for ort_id in range(1, 27)
}
