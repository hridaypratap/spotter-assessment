
import { useMemo, useState } from "react";
import RouteMap from "./RouteMap";
import "./App.css";


const API_URL = "https://spotter-weather-routing-api-q1as.onrender.com/api/analyze/";


function App() {
  const [origin, setOrigin] = useState("New York, USA");
  const [destination, setDestination] = useState("Boston, USA");
  const [departureTime, setDepartureTime] = useState("2026-10-14T12:00");
  const [loadLb, setLoadLb] = useState("25000");
  const [intervalMiles, setIntervalMiles] = useState("25");

  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [forecastHour, setForecastHour] = useState(0);

  async function handleSubmit(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setRoutes([]);
    setSelectedRoute(null);
    setForecastHour(0);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          origin,
          destination,
          departure_time: new Date(departureTime).toISOString(),
          load_lb: Number(loadLb),
          interval_miles: Number(intervalMiles),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Route analysis failed.");
      }

      setRoutes(data.routes || []);

      if (!data.routes?.length) {
        setError("No routes were returned. Try different locations.");
      }
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot reach the backend. Ensure Django is running on port 8000 and CORS allows localhost:5173."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  const displayedRoutes = useMemo(() => {
    const departureMs = new Date(departureTime).getTime();

    if (!Number.isFinite(departureMs)) {
      return routes;
    }

    const targetMs =
      departureMs + forecastHour * 60 * 60 * 1000;

    const forecastEndMs =
      departureMs + 48 * 60 * 60 * 1000;

    return routes.map((route) => ({
      ...route,
      checkpoints: (route.checkpoints || []).map((point) => {
        const forecast = point.hourly_forecast || [];

        const validForecasts = forecast.filter((item) => {
          const timeMs = new Date(item.time).getTime();

          return (
            Number.isFinite(timeMs) &&
            timeMs >= departureMs &&
            timeMs <= forecastEndMs
          );
        });

        const matchingForecast = validForecasts.reduce(
          (best, item) => {
            if (!best) return item;

            const itemDistance = Math.abs(
              new Date(item.time).getTime() - targetMs
            );

            const bestDistance = Math.abs(
              new Date(best.time).getTime() - targetMs
            );

            return itemDistance < bestDistance ? item : best;
          },
          null
        );

        // Temporary debugging: verify selected forecast time and risk.
        console.log("Selected weather:", {
  hour: forecastHour,
  mile: point.mile,
  time: matchingForecast?.time,
  weather: matchingForecast?.weather,
  windRisk: matchingForecast?.wind_risk,
  rainRisk: matchingForecast?.rain_risk,
  snowRisk: matchingForecast?.snow_risk,
  overallRisk: matchingForecast?.overall_risk,
});

        if (!matchingForecast) {
          return {
            ...point,
            forecast_unavailable: true,
            forecast_time: null,
          };
        }

        return {
          ...point,
          weather: matchingForecast.weather,
          wind_risk: matchingForecast.wind_risk,
          rain_risk: matchingForecast.rain_risk,
          snow_risk: matchingForecast.snow_risk,
          overall_risk: matchingForecast.overall_risk,
          forecast_time: matchingForecast.time,
          forecast_unavailable: false,
        };
      }),
    }));
  }, [routes, departureTime, forecastHour]);

  const selectedRouteData = displayedRoutes.find(
    (route) => route.route_number === selectedRoute
  );

  function getDynamicRiskSummary(route) {
    const counts = {
      low_checkpoints: 0,
      moderate_checkpoints: 0,
      high_checkpoints: 0,
      severe_checkpoints: 0,
      no_travel_checkpoints: 0,
      unavailable_checkpoints: 0,
    };

    (route.checkpoints || []).forEach((point) => {
      if (point.forecast_unavailable) {
        counts.unavailable_checkpoints++;
        return;
      }

      const key = {
        Low: "low_checkpoints",
        Moderate: "moderate_checkpoints",
        High: "high_checkpoints",
        Severe: "severe_checkpoints",
        "No Travel": "no_travel_checkpoints",
      }[point.overall_risk];

      if (key) {
        counts[key]++;
      }
    });

    return counts;
  }

  return (
    <main className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">SPOTTER · LOGISTICS INTELLIGENCE</p>
          <h1>Weather-Aware Routing</h1>
          <p className="subtitle">
            Compare truck routes using forecast weather and driving risk.
          </p>
        </div>

        <span className="status">● ROUTE PLANNER</span>
      </header>

      <section className="planner">
        <h2>Plan your journey</h2>

        <form onSubmit={handleSubmit}>
          <label>
            Origin
            <input
              value={origin}
              onChange={(event) => setOrigin(event.target.value)}
              required
            />
          </label>

          <label>
            Destination
            <input
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              required
            />
          </label>

          <label>
            Departure time
            <input
              type="datetime-local"
              value={departureTime}
              onChange={(event) => setDepartureTime(event.target.value)}
              required
            />
          </label>

          <label>
            Load weight (lb)
            <input
              type="number"
              min="1"
              value={loadLb}
              onChange={(event) => setLoadLb(event.target.value)}
              required
            />
          </label>

          <label>
            Checkpoint interval
            <select
              value={intervalMiles}
              onChange={(event) => setIntervalMiles(event.target.value)}
            >
              <option value="10">Every 10 miles</option>
              <option value="25">Every 25 miles</option>
              <option value="50">Every 50 miles</option>
            </select>
          </label>

          <button type="submit" disabled={loading}>
            {loading ? "Analyzing routes..." : "Analyze routes →"}
          </button>
        </form>

        {error && <p className="error-message">{error}</p>}
      </section>

      {routes.length > 0 && (
        <section className="forecast-controls">
          <div className="forecast-heading">
            <div>
              <h2>Weather forecast timeline</h2>
              <p className="muted">
                View checkpoint risks at different hours after departure.
              </p>
            </div>

            <strong>
              {forecastHour === 0
                ? "Departure"
                : `+${forecastHour} hours`}
            </strong>
          </div>

          <input
            className="forecast-slider"
            type="range"
            min="0"
            max="48"
            step="1"
            value={forecastHour}
            onChange={(event) =>
              setForecastHour(Number(event.target.value))
            }
            aria-label="Forecast hours after departure"
          />

          <div className="slider-labels">
            <span>0h</span>
            <span>12h</span>
            <span>24h</span>
            <span>36h</span>
            <span>48h</span>
          </div>

          {selectedRouteData && (
            <p className="forecast-summary">
              Route {selectedRouteData.route_number} ·{" "}
              {selectedRouteData.checkpoints.length} checkpoints · Forecast
              hour {forecastHour}
            </p>
          )}
        </section>
      )}

      <section className="workspace">
        <div className="map-container">
          <RouteMap
            routes={displayedRoutes}
            selectedRoute={selectedRoute}
            onSelectRoute={setSelectedRoute}
          />
        </div>

        <aside className="route-panel">
          <h2>Route comparison</h2>
          <p className="muted">
            {routes.length
              ? `${routes.length} route(s) returned by the routing service.`
              : "Run an analysis to compare available routes."}
          </p>

          {routes.length === 0 ? (
            <div className="empty-state">
              <span>↗</span>
              <p>No routes analyzed yet</p>
            </div>
          ) : (
            <div className="route-list">
              {displayedRoutes.map((route) => {
                const summary = getDynamicRiskSummary(route);

                return (
                  <article
                    className={`route-card ${
                      route.recommended ? "recommended" : ""
                    } ${
                      selectedRoute === route.route_number
                        ? "selected"
                        : ""
                    }`}
                    key={route.route_number}
                    onClick={() => setSelectedRoute(route.route_number)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        setSelectedRoute(route.route_number);
                      }
                    }}
                  >
                    <div className="route-card-header">
                      <h3>Route {route.route_number}</h3>

                      {route.recommended && (
                        <span className="recommended-badge">
                          Recommended
                        </span>
                      )}
                    </div>

                    <div className="route-stats">
                      <div>
                        <strong>{route.distance_miles} mi</strong>
                        <span>Distance</span>
                      </div>

                      <div>
                        <strong>{route.duration_hours} h</strong>
                        <span>Driving time</span>
                      </div>
                    </div>

                    <div className="risk-summary">
                      <span>Low: {summary.low_checkpoints}</span>
                      <span>Moderate: {summary.moderate_checkpoints}</span>
                      <span>High: {summary.high_checkpoints}</span>
                      <span>Severe: {summary.severe_checkpoints}</span>
                      <span>No Travel: {summary.no_travel_checkpoints}</span>

                      {summary.unavailable_checkpoints > 0 && (
                        <span>
                          Unavailable: {summary.unavailable_checkpoints}
                        </span>
                      )}
                    </div>

                    <p className="checkpoint-count">
                      {route.checkpoints?.length ?? 0} weather checkpoints
                    </p>
                  </article>
                );
              })}
            </div>
          )}
        </aside>
      </section>
    </main>
  );
}

export default App;

