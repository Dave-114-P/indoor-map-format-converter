import ezdxf
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from pathlib import Path

# Configuration
DXF_UNIT = "mm"  # Options: "mm", "cm", "m", "ft"
INPUT_DIR = "DXF"
OUTPUT_DIR = "OSM"

# Unit conversion factors to meters (for metadata)
UNIT_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "ft": 0.3048
}

def dxf_to_osm(dxf_path, osm_path, unit="mm"):
    """Convert DXF to OSM with local coordinates (x, y) and proper tags."""
    print(f"Converting DXF: {dxf_path} to OSM: {osm_path}")

    if not os.path.exists(dxf_path):
        print(f"Error: DXF file not found at {dxf_path}")
        return
        
    # Read DXF file
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    
    # Initialize OSM structure
    osm = ET.Element("osm", version="0.6", generator="dxf_to_osm")
    ET.SubElement(osm, "meta", author="dxf_to_osm", unit=unit, source="indoor_dwg")
    
    # Track nodes and their IDs
    node_id = 1
    node_map = {}  # (x, y) -> node_id
    ways = []
    
    # Process DXF entities
    for entity in msp:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            points = [(start.x, start.y), (end.x, end.y)]
            
            # Create or get node IDs
            node_refs = []
            for x, y in points:
                coord = (x, y)
                if coord not in node_map:
                    node_map[coord] = str(node_id)
                    ET.SubElement(osm, "node", id=str(node_id), visible="true", version="1", x=str(x), y=str(y))
                    node_id += 1
                node_refs.append(node_map[coord])
            
            # Create way
            if len(set(node_refs)) > 1:  # Skip if start == end
                way = {"id": str(node_id), "nodes": node_refs, "closed": False}
                ways.append(way)
                node_id += 1
        
        elif entity.dxftype() == "LWPOLYLINE":
            points = [(pt[0], pt[1]) for pt in entity.get_points()]
            is_closed = entity.closed and len(points) > 2
            
            # Create or get node IDs
            node_refs = []
            for x, y in points:
                coord = (x, y)
                if coord not in node_map:
                    node_map[coord] = str(node_id)
                    ET.SubElement(osm, "node", id=str(node_id), visible="true", version="1", x=str(x), y=str(y))
                    node_id += 1
                node_refs.append(node_map[coord])
            
            # Create way
            if len(set(node_refs)) >= (3 if is_closed else 2):  # Minimum points for valid geometry
                way = {"id": str(node_id), "nodes": node_refs, "closed": is_closed}
                if is_closed:
                    way["nodes"].append(way["nodes"][0])  # Ensure closed way
                ways.append(way)
                node_id += 1
        
        elif entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            x, y = center.x, center.y
            coord = (x, y)
            if coord not in node_map:
                node_map[coord] = str(node_id)
                node = ET.SubElement(osm, "node", id=str(node_id), visible="true", version="1", x=str(x), y=str(y))
                ET.SubElement(node, "tag", k="highway", v="point")
                ET.SubElement(node, "tag", k="indoor", v="yes")
                node_id += 1
    
    # Add ways to OSM
    for way in ways:
        way_elem = ET.SubElement(osm, "way", id=way["id"], visible="true", version="1")
        for ref in way["nodes"]:
            ET.SubElement(way_elem, "nd", ref=ref)
        
        # Add tags based on geometry
        if way["closed"]:
            ET.SubElement(way_elem, "tag", k="building", v="room")
        else:
            ET.SubElement(way_elem, "tag", k="highway", v="wall")
        ET.SubElement(way_elem, "tag", k="indoor", v="yes")
        ET.SubElement(way_elem, "tag", k="source", v="DXF")
        ET.SubElement(way_elem, "tag", k="unit", v=unit)
    
    # Write OSM file
    Path(osm_path).parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(osm)
    xml_str = minidom.parseString(ET.tostring(osm)).toprettyxml(indent="  ")
    with open(osm_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"OSM file saved to: {osm_path}")
    
    # Debug: Print stats
    print(f"Nodes created: {len(node_map)}")
    print(f"Ways created: {len(ways)}")
    x_coords = [x for x, y in node_map]
    y_coords = [y for x, y in node_map]
    print(f"X range: {min(x_coords):.3f} to {max(x_coords):.3f}")
    print(f"Y range: {min(y_coords):.3f} to {max(y_coords):.3f}")

def main():
    
    dxf_path = os.path.join(INPUT_DIR, "sample.dxf")
    osm_path = os.path.join(OUTPUT_DIR, "sample.osm")
    dxf_to_osm(dxf_path, osm_path, unit=DXF_UNIT)

if __name__ == "__main__":
    main()