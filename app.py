# app.py (VERSIÓN FINAL Y COMPLETA - CORRECCIÓN DE BOUNDS)

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import numpy as np
import pyvista as pv
import os
import math 
import traceback

app = Flask(__name__)
CORS(app) 

# --- FUNCIÓN DE CÁLCULO BASE ---
def calcular_campos(r_e, h_e, I_f, rho):
    """Realiza todos los cálculos de V y E y genera la nube de puntos."""
    r_s = 4.0 
    h_s = 6.0 
    nx, ny, nz = 30, 30, 30 
    epsilon = 1e-6 

    x = np.linspace(-r_s, r_s, nx)
    y = np.linspace(-r_s, r_s, ny)
    z = np.linspace(0.001, h_s, nz) 
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    points = np.c_[X.ravel(), Y.ravel(), Z.ravel()]
    
    if points.size == 0:
         raise ValueError('La malla 3D generada está vacía (cero puntos).')

    Factor_V = rho * I_f / (2.0 * math.pi * h_e) 

    V_values = np.zeros(len(points))
    E_vectors = np.zeros_like(points)
    
    for i, (px, py, pz) in enumerate(points):
        r = np.sqrt(px**2 + py**2)
        
        if r < r_e: r_calc = r_e 
        else: r_calc = r
        
        if r_calc < r_s:
             V_values[i] = Factor_V * np.log(r_s / (r_calc + epsilon))
        else:
             V_values[i] = 0.0 

        if r < r_e: magnitude = 0.0 
        else: magnitude = V_values[i] / (r + epsilon)
        
        if r < 1e-6: E_vectors[i] = np.array([0,0,0])
        else: E_vectors[i] = magnitude * np.array([px/r, py/r, 0])

    E_mag = np.linalg.norm(E_vectors, axis=1)
    
    cloud = pv.PolyData(points)
    cloud["E_vec"] = E_vectors
    cloud["E_mag"] = E_mag
    cloud["V_pot"] = V_values 
    
    return cloud, V_values, E_mag, r_s, h_e

# --- RUTA 1: SIMULACIÓN 3D (ANIMADA) ---
# (Sin cambios, ya funciona)

@app.route("/simular_3d", methods=["POST"])
def simular_3d():
    try:
        data = request.json
        r_e = float(data["r_e"]) 
        h_e = float(data["h_e"]) 
        I_f = float(data["I_f"]) 
        rho = float(data["rho"]) 

        if r_e <= 0 or h_e <= 0 or I_f <= 0 or rho <= 0:
             return jsonify({'error': 'Todos los parámetros deben ser positivos.'}), 400

        cloud, V_values, E_mag, r_s, h_e = calcular_campos(r_e, h_e, I_f, rho)
        
        E_mag_max = E_mag.max() if E_mag.size > 0 and E_mag.max() != 0 else 1.0
        epsilon = 1e-6
        V_max = V_values.max() if V_values.size > 0 else 500.0
        V_clim = [0, max(V_max * 1.1, 500.0)] 

        pv.global_theme.allow_empty_mesh = True 
        try:
             grid = cloud.delaunay_3d().extract_surface()
             grid["V_pot"] = V_values
        except Exception:
             grid = cloud

        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "white"
        
        slice_xz = grid.slice(normal='y', origin=(0, 0, h_e/2))
        plotter.add_mesh(slice_xz, scalars='V_pot', cmap='viridis', clim=V_clim, label="Potencial V (2D Corte)")
        
        cylinder = pv.Cylinder(center=(0,0,h_e/2), direction=(0,0,1), radius=r_e, height=h_e)
        plotter.add_mesh(cylinder, color="red", opacity=0.9, label="Electrodo")
        
        arrows = cloud.glyph(
            orient="E_vec",
            scale="E_mag",
            factor=0.5 * r_s / (E_mag_max + epsilon), 
            tolerance=0.01 
        )
        plotter.add_mesh(arrows, scalars=arrows["E_mag"], cmap="plasma", label="Campo Eléctrico E")
        
        plotter.add_scalar_bar('Potencial V (V)', vertical=True, interactive=False, title_font_size=10, label_font_size=8, position_x=0.05, position_y=0.2)
        plotter.add_scalar_bar('Campo E (V/m)', vertical=True, interactive=False, title_font_size=10, label_font_size=8, position_x=0.90, position_y=0.2)
        
        filename = "simulacion_3d_animada.gif"
        plotter.open_gif(filename)

        for i in range(40):
            plotter.camera.azimuth += 2 
            plotter.write_frame()

        plotter.close()

        return jsonify({"filename": filename})
    
    except Exception as e:
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500
# app.py (AGREGA ESTA FUNCIÓN COMPLETA)

def calcular_campos_2d(r_e, I_f, rho):
    """Calcula V y E directamente en una malla 2D (plano XY)."""
    # Usaremos una Longitud Efectiva H_e fija para la fórmula V.
    h_e_fixed = 1.0 
    r_s = 4.0 # Dominio de simulación fijo
    nx, ny = 100, 100 # Alta resolución para el heatmap

    x = np.linspace(-r_s, r_s, nx)
    y = np.linspace(-r_s, r_s, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")
    
    # Creamos la malla 2D (StructuredGrid)
    grid_2d = pv.StructuredGrid(X, Y, np.zeros_like(X)) # Forzamos Z=0
    points_2d = grid_2d.points
    
    if points_2d.size == 0:
         raise ValueError('La malla 2D generada está vacía.')

    Factor_V = rho * I_f / (2.0 * math.pi * h_e_fixed) 
    epsilon = 1e-6 

    V_values = np.zeros(len(points_2d))
    E_vectors = np.zeros_like(points_2d)
    
    for i, (px, py, pz) in enumerate(points_2d):
        r = np.sqrt(px**2 + py**2)
        
        # Aplicamos el mismo modelo de potencial para el plano XY (aproximación)
        if r < r_e: r_calc = r_e 
        else: r_calc = r
        
        if r_calc < r_s:
             V_values[i] = Factor_V * np.log(r_s / (r_calc + epsilon))
        else:
             V_values[i] = 0.0 

        # Cálculo del Campo E (Radial y en el plano XY)
        if r < r_e: magnitude = 0.0 
        else: magnitude = V_values[i] / (r + epsilon)
        
        if r < 1e-6: E_vectors[i] = np.array([0,0,0])
        else: E_vectors[i] = magnitude * np.array([px/r, py/r, 0])

    E_mag = np.linalg.norm(E_vectors, axis=1)
    
    # Asignar data a la malla 2D
    grid_2d["E_vec"] = E_vectors
    grid_2d["E_mag"] = E_mag
    grid_2d["V_pot"] = V_values 
    
    return grid_2d, V_values, E_mag, r_s
# --- RUTA 2: SIMULACIÓN 2D (VISTA SUPERIOR) ---

# app.py (RUTA simular_2d REEMPLAZADA POR LA VERSIÓN 2D PURA)

@app.route("/simular_2d", methods=["POST"])
def simular_2d():
    """Genera la vista 2D del potencial y Campo E en el plano XY."""
    try:
        data = request.json
        r_e = float(data["r_e"]) 
        # Ya no necesitamos h_e, pero lo leemos para no romper el front-end
        # h_e = float(data["h_e"]) 
        I_f = float(data["I_f"]) 
        rho = float(data["rho"]) 

        if r_e <= 0 or I_f <= 0 or rho <= 0:
             return jsonify({'error': 'Todos los parámetros deben ser positivos.'}), 400

        # LLAMAMOS A LA FUNCIÓN PURA 2D
        grid_2d, V_values, E_mag, r_s = calcular_campos_2d(r_e, I_f, rho)

        E_mag_max = E_mag.max() if E_mag.size > 0 and E_mag.max() != 0 else 1.0
        epsilon = 1e-6
        V_max = V_values.max() if V_values.size > 0 else 500.0
        V_clim = [0, max(V_max * 1.1, 500.0)] 
        
        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "white"
        
        # 1. Dibujamos la malla 2D (Heatmap)
        plotter.add_mesh(grid_2d, scalars='V_pot', cmap='viridis', clim=V_clim, label="Potencial V (Superficie)")
        
        # 2. Dibuja el electrodo como un círculo central
        # Lo dibujamos en Z=0 (el mismo plano que la malla)
        try:
            circle = pv.Disc(center=(0,0,0), inner=0, outer=r_e, n_sides=50)
        except TypeError:
            circle = pv.Disc(center=(0,0,0), inner=0, outer=r_e)
            
        plotter.add_mesh(circle, color='red', opacity=0.9, label='Electrodo')

        # 3. AGREGAMOS EL CAMPO ELÉCTRICO (E) - Flechas 
        # Tomamos los puntos directamente de la malla 2D
        arrows_2d = grid_2d.glyph(
            orient="E_vec",
            scale="E_mag",
            factor=0.1 * r_s / (E_mag_max + epsilon), 
            tolerance=0.01 
        )
        plotter.add_mesh(arrows_2d, scalars=arrows_2d["E_mag"], cmap="plasma", label="Campo Eléctrico E")
        
        # 4. Ajustar la cámara para una VISTA SUPERIOR
        plotter.view_xy() 
        plotter.camera.zoom(1.2)
        
        # 5. Barra de Color
        plotter.add_scalar_bar('Potencial V (V)', vertical=True, interactive=False, title_font_size=10, label_font_size=8)
        
        # 6. Generar PNG estático
        filename = "simulacion_2d_superior.png"
        plotter.screenshot(filename)
        plotter.close()

        return jsonify({"filename": filename})
    
    except Exception as e:
        traceback.print_exc() 
        return jsonify({"error": str(e)}), 500
# --- RUTAS DE OBTENCIÓN DE ARCHIVOS ---

@app.route("/get_gif")
def get_gif():
    name = request.args.get("name")
    path = os.path.join(os.getcwd(), name) 
    if name and os.path.exists(path):
        return send_file(path, mimetype="image/gif")
    return jsonify({"error": "Archivo GIF no encontrado"}), 404

@app.route("/get_png")
def get_png():
    name = request.args.get("name")
    path = os.path.join(os.getcwd(), name) 
    if name and os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return jsonify({"error": "Archivo PNG no encontrado"}), 404


if __name__ == "__main__":
    app.run(debug=True)