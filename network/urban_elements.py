import xml.etree.ElementTree as ET
import os
import random

def create_urban_elements(network_dir='network'):
    """Create urban elements"""
    create_buildings(network_dir)
    create_pois(network_dir)
    print("Urban elements created")

def create_buildings(network_dir):
    """Generate buildings"""
    buildings_file = os.path.join(network_dir, 'buildings.poly.xml')
    
    root = ET.Element('polygons', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                     xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/polygons_file.xsd")
    
    spacing = 250
    building_types = [
        {'height': 12, 'color': '0.85,0.85,0.90'},
        {'height': 25, 'color': '0.75,0.78,0.85'},
        {'height': 35, 'color': '0.55,0.60,0.75'},
    ]
    
    building_id = 0
    
    for row in range(4):
        for col in range(4):
            center_x = col * spacing + spacing/2
            center_y = row * spacing + spacing/2
            
            for i in range(random.randint(2, 4)):
                building_type = random.choice(building_types)
                
                offset_x = random.uniform(-75, 75)
                offset_y = random.uniform(-75, 75)
                
                x = center_x + offset_x
                y = center_y + offset_y
                
                width = random.uniform(20, 40)
                depth = random.uniform(15, 35)
                height = building_type['height'] + random.uniform(-3, 8)
                
                poly = ET.SubElement(root, 'poly')
                poly.set('id', f'building_{building_id}')
                poly.set('color', building_type['color'])
                poly.set('fill', '1')
                poly.set('layer', '1')
                poly.set('height', str(height))
                
                corners = [
                    f"{x - width/2},{y - depth/2}",
                    f"{x + width/2},{y - depth/2}",
                    f"{x + width/2},{y + depth/2}",
                    f"{x - width/2},{y + depth/2}"
                ]
                poly.set('shape', ' '.join(corners))
                
                building_id += 1
    
    tree = ET.ElementTree(root)
    tree.write(buildings_file, encoding='utf-8', xml_declaration=True)
    print(f"Buildings generated: {buildings_file}")

def create_pois(network_dir):
    """Create points of interest"""
    poi_file = os.path.join(network_dir, 'pois.add.xml')
    
    root = ET.Element('additional', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                     xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd")
    
    spacing = 250
    poi_id = 0
    
    for row in range(4):
        for col in range(3):
            for side in [-1, 1]:
                for tree_pos in range(0, 250, 40):
                    x = col * spacing + tree_pos
                    y = row * spacing + side * 15
                    
                    poi = ET.SubElement(root, 'poi')
                    poi.set('id', f'tree_{poi_id}')
                    poi.set('type', 'tree')
                    poi.set('x', str(x))
                    poi.set('y', str(y))
                    poi.set('color', '0.2,0.8,0.2')
                    poi.set('width', '3')
                    poi.set('height', '8')
                    poi_id += 1
    
    for col in range(4):
        for row in range(3):
            for side in [-1, 1]:
                for tree_pos in range(0, 250, 40):
                    x = col * spacing + side * 15
                    y = row * spacing + tree_pos
                    
                    poi = ET.SubElement(root, 'poi')
                    poi.set('id', f'tree_{poi_id}')
                    poi.set('type', 'tree')
                    poi.set('x', str(x))
                    poi.set('y', str(y))
                    poi.set('color', '0.2,0.8,0.2')
                    poi.set('width', '3')
                    poi.set('height', '8')
                    poi_id += 1
    
    tree = ET.ElementTree(root)
    tree.write(poi_file, encoding='utf-8', xml_declaration=True)
    print(f"POIs generated: {poi_file}")

def create_3d_gui_settings(network_dir='network'):
    """Create GUI settings"""
    gui_file = os.path.join(network_dir, 'gui-settings.xml')
    
    root = ET.Element('viewsettings')
    
    scheme = ET.SubElement(root, 'scheme')
    scheme.set('name', 'enhanced_3d')
    
    background = ET.SubElement(scheme, 'background')
    background.set('backgroundColor', '0.82,0.92,1.0')
    background.set('showGrid', '0')
    
    opengl = ET.SubElement(scheme, 'opengl')
    opengl.set('antialiase', '1')
    opengl.set('dither', '1')
    
    delay = ET.SubElement(scheme, 'delay')
    delay.set('value', '50')
    
    viewport = ET.SubElement(scheme, 'viewport')
    viewport.set('zoom', '650.00')
    viewport.set('x', '375.00')
    viewport.set('y', '375.00')
    
    tree = ET.ElementTree(root)
    tree.write(gui_file, encoding='utf-8', xml_declaration=True)
    print(f"GUI settings created: {gui_file}")
