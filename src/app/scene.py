"""3D Illustration Renderer for Trucks and Packages using Plotly.

Renders:
- Container cargo bed with semi-transparent walls and wireframe frame.
- Cabin, chassis, bumpers, headlights, and wheels for each truck.
- Support for multiple trucks arranged side-by-side.
- 3D boxes placed inside containers with orientations, colors, and crisp edge lines.
- Unpacked boxes staging ground behind/next to the trucks.
- Fragile item visual indicators.
- Interactive hover tooltips.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pcolors

from src.core.models import Package, Truck, Placement


# Cube mesh rendering
def _cuboid_mesh(x0: float, y0: float, z0: float,
                 dx: float, dy: float, dz: float,
                 color: str, name: str, opacity: float = 0.85,
                 hovertext: str = "") -> go.Mesh3d:
    """Generate a go.Mesh3d for a cuboid."""
    # 8 vertices
    x = [x0, x0 + dx, x0 + dx, x0, x0, x0 + dx, x0 + dx, x0]
    y = [y0, y0, y0 + dy, y0 + dy, y0, y0, y0 + dy, y0 + dy]
    z = [z0, z0, z0, z0, z0 + dz, z0 + dz, z0 + dz, z0 + dz]
    
    # 12 triangles (2 per face * 6 faces)
    i = [0, 0, 4, 4, 0, 0, 2, 2, 0, 0, 1, 1]
    j = [1, 2, 5, 6, 1, 5, 3, 7, 3, 7, 2, 6]
    k = [2, 3, 6, 7, 5, 4, 7, 6, 7, 4, 6, 5]
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        name=name,
        flatshading=True,
        hoverinfo="text" if hovertext else "none",
        hovertext=hovertext,
        showlegend=False,
    )


# Cube edge rendering
def _cuboid_edges(x0: float, y0: float, z0: float,
                  dx: float, dy: float, dz: float,
                  color: str = "black", width: int = 2) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    # Vertices
    v = [
        (x0, y0, z0),              # 0
        (x0 + dx, y0, z0),         # 1
        (x0 + dx, y0 + dy, z0),    # 2
        (x0, y0 + dy, z0),         # 3
        (x0, y0, z0 + dz),         # 4
        (x0 + dx, y0, z0 + dz),    # 5
        (x0 + dx, y0 + dy, z0 + dz),# 6
        (x0, y0 + dy, z0 + dz),    # 7
    ]
    
    # Edge sequences with None separators for a single Scatter3d trace
    seq = [
        0, 1, 2, 3, 0,  # bottom loop
        4, 5, 6, 7, 4,  # top loop
        None, 1, 5, None, 2, 6, None, 3, 7  # vertical pillars
    ]
    
    xs, ys, zs = [], [], []
    for idx in seq:
        if idx is None:
            xs.append(None)
            ys.append(None)
            zs.append(None)
        else:
            xs.append(v[idx][0])
            ys.append(v[idx][1])
            zs.append(v[idx][2])
            
    return xs, ys, zs


# Random color generation
def _get_package_color(idx: int, total: int, is_fragile: bool) -> str:
    palette = pcolors.qualitative.Plotly + pcolors.qualitative.Dark24 + pcolors.qualitative.Bold
    base_color = palette[idx % len(palette)]
    return base_color


# Render 3d scene of trucks and packages, using the plotly.go library
def render_scene_3d(trucks: List[Truck],
                    packages: List[Package],
                    placements: Dict[str, Placement],
                    step_info: Optional[Dict[str, Any]] = None,
                    camera: Optional[Dict[str, Any]] = None) -> go.Figure:

    fig = go.Figure()
    
    if not trucks:
        trucks = [Truck(id="Truck_1", w=10.0, l=20.0, h=5.0, max_capacity=500.0)]
        
    pkg_map = {p.id: p for p in packages}
    truck_spacing = 6.0
    
    # Calculate Y-offsets for each truck
    current_y_offset = 0.0
    truck_offsets: Dict[int, float] = {}
    for i, t in enumerate(trucks):
        truck_offsets[i] = current_y_offset
        current_y_offset += (t.w + truck_spacing)
        
    total_fleet_width = current_y_offset - truck_spacing
    max_truck_length = max(t.l for t in trucks)
    max_truck_height = max(t.h for t in trucks)
    
    wheel_radius = 0.8
    ground_z = -wheel_radius * 2
    
    # --------------------------------------------------------------------------
    # 1. GROUND PLANE (Asphalt Road)
    # --------------------------------------------------------------------------
    road_x_min = -10.0
    road_x_max = max_truck_length + 20.0
    road_y_min = -5.0
    road_y_max = total_fleet_width + 5.0
    
    fig.add_trace(go.Mesh3d(
        x=[road_x_min, road_x_max, road_x_max, road_x_min],
        y=[road_y_min, road_y_min, road_y_max, road_y_max],
        z=[ground_z, ground_z, ground_z, ground_z],
        i=[0, 0], j=[1, 2], k=[2, 3],
        color="#2b2d42",
        opacity=0.9,
        name="Ground",
        hoverinfo="none",
        showlegend=False
    ))
    
    # --------------------------------------------------------------------------
    # 2. RENDER EACH TRUCK
    # --------------------------------------------------------------------------
    truck_weights: Dict[int, float] = {i: 0.0 for i in range(len(trucks))}
    for pid, plc in placements.items():
        if plc.is_packed and plc.truck_id in truck_offsets and pid in pkg_map:
            truck_weights[plc.truck_id] += pkg_map[pid].weight
            
    for t_idx, truck in enumerate(trucks):
        y_off = truck_offsets[t_idx]
        L = truck.l
        W = truck.w
        H = truck.h
        
        # A. Truck Chassis (under container and cab)
        chassis_h = 0.5
        chassis_z = -chassis_h
        chassis_x_min = -min(5.0, L * 0.28)
        chassis_x_max = L
        chassis_w = W * 0.8
        chassis_y_min = y_off + (W - chassis_w) / 2
        
        fig.add_trace(_cuboid_mesh(
            chassis_x_min, chassis_y_min, chassis_z,
            chassis_x_max - chassis_x_min, chassis_w, chassis_h,
            color="#1e293b", name=f"Chassis_{t_idx}", opacity=1.0
        ))
        
        # B. Container Floor Bed (Metallic)
        fig.add_trace(_cuboid_mesh(
            0, y_off, -0.2, L, W, 0.2,
            color="#475569", name=f"Floor_{t_idx}", opacity=1.0,
            hovertext=f"Truck {t_idx+1} Floor Bed"
        ))
        
        # C. Container Semi-transparent Walls (Left, Right, Front, Roof)
        # Left wall (y = y_off)
        fig.add_trace(go.Mesh3d(
            x=[0, L, L, 0],
            y=[y_off, y_off, y_off, y_off],
            z=[0, 0, H, H],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color="#94a3b8", opacity=0.15,
            name=f"Wall_L_{t_idx}", hoverinfo="none", showlegend=False
        ))
        # Right wall (y = y_off + W)
        fig.add_trace(go.Mesh3d(
            x=[0, L, L, 0],
            y=[y_off + W, y_off + W, y_off + W, y_off + W],
            z=[0, 0, H, H],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color="#94a3b8", opacity=0.15,
            name=f"Wall_R_{t_idx}", hoverinfo="none", showlegend=False
        ))
        # Front wall (x = 0, behind cabin)
        fig.add_trace(go.Mesh3d(
            x=[0, 0, 0, 0],
            y=[y_off, y_off + W, y_off + W, y_off],
            z=[0, 0, H, H],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color="#64748b", opacity=0.3,
            name=f"Wall_F_{t_idx}", hoverinfo="none", showlegend=False
        ))
        
        # D. Container Wireframe Frame (Bright crisp outline)
        c_ex, c_ey, c_ez = _cuboid_edges(0, y_off, 0, L, W, H)
        fig.add_trace(go.Scatter3d(
            x=c_ex, y=c_ey, z=c_ez,
            mode="lines",
            line=dict(color="#0284c7", width=5),
            name=f"Truck #{t_idx+1} Frame",
            hoverinfo="name"
        ))
        
        # E. Truck Cabin (In front of container: x < 0)
        cab_len = min(5.0, L * 0.28)
        cab_h = H * 0.88
        cab_x0 = -cab_len
        cab_colors = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#9333ea"]
        cab_color = cab_colors[t_idx % len(cab_colors)]
        
        # Cabin body
        fig.add_trace(_cuboid_mesh(
            cab_x0, y_off, 0, cab_len, W, cab_h,
            color=cab_color, name=f"Cabin_{t_idx}", opacity=1.0,
            hovertext=f"Truck #{t_idx+1} Driver Cabin"
        ))
        
        # Cabin Windshield (slanted light blue)
        ws_len = cab_len * 0.4
        ws_h = cab_h * 0.45
        fig.add_trace(_cuboid_mesh(
            cab_x0 - 0.05, y_off + W * 0.1, cab_h * 0.4,
            ws_len * 0.3, W * 0.8, ws_h,
            color="#38bdf8", name=f"Windshield_{t_idx}", opacity=0.9
        ))
        
        # Headlights & Front Bumper
        fig.add_trace(_cuboid_mesh(
            cab_x0 - 0.2, y_off, -0.1, 0.2, W, 0.4,
            color="#0f172a", name=f"Bumper_{t_idx}", opacity=1.0
        ))
        # Left & Right Headlights
        fig.add_trace(_cuboid_mesh(
            cab_x0 - 0.22, y_off + W * 0.08, 0.05, 0.05, W * 0.2, 0.25,
            color="#fef08a", name="Headlight_L", opacity=1.0
        ))
        fig.add_trace(_cuboid_mesh(
            cab_x0 - 0.22, y_off + W * 0.72, 0.05, 0.05, W * 0.2, 0.25,
            color="#fef08a", name="Headlight_R", opacity=1.0
        ))
        
        # F. Wheels (Chassis level to ground)
        wheel_w = 0.5
        wheel_h = wheel_radius * 1.5
        wheel_len = wheel_radius * 1.8
        
        # Front axle positions
        front_axle_x = cab_x0 + cab_len * 0.4
        # Rear tandem axles positions
        rear_axle_1_x = L * 0.65
        rear_axle_2_x = L * 0.88
        
        axle_positions = [front_axle_x, rear_axle_1_x, rear_axle_2_x]
        for ax_x in axle_positions:
            # Left wheel
            fig.add_trace(_cuboid_mesh(
                ax_x - wheel_len / 2, y_off - wheel_w + 0.1, ground_z,
                wheel_len, wheel_w, wheel_h,
                color="#0f172a", name="Tire", opacity=1.0
            ))
            # Right wheel
            fig.add_trace(_cuboid_mesh(
                ax_x - wheel_len / 2, y_off + W - 0.1, ground_z,
                wheel_len, wheel_w, wheel_h,
                color="#0f172a", name="Tire", opacity=1.0
            ))
            
        # G. 3D Floating Truck Label
        used_wt = truck_weights[t_idx]
        cap = truck.max_capacity
        wt_pct = (used_wt / cap * 100) if cap > 0 else 0
        status_color = "#16a34a" if used_wt <= cap else "#dc2626"
        
        fig.add_trace(go.Scatter3d(
            x=[L / 2],
            y=[y_off + W / 2],
            z=[H + 1.2],
            mode="text",
            text=[f"<b>Truck {t_idx+1}</b><br>{L:.0f}x{W:.0f}x{H:.0f} | Load: {used_wt:.0f}/{cap:.0f}kg ({wt_pct:.0f}%)"],
            textposition="top center",
            textfont=dict(size=11, color=status_color),
            showlegend=False,
            hoverinfo="none"
        ))

    # --------------------------------------------------------------------------
    # 3. UNPACKED PACKAGES STAGING GROUND (Behind trucks: x > max_truck_length + 2)
    # --------------------------------------------------------------------------
    staging_x0 = max_truck_length + 3.0
    staging_w = max(total_fleet_width, 12.0)
    staging_len = 10.0
    
    # Palette / Staging Platform
    fig.add_trace(_cuboid_mesh(
        staging_x0, 0, ground_z + 0.1, staging_len, staging_w, 0.3,
        color="#d97706", name="Staging Palette", opacity=0.7,
        hovertext="Unpacked Packages Staging Ground"
    ))
    
    # Label for Staging Area
    fig.add_trace(go.Scatter3d(
        x=[staging_x0 + staging_len / 2],
        y=[staging_w / 2],
        z=[0.6],
        mode="text",
        text=["<b>STAGING AREA (UNPACKED)</b>"],
        textposition="top center",
        textfont=dict(size=12, color="#b45309"),
        showlegend=False,
        hoverinfo="none"
    ))
    
    # --------------------------------------------------------------------------
    # 4. RENDER PACKAGES (PACKED INSIDE TRUCKS + UNPACKED ON STAGING GROUND)
    # --------------------------------------------------------------------------
    packed_edges_x, packed_edges_y, packed_edges_z = [], [], []
    unpacked_grid_x = staging_x0 + 0.8
    unpacked_grid_y = 0.8
    row_max_h = 0.0
    
    for idx, pkg in enumerate(packages):
        plc = placements.get(pkg.id)
        if plc is None:
            plc = Placement(truck_id=None, orientation=pkg.orientation)
            
        dx, dy, dz = pkg.get_effective_dimensions(plc.orientation)
        color = _get_package_color(idx, len(packages), pkg.is_fragile)
        
        if plc.is_packed and plc.truck_id in truck_offsets:
            # Inside truck
            t_id = plc.truck_id
            px = plc.x
            py = truck_offsets[t_id] + plc.y
            pz = plc.z
            status_text = f"Inside Truck #{t_id + 1}"
            
            # Hover text
            fragile_badge = "⚠️ YES (Fragile)" if pkg.is_fragile else "No"
            htext = (
                f"<b>Package: {pkg.id}</b><br>"
                f"Status: {status_text}<br>"
                f"Pos: ({plc.x:.1f}, {plc.y:.1f}, {plc.z:.1f})<br>"
                f"Size: {dx:.1f} x {dy:.1f} x {dz:.1f}<br>"
                f"Weight: {pkg.weight:.1f} kg | Value: ${pkg.value:.1f}<br>"
                f"Fragile: {fragile_badge} | ETA: {pkg.eta:.0f}d"
            )
            
            # Mesh box
            fig.add_trace(_cuboid_mesh(
                px, py, pz, dx, dy, dz,
                color=color, name=f"Package_{pkg.id}",
                opacity=0.90, hovertext=htext
            ))
            
            # Add wireframe edges
            bx, by, bz = _cuboid_edges(px, py, pz, dx, dy, dz)
            packed_edges_x.extend(bx + [None])
            packed_edges_y.extend(by + [None])
            packed_edges_z.extend(bz + [None])
            
            # If fragile, add distinct warning wireframe in red/amber
            if pkg.is_fragile:
                fx, fy, fz = _cuboid_edges(px, py, pz, dx, dy, dz)
                fig.add_trace(go.Scatter3d(
                    x=fx, y=fy, z=fz,
                    mode="lines",
                    line=dict(color="#ef4444", width=3, dash="dash"),
                    showlegend=False, hoverinfo="none"
                ))
                
        else:
            # Unpacked: Arrange neatly on staging palette
            px = unpacked_grid_x
            py = unpacked_grid_y
            pz = ground_z + 0.4
            
            htext = (
                f"<b>Package: {pkg.id}</b><br>"
                f"Status: Outside / Unpacked<br>"
                f"Size: {dx:.1f} x {dy:.1f} x {dz:.1f}<br>"
                f"Weight: {pkg.weight:.1f} kg | Value: ${pkg.value:.1f}<br>"
                f"Fragile: {'YES' if pkg.is_fragile else 'No'}"
            )
            
            fig.add_trace(_cuboid_mesh(
                px, py, pz, dx, dy, dz,
                color=color, name=f"Package_{pkg.id}",
                opacity=0.65, hovertext=htext
            ))
            
            bx, by, bz = _cuboid_edges(px, py, pz, dx, dy, dz)
            packed_edges_x.extend(bx + [None])
            packed_edges_y.extend(by + [None])
            packed_edges_z.extend(bz + [None])
            
            # Advance grid position
            unpacked_grid_y += (dy + 0.8)
            row_max_h = max(row_max_h, dx)
            if unpacked_grid_y + dy > staging_w:
                unpacked_grid_y = 0.8
                unpacked_grid_x += (row_max_h + 0.8)
                row_max_h = 0.0
                
    # Add all box wireframe outlines in a single efficient trace
    if packed_edges_x:
        fig.add_trace(go.Scatter3d(
            x=packed_edges_x, y=packed_edges_y, z=packed_edges_z,
            mode="lines",
            line=dict(color="#1e293b", width=2),
            showlegend=False,
            hoverinfo="none"
        ))
        
    # --------------------------------------------------------------------------
    # 5. CAMERA & SCENE LAYOUT
    # --------------------------------------------------------------------------
    title_text = ""
    if step_info:
        it = step_info.get("iteration", 0)
        sc = step_info.get("objective_value", 0.0)
        title_text = f"Iteration {it} | Objective Value: {sc:.1f}"
        
    default_camera = dict(
        eye=dict(x=-1.5, y=-1.8, z=1.4),
        center=dict(x=0, y=0, z=0),
        up=dict(x=0, y=0, z=1)
    )
    active_camera = camera if camera else default_camera

    fig.update_layout(
        title=dict(text=title_text, x=0.5, y=0.96, font=dict(size=14, color="#334155")),
        margin=dict(l=0, r=0, t=25, b=0),
        autosize=True,
        uirevision="truck_scene_revision",
        scene=dict(
            uirevision="truck_scene_revision",
            aspectmode="data",
            camera=active_camera,
            xaxis=dict(title="Length (X)", showgrid=True, zeroline=False, backgroundcolor="#f8fafc"),
            yaxis=dict(title="Width (Y)", showgrid=True, zeroline=False, backgroundcolor="#f8fafc"),
            zaxis=dict(title="Height (Z)", showgrid=True, zeroline=False, backgroundcolor="#f8fafc"),
        )
    )
    
    return fig
