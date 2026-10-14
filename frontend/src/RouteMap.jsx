
import { useEffect, useRef } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const token = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

const RISK_COLORS = {
  Low: "#22c55e",
  Moderate: "#eab308",
  High: "#f97316",
  Severe: "#ef4444",
  "No Travel": "#a855f7",
};

const RISK_LEVELS = ["Low", "Moderate", "High", "Severe", "No Travel"];

export default function RouteMap({
  routes = [],
  selectedRoute,
  onSelectRoute,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const loadedRef = useRef(false);
  const markersRef = useRef([]);
  const drawRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    if (!token) {
      console.error("Missing VITE_MAPBOX_ACCESS_TOKEN in frontend/.env");
      return;
    }

    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: [-73.5, 41.3],
      zoom: 6,
    });

    mapRef.current = map;
    map.addControl(new mapboxgl.NavigationControl(), "top-right");

    const handleLoad = () => {
      loadedRef.current = true;
      map.resize();
      drawRef.current?.();
    };

    map.on("load", handleLoad);

    map.on("error", (event) => {
      console.error("Mapbox error:", event.error);
    });

    return () => {
      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];
      loadedRef.current = false;
      drawRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    const drawRoutes = () => {
      if (!map || !loadedRef.current || !map.isStyleLoaded()) return;

      markersRef.current.forEach((marker) => marker.remove());
      markersRef.current = [];

      routes.forEach((route) => {
        const layerId = `route-line-${route.route_number}`;
        const sourceId = `route-${route.route_number}`;

        if (map.getLayer(layerId)) map.removeLayer(layerId);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      });

      const bounds = new mapboxgl.LngLatBounds();

      routes.forEach((route) => {
        const coordinates = route.geometry?.coordinates || [];
        const checkpoints = route.checkpoints || [];

        if (coordinates.length < 2) return;

        coordinates.forEach((coordinate) => bounds.extend(coordinate));

        const sourceId = `route-${route.route_number}`;
        const layerId = `route-line-${route.route_number}`;

        map.addSource(sourceId, {
          type: "geojson",
          data: {
            type: "Feature",
            properties: { routeNumber: route.route_number },
            geometry: {
              type: "LineString",
              coordinates,
            },
          },
        });

        const isSelected =
          selectedRoute == null ||
          route.route_number === selectedRoute;

        map.addLayer({
          id: layerId,
          type: "line",
          source: sourceId,
          paint: {
            "line-color": isSelected
              ? route.recommended
                ? "#66d9b2"
                : "#38bdf8"
              : "#64748b",
            "line-width":
              selectedRoute === route.route_number ? 5 : 3,
            "line-opacity": isSelected ? 0.95 : 0.45,
          },
        });

        if (!isSelected) return;

        checkpoints.forEach((point) => {
          const element = document.createElement("button");
          element.type = "button";
          element.setAttribute(
            "aria-label",
            `Mile ${point.mile}, risk ${point.overall_risk}`
          );
          element.title = `Mile ${point.mile}: ${point.overall_risk}`;
          element.style.cssText = `
            width: 15px;
            height: 15px;
            border: 2px solid white;
            border-radius: 50%;
            padding: 0;
            background: ${RISK_COLORS[point.overall_risk] || "#94a3b8"};
            cursor: pointer;
            box-shadow: 0 0 5px #0008;
          `;

          const popupContent = document.createElement("div");
          popupContent.style.color = "#172033";

          const heading = document.createElement("strong");
          heading.textContent = `Mile ${point.mile}`;
          popupContent.appendChild(heading);

          const details = [
            `Overall risk: ${point.overall_risk}`,
            `Wind: ${point.weather?.wind_mph ?? "N/A"} mph`,
            `Rain: ${point.weather?.rain_in_hr ?? "N/A"} in/hr`,
            `Snow: ${point.weather?.snow_in_hr ?? "N/A"} in/hr`,
            `Arrival: ${point.arrival_utc || "N/A"}`,
          ];

          details.forEach((detail) => {
            const line = document.createElement("div");
            line.textContent = detail;
            popupContent.appendChild(line);
          });

          const popup = new mapboxgl.Popup({ offset: 12 })
            .setDOMContent(popupContent);

          const marker = new mapboxgl.Marker({ element })
            .setLngLat([point.longitude, point.latitude])
            .setPopup(popup)
            .addTo(map);

          element.addEventListener("click", () => {
            onSelectRoute?.(route.route_number);
          });

          markersRef.current.push(marker);
        });
      });

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, {
          padding: 45,
          maxZoom: 9,
          duration: 500,
        });
      }
    };

    drawRef.current = drawRoutes;

    if (loadedRef.current && map?.isStyleLoaded()) {
      drawRoutes();
    }

    return () => {
      if (drawRef.current === drawRoutes) {
        drawRef.current = null;
      }
    };
  }, [routes, selectedRoute, onSelectRoute]);

  return (
    <div className="route-map-wrapper">
      <div
        ref={containerRef}
        className="route-map-canvas"
        aria-label="Map of routes and weather checkpoints"
      />

      <div className="risk-legend">
        <strong>Weather risk</strong>
        {RISK_LEVELS.map((level) => (
          <span key={level} className="risk-legend-item">
            <i
              className="risk-legend-dot"
              style={{ backgroundColor: RISK_COLORS[level] }}
            />
            {level}
          </span>
        ))}
      </div>
    </div>
  );
}
