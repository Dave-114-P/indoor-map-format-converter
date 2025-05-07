import ezdxf
import geojson
from shapely.geometry import mapping, LineString, Point, Polygon

# convert dxf into geojson with official packages

def dxf_to_geojson(dxf_path, geojson_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    features = []

    for entity in msp:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            line = LineString([(start.x, start.y), (end.x, end.y)])
            features.append(geojson.Feature(geometry=mapping(line)))

        elif entity.dxftype() == "CIRCLE":
            center = entity.dxf.center
            point = Point((center.x, center.y))
            features.append(geojson.Feature(geometry=mapping(point)))

        elif entity.dxftype() == "LWPOLYLINE":
            points = [(pt[0], pt[1]) for pt in entity.get_points()]
            if entity.closed:
                poly = Polygon(points)
                features.append(geojson.Feature(geometry=mapping(poly)))
            else:
                line = LineString(points)
                features.append(geojson.Feature(geometry=mapping(line)))

    gj = geojson.FeatureCollection(features)
    with open(geojson_path, "w") as f:
        geojson.dump(gj, f, indent=2)

    print(f"GeoJSON saved to: {geojson_path}")

# coverting
dxf_to_geojson("sample.dxf", "sample.geojson")
