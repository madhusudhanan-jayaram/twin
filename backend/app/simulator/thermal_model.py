"""Spoilage prediction using linear extrapolation + cumulative exposure."""

from app.config import settings

# Skyrizi must stay between 2-8°C
SAFE_MIN = 2.0
SAFE_MAX = 8.0
CRITICAL_TEMP = settings.critical_temperature_celsius  # 8.0

# After cumulative exposure of this many degree-hours above threshold, product is compromised
MAX_CUMULATIVE_EXPOSURE_DEGREE_HOURS = 20.0


def predict_spoilage_hours(
    current_temp: float,
    temp_rise_rate_per_hour: float,
    cumulative_exposure_dh: float,
) -> float | None:
    """Predict hours until spoilage based on current trajectory.

    Returns None if temperature is normal and not rising.
    """
    if current_temp <= settings.temperature_threshold_celsius and temp_rise_rate_per_hour <= 0.05:
        return None

    if temp_rise_rate_per_hour <= 0.01:
        # Temperature elevated but stable — use cumulative exposure
        if current_temp > SAFE_MAX:
            excess = current_temp - SAFE_MAX
            remaining_dh = MAX_CUMULATIVE_EXPOSURE_DEGREE_HOURS - cumulative_exposure_dh
            if excess > 0 and remaining_dh > 0:
                return remaining_dh / excess
        return None

    # Linear extrapolation: how long until cumulative exposure limit is reached
    excess_now = max(0, current_temp - SAFE_MAX)
    remaining_dh = MAX_CUMULATIVE_EXPOSURE_DEGREE_HOURS - cumulative_exposure_dh

    if remaining_dh <= 0:
        return 0.0

    # Integrate: area under (temp - SAFE_MAX) over time
    # temp(t) = current_temp + rate * t
    # excess(t) = max(0, current_temp + rate * t - SAFE_MAX)
    # If already above, excess = excess_now + rate * t
    # Cumulative = excess_now * t + 0.5 * rate * t^2 = remaining_dh
    # 0.5 * rate * t^2 + excess_now * t - remaining_dh = 0

    a = 0.5 * temp_rise_rate_per_hour
    b = excess_now
    c = -remaining_dh

    if a == 0:
        if b > 0:
            return remaining_dh / b
        return None

    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return None

    t = (-b + discriminant ** 0.5) / (2 * a)
    return max(0.0, t)


def compute_cumulative_exposure(readings_temps: list[float], interval_hours: float) -> float:
    """Compute cumulative degree-hours above safe max."""
    total = 0.0
    for temp in readings_temps:
        if temp > SAFE_MAX:
            total += (temp - SAFE_MAX) * interval_hours
    return total
