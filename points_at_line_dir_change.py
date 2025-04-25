import geopandas as gpd
import math

points = gpd.read_file(r"D:\___WodyPolskie\Gora\przekroje\vertices.shp")

points.sort_values("vertex_ind", ascending = True, inplace = True)

points["Section"] = ""
points["Azimuth"] = ""

diff_thresh = 20

unique_ditch = points["fid"].value_counts()
print(unique_ditch)
unique_ditch_num = unique_ditch.index

def condition(val):
    return (points["fid"] == unique_ditch_num[index]) & (points["vertex_ind"] == vertex + val)

def czwartak(dx, dy, fi):
    if dx > 0 and dy > 0:
        return fi
    elif dy < 0 and dx > 0:
        return 180 - fi
    elif dy < 0 and dx < 0:
        return 180 + fi
    elif dy > 0 and dx < 0:
        return 360 - fi


for index in range(unique_ditch_num.shape[0]):
    index_count = int(unique_ditch.iloc[index])

    for vertex in range(index_count):

        if vertex > 0:
            vertices_prev = points.loc[condition(-1), "geometry"].iloc[0]
            vertices_curr = points.loc[condition(0), "geometry"].iloc[0]

            dx = vertices_prev.y - vertices_curr.y
            dy = vertices_prev.x - vertices_curr.x
            try:
                fi = (math.atan(abs((dy) / (dx))) * 180) /math.pi

                azimuth = czwartak(dy, dx, fi)
                points.loc[condition(0), "Azimuth"] = azimuth
            except:
                pass
    
    for vertex in range(index_count - 1):
        try:
            diff = int(points.loc[condition(1), "Azimuth"].iloc[0]) - int(points.loc[condition(0), "Azimuth"].iloc[0])
            if abs(diff) > diff_thresh:
                points.loc[condition(0), "Section"] = True
        except:
            pass


#print(points)
points.to_file(r"D:\___WodyPolskie\Gora\przekroje\selected.shp")