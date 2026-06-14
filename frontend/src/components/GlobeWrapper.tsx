"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import type { SatelliteTrack } from "@/utils/mosip-data";
import * as THREE from "three";

const Globe = dynamic(() => import("react-globe.gl"), {
  ssr: false,
  loading: () => (
    <div
      className="grid h-full min-h-[420px] place-items-center"
      style={{
        background: "var(--c-surface-0)",
        border: "1px solid var(--c-border)",
        borderRadius: "var(--border-r)",
      }}
    >
      <div className="flex flex-col items-center gap-3">
        <div className="relative h-12 w-12">
          <div
            className="absolute inset-0 rounded-full"
            style={{
              border: "1px solid rgba(77,217,245,0.2)",
              animation: "atmosphere-pulse 2s ease-in-out infinite",
            }}
          />
          <div
            className="absolute inset-2 rounded-full"
            style={{
              border: "1px solid rgba(77,217,245,0.4)",
              animation: "atmosphere-pulse 2s ease-in-out infinite 0.5s",
            }}
          />
          <div className="absolute inset-0 grid place-items-center">
            <div
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: "var(--c-cyan)", boxShadow: "0 0 6px var(--c-cyan)" }}
            />
          </div>
        </div>
        <span
          className="font-data text-[8px] uppercase tracking-[0.35em]"
          style={{ color: "var(--c-cyan-dim)" }}
        >
          ACQUIRING ORBITAL DATA
        </span>
      </div>
    </div>
  ),
});

type GlobeWrapperProps = {
  satellites: SatelliteTrack[];
  selectedId: number;
  onSelect: (satellite: SatelliteTrack) => void;
  orbitPath?: { lat: number; lng: number }[];
};

/* ── ISS Propagation & Orbit Path Generation ────────────────────────────── */
function propagateIss(timeMs: number) {
  const alt = 420; // altitude km
  const inclinationDeg = 51.64; // real ISS inclination
  const inclinationRad = (inclinationDeg * Math.PI) / 180;
  const raanDeg = 125;
  const raanRad = (raanDeg * Math.PI) / 180;
  const R_earth = 6371;
  const GM = 3.986004418e5;
  const a = R_earth + alt;
  const periodSec = 2 * Math.PI * Math.sqrt(Math.pow(a, 3) / GM);
  const periodMs = periodSec * 1000;
  
  // Speed up rotation to make it visible
  const timeSpeedup = 150;
  const phase = ((timeMs * timeSpeedup) / periodMs) * 2 * Math.PI;

  const x_orbit = a * Math.cos(phase);
  const y_orbit = a * Math.sin(phase);

  const x_eci = x_orbit * Math.cos(raanRad) - y_orbit * Math.sin(raanRad) * Math.cos(inclinationRad);
  const y_eci = x_orbit * Math.sin(raanRad) + y_orbit * Math.cos(raanRad) * Math.cos(inclinationRad);
  const z_eci = y_orbit * Math.sin(inclinationRad);

  const r = Math.sqrt(x_eci * x_eci + y_eci * y_eci + z_eci * z_eci);
  const lat = (Math.asin(z_eci / r) * 180) / Math.PI;
  let lng = (Math.atan2(y_eci, x_eci) * 180) / Math.PI;

  const earthRotationSpeed = 360 / (86164 * 1000);
  const rotationAngle = (timeMs * timeSpeedup * earthRotationSpeed) % 360;
  lng = ((lng - rotationAngle + 180) % 360) - 180;
  if (lng < -180) lng += 360;

  // Altitude mapped to globe units (0.18 is very clean and visible)
  return { lat, lng, alt: 0.18 };
}

function generateIssOrbitPath() {
  const alt = 420;
  const inclinationDeg = 51.64;
  const inclinationRad = (inclinationDeg * Math.PI) / 180;
  const raanDeg = 125;
  const raanRad = (raanDeg * Math.PI) / 180;
  const R_earth = 6371;
  const a = R_earth + alt;

  const points = [];
  const numPoints = 120;
  for (let i = 0; i <= numPoints; i++) {
    const phase = (i / numPoints) * 2 * Math.PI;
    const x_orbit = a * Math.cos(phase);
    const y_orbit = a * Math.sin(phase);

    const x_eci = x_orbit * Math.cos(raanRad) - y_orbit * Math.sin(raanRad) * Math.cos(inclinationRad);
    const y_eci = x_orbit * Math.sin(raanRad) + y_orbit * Math.cos(raanRad) * Math.cos(inclinationRad);
    const z_eci = y_orbit * Math.sin(inclinationRad);

    const r = Math.sqrt(x_eci * x_eci + y_eci * y_eci + z_eci * z_eci);
    const lat = (Math.asin(z_eci / r) * 180) / Math.PI;
    const lng = (Math.atan2(y_eci, x_eci) * 180) / Math.PI;

    points.push({ lat, lng });
  }
  return points;
}

export function GlobeWrapper({ satellites, selectedId, onSelect, orbitPath }: GlobeWrapperProps) {
  const globeRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [dataAge, setDataAge] = useState(0);
  const [localTime, setLocalTime] = useState(0);
  const moonRef = useRef<THREE.Mesh | null>(null);

  // Local ticker for ISS & Moon propagation
  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setLocalTime(Date.now() - start);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  // Data freshness ticker
  useEffect(() => {
    setDataAge(0);
    const id = setInterval(() => setDataAge((p) => p + 1), 1000);
    return () => clearInterval(id);
  }, [satellites.length]);

  const arcs = useMemo(
    () =>
      satellites.map((s, i) => ({
        ...s,
        startLat: s.lat,
        startLng: s.lng,
        endLat: s.lat * -0.72,
        endLng: s.lng + 110 - i * 18,
      })),
    [satellites],
  );

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setDimensions({
          width: entry.contentRect.width || 800,
          height: entry.contentRect.height || 600,
        });
      }
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Initialize Moon & Custom Sun/Directional Lights in Three.js
  useEffect(() => {
    if (!globeRef.current) return;
    const scene = globeRef.current.scene();
    if (!scene) return;

    // Create 3D Moon sphere
    // Earth radius is 100 in react-globe.gl, so moon radius of 8 looks nicely balanced in space
    const moonRadius = 8;
    const moonGeom = new THREE.SphereGeometry(moonRadius, 32, 32);
    
    // Load Moon texture from standard unpkg CDN
    const textureLoader = new THREE.TextureLoader();
    const moonTexture = textureLoader.load("//unpkg.com/three-globe/example/img/moon.jpg");
    const moonMat = new THREE.MeshStandardMaterial({
      map: moonTexture,
      roughness: 0.9,
      metalness: 0.1,
    });
    
    const moon = new THREE.Mesh(moonGeom, moonMat);
    scene.add(moon);
    moonRef.current = moon;

    // Fixed Sun directional light for dramatic shadows and atmospheric contrast
    const sunLight = new THREE.DirectionalLight(0xffffff, 2.5);
    sunLight.position.set(-180, 120, 180);
    scene.add(sunLight);

    // Strong backlit Sun light source behind the Earth for high-contrast rim lighting
    const sunBackLight = new THREE.DirectionalLight(0xfff5db, 3.5);
    sunBackLight.position.set(-100, 50, -250);
    scene.add(sunBackLight);

    // Deep space ambient fill (soft blue-gray shadows)
    const ambientLight = new THREE.AmbientLight(0x0c1322, 0.85);
    scene.add(ambientLight);

    // Inner sunlight corona glow (warm gold-white, radius of Earth is 100)
    const glowGeom1 = new THREE.SphereGeometry(101.5, 32, 32);
    const glowMat1 = new THREE.MeshBasicMaterial({
      color: 0xfff3d1,
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
    });
    const glowMesh1 = new THREE.Mesh(glowGeom1, glowMat1);
    scene.add(glowMesh1);

    // Outer atmospheric halo glow (cyan theme)
    const glowGeom2 = new THREE.SphereGeometry(104.5, 32, 32);
    const glowMat2 = new THREE.MeshBasicMaterial({
      color: 0x4dd9f5,
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
    });
    const glowMesh2 = new THREE.Mesh(glowGeom2, glowMat2);
    scene.add(glowMesh2);

    return () => {
      if (moonRef.current) scene.remove(moonRef.current);
      scene.remove(sunLight);
      scene.remove(sunBackLight);
      scene.remove(ambientLight);
      scene.remove(glowMesh1);
      scene.remove(glowMesh2);
    };
  }, []);

  // Update Moon Orbit & axial rotation
  useEffect(() => {
    if (moonRef.current) {
      const orbitRadius = 165; // Orbiting comfortably in outer frame
      const orbitSpeed = 0.00015; // Slow ambient orbit
      const angle = localTime * orbitSpeed;

      const x = orbitRadius * Math.cos(angle);
      const z = orbitRadius * Math.sin(angle);
      const y = 35 * Math.sin(angle); // Slight orbital tilt

      moonRef.current.position.set(x, y, z);
      moonRef.current.rotation.y = localTime * 0.0001; // slow rotation
    }
  }, [localTime]);

  useEffect(() => {
    const controls = globeRef.current?.controls?.();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.15; // Slow, ambient rotation
      controls.enableZoom = false; // Disable scroll-zooming so mouse wheel scrolls the page normally
      controls.minDistance = 150;
      controls.maxDistance = 500;
    }
  }, []);

  useEffect(() => {
    const sel = satellites.find((s) => s.id === selectedId);
    if (sel) {
      globeRef.current?.pointOfView?.(
        { lat: sel.lat, lng: sel.lng, altitude: 1.85 },
        1100,
      );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  // ISS Position
  const issPosition = useMemo(() => {
    const pos = propagateIss(localTime);
    return [
      {
        id: "ISS",
        name: "International Space Station",
        lat: pos.lat,
        lng: pos.lng,
        alt: pos.alt,
        isIss: true,
      },
    ];
  }, [localTime]);

  // ISS 3D Model Instance
  const issGroup = useMemo(() => {
    const group = new THREE.Group();

    // Main structural truss
    const trussGeom = new THREE.CylinderGeometry(0.06, 0.06, 3.2, 8);
    const trussMat = new THREE.MeshStandardMaterial({ 
      color: 0x8899a6, 
      metalness: 0.8, 
      roughness: 0.3 
    });
    const truss = new THREE.Mesh(trussGeom, trussMat);
    truss.rotation.z = Math.PI / 2;
    group.add(truss);
    
    // Central pressurized modules
    const moduleMat = new THREE.MeshStandardMaterial({ 
      color: 0xe0e8f0, 
      metalness: 0.5, 
      roughness: 0.2 
    });
    
    const coreGeom = new THREE.CylinderGeometry(0.16, 0.16, 1.0, 12);
    const core = new THREE.Mesh(coreGeom, moduleMat);
    core.rotation.x = Math.PI / 2;
    group.add(core);

    const nodeGeom = new THREE.CylinderGeometry(0.12, 0.12, 0.6, 10);
    const node1 = new THREE.Mesh(nodeGeom, moduleMat);
    node1.position.set(0, 0, 0.28);
    group.add(node1);

    const node2 = new THREE.Mesh(nodeGeom, moduleMat);
    node2.position.set(0, 0, -0.28);
    group.add(node2);

    // Solar panels
    const panelGeom = new THREE.BoxGeometry(0.28, 0.01, 1.1);
    const panelMat = new THREE.MeshStandardMaterial({ 
      color: 0x00a2ff, 
      emissive: 0x002d66,
      metalness: 0.9, 
      roughness: 0.1 
    });

    const offsets = [-1.3, -0.8, 0.8, 1.3];
    offsets.forEach((offsetX) => {
      const p1 = new THREE.Mesh(panelGeom, panelMat);
      p1.position.set(offsetX, 0.38, 0.1);
      p1.rotation.y = 0.12;
      group.add(p1);

      const p2 = new THREE.Mesh(panelGeom, panelMat);
      p2.position.set(offsetX, -0.38, 0.1);
      p2.rotation.y = 0.12;
      group.add(p2);
    });

    // Radiators
    const radiatorGeom = new THREE.BoxGeometry(0.16, 0.008, 0.65);
    const radiatorMat = new THREE.MeshStandardMaterial({ 
      color: 0xffffff, 
      metalness: 0.1, 
      roughness: 0.7 
    });
    
    const rad1 = new THREE.Mesh(radiatorGeom, radiatorMat);
    rad1.position.set(-0.3, 0, 0.4);
    rad1.rotation.y = Math.PI / 4;
    group.add(rad1);

    const rad2 = new THREE.Mesh(radiatorGeom, radiatorMat);
    rad2.position.set(0.3, 0, -0.4);
    rad2.rotation.y = -Math.PI / 4;
    group.add(rad2);

    // Scale up ISS for visibility
    group.scale.set(6.5, 6.5, 6.5);

    return group;
  }, []);

  // Slowly spin the ISS
  useEffect(() => {
    if (issGroup) {
      issGroup.rotation.y = (localTime * 0.0006) % (Math.PI * 2);
    }
  }, [localTime, issGroup]);

  const getIssModel = useCallback(() => {
    return issGroup;
  }, [issGroup]);

  // ISS Orbit Path
  const issOrbitPath = useMemo(() => generateIssOrbitPath(), []);

  // Combine ISS path and selected satellite path
  const allPaths = useMemo(() => {
    const list: any[] = [];
    list.push({
      points: issOrbitPath,
      isIss: true,
    });
    if (orbitPath) {
      list.push({
        points: orbitPath,
        isIss: false,
      });
    }
    return list;
  }, [orbitPath, issOrbitPath]);

  const formatAge = (s: number) => {
    if (s < 60) return `${s}s`;
    return `${Math.floor(s / 60)}m ${s % 60}s`;
  };

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden" style={{ minHeight: 420 }}>
      {/* Deep space glow */}
      <div
        className="atmosphere-pulse absolute inset-0 pointer-events-none z-10"
        style={{
          background: "radial-gradient(circle at 50% 52%, rgba(77,217,245,0.065) 0%, transparent 52%)",
        }}
      />

      <Globe
        ref={globeRef}
        backgroundColor="rgba(0,0,0,0)"
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        showAtmosphere
        atmosphereColor="#4dd9f5"
        atmosphereAltitude={0.15}
        
        /* Satellites Points Layer */
        pointsData={satellites}
        pointLat="lat"
        pointLng="lng"
        pointAltitude={(s: object) => {
          const sat = s as SatelliteTrack;
          return sat.orbit === "GEO" ? 0.44 : sat.orbit === "MEO" ? 0.28 : 0.16;
        }}
        pointRadius={(s: object) => {
          const sat = s as SatelliteTrack;
          return sat.id === selectedId ? 0.55 : 0.22;
        }}
        pointColor={(s: object) => {
          const sat = s as SatelliteTrack;
          if (sat.id === selectedId) return "#ffffff";
          if (sat.risk >= 75) return "#ef4343";
          if (sat.risk >= 55) return "#f5a623";
          return "#4dd9f5";
        }}
        pointsTransitionDuration={700}
        onPointClick={(s: object) => onSelect(s as SatelliteTrack)}

        /* Satellite Arc Traces */
        arcsData={arcs}
        arcStartLat="startLat"
        arcStartLng="startLng"
        arcEndLat="endLat"
        arcEndLng="endLng"
        arcAltitude={(s: object) => {
          const sat = s as SatelliteTrack;
          return sat.orbit === "GEO" ? 0.5 : 0.2;
        }}
        arcStroke={0.35}
        arcDashLength={0.45}
        arcDashGap={2.5}
        arcDashAnimateTime={5000}
        arcColor={(s: object) => {
          const sat = s as SatelliteTrack;
          return sat.id === selectedId
            ? ["rgba(77,217,245,0.9)", "rgba(255,255,255,0.2)"]
            : ["rgba(77,217,245,0.08)", "rgba(8,12,18,0)"];
        }}

        /* ISS custom object layer */
        objectsData={issPosition}
        objectLat="lat"
        objectLng="lng"
        objectAltitude="alt"
        objectThreeObject={getIssModel}

        /* Combined Orbit Paths (ISS + Selected Sat) */
        pathsData={allPaths}
        pathPoints={(d: any) => d.points}
        pathPointLat="lat"
        pathPointLng="lng"
        pathColor={(d: any) => d.isIss ? "rgba(245,166,35,0.55)" : "rgba(77,217,245,0.45)"}
        pathStroke={(d: any) => d.isIss ? 1.5 : 1.0}
        pathDashLength={(d: any) => d.isIss ? 0.08 : 0.05}
        pathDashGap={(d: any) => d.isIss ? 0.04 : 0.025}
        pathDashAnimateTime={(d: any) => d.isIss ? 12000 : 18000}

        width={dimensions.width}
        height={dimensions.height}
      />

      {/* ── HUD Overlay — top ──────────────────────────────────────────────────── */}
      <div
        className="pointer-events-none absolute inset-x-4 top-3 flex items-center justify-between z-20"
        style={{ fontFamily: "JetBrains Mono, monospace" }}
      >
        <span
          className="text-[8px] uppercase tracking-[0.3em]"
          style={{ color: "rgba(77,217,245,0.35)" }}
        >
          THREE.JS / ORBITAL MISSION SCENE
        </span>
        <div className="flex items-center gap-2">
          <span
            className="text-[8px] uppercase tracking-[0.25em]"
            style={{ color: "rgba(77,217,245,0.3)" }}
          >
            ORBITAL DATA — UPDATED {formatAge(dataAge)} AGO
          </span>
          <span className="pulse-dot" style={{ background: "var(--c-nominal)" }} />
        </div>
      </div>

      {/* ── HUD Overlay — bottom left: orbit legend ────────────────────────────── */}
      <div
        className="pointer-events-none absolute bottom-3 left-4 z-20 flex items-center gap-3"
        style={{ fontFamily: "JetBrains Mono, monospace" }}
      >
        {[
          { label: "LEO", color: "#4dd9f5" },
          { label: "MEO", color: "#f5a623" },
          { label: "GEO", color: "#3de89b" },
          { label: "ISS (LEO)", color: "#f5a623", isIss: true },
          { label: "MOON (LUNAR)", color: "#ffffff", isIss: true }
        ].map((regime) => (
          <div key={regime.label} className="flex items-center gap-1">
            <div
              className="h-1.5 w-1.5 rounded-full"
              style={{ background: regime.color, opacity: regime.isIss ? 1.0 : 0.7 }}
            />
            <span
              className="text-[7px] uppercase tracking-widest"
              style={{ color: regime.isIss ? "var(--c-elevated)" : "rgba(255,255,255,0.25)" }}
            >
              {regime.label}
            </span>
          </div>
        ))}
      </div>

      {/* ── Corner targeting reticles ──────────────────────────────────────────── */}
      {[
        { top: 8, left: 8 },
        { top: 8, right: 8 },
        { bottom: 8, left: 8 },
        { bottom: 8, right: 8 },
      ].map((pos, i) => (
        <div
          key={i}
          className="pointer-events-none absolute z-20"
          style={{
            ...pos,
            width: 14,
            height: 14,
            borderTop: i < 2 ? "1px solid rgba(77,217,245,0.2)" : "none",
            borderBottom: i >= 2 ? "1px solid rgba(77,217,245,0.2)" : "none",
            borderLeft: i % 2 === 0 ? "1px solid rgba(77,217,245,0.2)" : "none",
            borderRight: i % 2 === 1 ? "1px solid rgba(77,217,245,0.2)" : "none",
          }}
        />
      ))}
    </div>
  );
}
