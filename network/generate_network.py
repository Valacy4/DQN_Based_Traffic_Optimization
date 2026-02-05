import xml.etree.ElementTree as ET
import os
import subprocess

def generate_3x3_grid():
    """Generate 3x3 grid network"""
    network_dir = 'network'
    os.makedirs(network_dir, exist_ok=True)
    
    net_file = os.path.join(network_dir, 'grid.net.xml')
    
    nodes = ET.Element('nodes', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance", 
                       xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/nodes_file.xsd")
    
    spacing = 250
    for row in range(4):
        for col in range(4):
            node = ET.SubElement(nodes, 'node')
            node.set('id', f'n{row}_{col}')
            node.set('x', str(col * spacing))
            node.set('y', str(row * spacing))
            
            if 0 < row < 3 and 0 < col < 3:
                node.set('type', 'traffic_light')
                node.set('tlType', 'static')
                node.set('shape', f"{col * spacing - 15},{row * spacing - 15} "
                                f"{col * spacing + 15},{row * spacing - 15} "
                                f"{col * spacing + 15},{row * spacing + 15} "
                                f"{col * spacing - 15},{row * spacing + 15}")
    
    nodes_file = os.path.join(network_dir, 'grid.nod.xml')
    tree = ET.ElementTree(nodes)
    tree.write(nodes_file, encoding='utf-8', xml_declaration=True)
    
    edges = ET.Element('edges', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                      xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/edges_file.xsd")
    
    for row in range(4):
        for col in range(3):
            edge = ET.SubElement(edges, 'edge')
            edge.set('id', f'h{row}_{col}')
            edge.set('from', f'n{row}_{col}')
            edge.set('to', f'n{row}_{col+1}')
            edge.set('numLanes', '2')
            edge.set('speed', '13.89')
            edge.set('priority', '5')
            edge.set('spreadType', 'center')
            
            edge = ET.SubElement(edges, 'edge')
            edge.set('id', f'h{row}_{col}_rev')
            edge.set('from', f'n{row}_{col+1}')
            edge.set('to', f'n{row}_{col}')
            edge.set('numLanes', '2')
            edge.set('speed', '13.89')
            edge.set('priority', '5')
            edge.set('spreadType', 'center')
    
    for col in range(4):
        for row in range(3):
            edge = ET.SubElement(edges, 'edge')
            edge.set('id', f'v{row}_{col}')
            edge.set('from', f'n{row}_{col}')
            edge.set('to', f'n{row+1}_{col}')
            edge.set('numLanes', '2')
            edge.set('speed', '13.89')
            edge.set('priority', '5')
            edge.set('spreadType', 'center')
            
            edge = ET.SubElement(edges, 'edge')
            edge.set('id', f'v{row}_{col}_rev')
            edge.set('from', f'n{row+1}_{col}')
            edge.set('to', f'n{row}_{col}')
            edge.set('numLanes', '2')
            edge.set('speed', '13.89')
            edge.set('priority', '5')
            edge.set('spreadType', 'center')
    
    edges_file = os.path.join(network_dir, 'grid.edg.xml')
    tree = ET.ElementTree(edges)
    tree.write(edges_file, encoding='utf-8', xml_declaration=True)
    
    types = ET.Element('types', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                      xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/types_file.xsd")
    
    typ = ET.SubElement(types, 'type')
    typ.set('id', 'default')
    typ.set('priority', '5')
    typ.set('numLanes', '2')
    typ.set('speed', '13.89')
    typ.set('allow', 'passenger emergency bicycle delivery truck motorcycle')
    typ.set('sidewalkWidth', '2.0')
    
    types_file = os.path.join(network_dir, 'grid.typ.xml')
    tree = ET.ElementTree(types)
    tree.write(types_file, encoding='utf-8', xml_declaration=True)
    
    _generate_traffic_light_logics(network_dir)
    
    try:
        result = subprocess.run([
            'netconvert',
            '-n', nodes_file,
            '-e', edges_file,
            '-t', types_file,
            '-o', net_file,
            '--no-turnarounds', 'false',
            '--junctions.corner-detail', '5',
            '--junctions.limit-turn-speed', '5.5',
            '--crossings.guess', 'true',
            '--walkingareas', 'true',
            '--sidewalks.guess', 'true',
            '--junctions.scurve-stretch', '1.0',
            '--tls.guess-signals', 'true',
            '--tls.discard-simple', 'false',
            '--geometry.remove', 'false',
            '--roundabouts.guess', 'false'
        ], capture_output=True, text=True, check=True)
        
        print(f"Network generated: {net_file}")
        return net_file
    except subprocess.CalledProcessError as e:
        print(f"Error generating network: {e.stderr}")
        raise

def _generate_traffic_light_logics(network_dir):
    """Generate traffic light logic"""
    tls_file = os.path.join(network_dir, 'traffic_lights.add.xml')
    
    root = ET.Element('additional', xmlns__xsi="http://www.w3.org/2001/XMLSchema-instance",
                     xsi__noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd")
    
    for row in range(1, 3):
        for col in range(1, 3):
            tls_id = f'n{row}_{col}'
            
            tls = ET.SubElement(root, 'tlLogic')
            tls.set('id', tls_id)
            tls.set('type', 'static')
            tls.set('programID', '0')
            tls.set('offset', '0')
            
            phase = ET.SubElement(tls, 'phase')
            phase.set('duration', '31')
            phase.set('state', 'GGrrrrGGrrrr')
            
            phase = ET.SubElement(tls, 'phase')
            phase.set('duration', '4')
            phase.set('state', 'yyrrrryyrrr')
            
            phase = ET.SubElement(tls, 'phase')
            phase.set('duration', '31')
            phase.set('state', 'rrGGrrrrGGrr')
            
            phase = ET.SubElement(tls, 'phase')
            phase.set('duration', '4')
            phase.set('state', 'rryyrrrryyrr')
    
    tree = ET.ElementTree(root)
    tree.write(tls_file, encoding='utf-8', xml_declaration=True)
    print(f"Traffic light logics generated: {tls_file}")
