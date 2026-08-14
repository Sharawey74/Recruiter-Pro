"use client";

import { useId, useMemo } from "react";
import { usePrefersReducedMotion } from "./primitives";

/**
 * The corpus, plotted where its jobs actually are.
 *
 * Two layers. The land is a stippled silhouette — a deliberately coarse,
 * stylised approximation, not cartography, which is why it is drawn as loose
 * dots rather than coastlines: dots read as "world" without implying a
 * precision the shape does not have. The nodes on top are the real thing,
 * placed at each country's real coordinates and sized by its real job count.
 *
 * Equirectangular projection, because it is the one where a lat/long pair maps
 * to x/y with two multiplications, and at this size a truer projection would
 * cost complexity nobody could see.
 */

const VIEW_W = 1000;
const VIEW_H = 500;

/** [lon, lat] rings. Coarse on purpose — see the note above. */
const CONTINENTS: [number, number][][] = [
  // North America
  [
    [-168, 65], [-158, 71], [-140, 70], [-125, 70], [-100, 72], [-80, 73],
    [-62, 68], [-55, 52], [-66, 45], [-70, 41], [-76, 35], [-81, 25],
    [-97, 26], [-107, 23], [-117, 32], [-125, 40], [-125, 49], [-137, 58],
    [-152, 60], [-168, 65],
  ],
  // South America
  [
    [-81, 8], [-70, 11], [-60, 10], [-50, 0], [-35, -5], [-38, -15],
    [-48, -25], [-58, -35], [-65, -45], [-72, -52], [-75, -45], [-70, -30],
    [-70, -18], [-78, -5], [-81, 8],
  ],
  // Africa
  [
    [-17, 15], [-5, 5], [9, 4], [12, -5], [13, -17], [18, -34], [27, -34],
    [33, -25], [40, -16], [42, -2], [51, 11], [43, 12], [35, 22], [32, 31],
    [20, 32], [10, 37], [-6, 36], [-16, 28], [-17, 15],
  ],
  // Europe
  [
    [-10, 36], [-9, 44], [-2, 49], [3, 51], [5, 53], [8, 55], [11, 58],
    [16, 62], [22, 66], [30, 70], [40, 67], [40, 55], [35, 48], [28, 45],
    [20, 42], [14, 45], [12, 38], [17, 39], [10, 44], [3, 43], [-3, 37],
    [-10, 36],
  ],
  // Asia
  [
    [40, 67], [60, 70], [80, 73], [105, 76], [130, 72], [150, 70], [160, 62],
    [155, 52], [142, 45], [135, 34], [122, 30], [110, 20], [100, 10], [95, 5],
    [80, 8], [72, 20], [68, 24], [60, 25], [52, 28], [44, 38], [35, 48],
    [40, 55], [40, 67],
  ],
  // Australia
  [
    [113, -22], [122, -18], [130, -12], [137, -12], [143, -11], [146, -18],
    [151, -25], [153, -29], [149, -37], [143, -39], [135, -35], [125, -33],
    [115, -34], [113, -22],
  ],
  // New Zealand
  [[166, -46], [172, -41], [175, -37], [178, -38], [174, -42], [169, -47], [166, -46]],
];

/** Every country in the corpus, at its approximate centroid. */
const COUNTRY_COORDS: Record<string, [number, number]> = {
  "United States": [-98.6, 39.8],
  "United Kingdom": [-2.0, 54.0],
  Netherlands: [5.3, 52.2],
  India: [78.0, 21.0],
  Germany: [10.4, 51.2],
  Poland: [19.1, 52.0],
  Spain: [-3.7, 40.2],
  Canada: [-106.3, 56.1],
  Australia: [133.8, -25.3],
  France: [2.2, 46.6],
  Egypt: [30.8, 26.8],
  "United Arab Emirates": [54.0, 24.0],
  Denmark: [10.0, 56.0],
  Switzerland: [8.2, 46.8],
  Sweden: [18.6, 60.1],
  "New Zealand": [174.0, -41.0],
  Singapore: [103.8, 1.35],
  Belgium: [4.5, 50.5],
  "Saudi Arabia": [45.0, 24.0],
  Portugal: [-8.2, 39.4],
  Ireland: [-8.2, 53.4],
  Czechia: [15.5, 49.8],
  Norway: [8.5, 60.5],
  Finland: [25.7, 61.9],
  Austria: [14.6, 47.5],
  Qatar: [51.2, 25.3],
  Italy: [12.6, 41.9],
};

function project(lon: number, lat: number): [number, number] {
  return [((lon + 180) / 360) * VIEW_W, ((90 - lat) / 180) * VIEW_H];
}

/** Ray casting. Used once, to decide which stipple dots fall on land. */
function inside(point: [number, number], polygon: [number, number][]): boolean {
  const [x, y] = point;
  let hit = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i]!;
    const [xj, yj] = polygon[j]!;
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) {
      hit = !hit;
    }
  }
  return hit;
}

export function WorldMap({
  countries,
  className,
}: {
  countries: { country: string; jobs: number }[];
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  // Gradient and filter ids must be unique per instance or a second map on the
  // page silently reuses the first one's definitions.
  const uid = useId().replace(/:/g, "");

  // The land stipple, computed once. 2.5-degree spacing is dense enough to
  // read as landmass and sparse enough to stay a few hundred nodes.
  const dots = useMemo(() => {
    const points: [number, number][] = [];
    for (let lat = 80; lat >= -58; lat -= 2.5) {
      for (let lon = -180; lon <= 180; lon += 2.5) {
        if (CONTINENTS.some((ring) => inside([lon, lat], ring))) {
          points.push(project(lon, lat));
        }
      }
    }
    return points;
  }, []);

  const busiest = countries[0]?.jobs ?? 1;
  const hub = COUNTRY_COORDS["United States"];

  const nodes = countries
    .map(({ country, jobs }) => {
      const coords = COUNTRY_COORDS[country];
      if (!coords) return null;
      const [x, y] = project(coords[0], coords[1]);
      return { country, jobs, x, y, weight: jobs / busiest };
    })
    .filter((n): n is NonNullable<typeof n> => n !== null);

  const [hubX, hubY] = hub ? project(hub[0], hub[1]) : [0, 0];

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      className={className}
      role="img"
      aria-label={`World map showing ${countries.length} markets, busiest ${countries[0]?.country ?? ""}`}
    >
      <defs>
        <radialGradient id={`${uid}-node`}>
          <stop offset="0%" stopColor="#d0bcff" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#d0bcff" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${uid}-arc`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#adc6ff" stopOpacity="0" />
          <stop offset="50%" stopColor="#adc6ff" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#d0bcff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Land */}
      <g fill="#3b4a63" opacity="0.55">
        {dots.map(([x, y], index) => (
          <circle key={index} cx={x} cy={y} r={1.15} />
        ))}
      </g>

      {/*
        Routes from the busiest market to the rest. A quadratic curve lifted
        perpendicular to the chord, so an arc between two points always bows
        the same way rather than flipping when the target crosses the hub.
      */}
      <g fill="none" stroke={`url(#${uid}-arc)`} strokeWidth="1.2">
        {nodes.slice(1, 9).map((node, index) => {
          const midX = (hubX + node.x) / 2;
          const midY = (hubY + node.y) / 2;
          const lift = Math.hypot(node.x - hubX, node.y - hubY) * 0.22;
          const path = `M ${hubX} ${hubY} Q ${midX} ${midY - lift} ${node.x} ${node.y}`;
          return (
            <g key={node.country}>
              <path d={path} />
              {!reduced && (
                <circle r="2.4" fill="#d0bcff">
                  <animateMotion
                    dur={`${3.2 + index * 0.35}s`}
                    repeatCount="indefinite"
                    path={path}
                    begin={`${index * 0.45}s`}
                  />
                  <animate
                    attributeName="opacity"
                    values="0;1;1;0"
                    dur={`${3.2 + index * 0.35}s`}
                    repeatCount="indefinite"
                    begin={`${index * 0.45}s`}
                  />
                </circle>
              )}
            </g>
          );
        })}
      </g>

      {/* Markets. Radius carries the job count, so the map is the chart. */}
      <g>
        {nodes.map((node, index) => {
          const radius = 2.6 + node.weight * 6;
          return (
            <g key={node.country}>
              <circle
                cx={node.x}
                cy={node.y}
                r={radius * 3.2}
                fill={`url(#${uid}-node)`}
                opacity="0.5"
              />
              {!reduced && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill="none"
                  stroke="#d0bcff"
                  strokeWidth="1"
                  style={{
                    transformOrigin: `${node.x}px ${node.y}px`,
                    animation: `landing-pulse-ring ${2.4 + (index % 5) * 0.4}s ease-out ${
                      index * 0.18
                    }s infinite`,
                  }}
                />
              )}
              <circle cx={node.x} cy={node.y} r={radius} fill="#e9ddff">
                <title>{`${node.country}: ${node.jobs} roles`}</title>
              </circle>
            </g>
          );
        })}
      </g>
    </svg>
  );
}
