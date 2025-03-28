import geopandas as gpd
import time
import pandas as pd
import numpy as np

#gdf = gpd.read_file(r"D:\Atlasus\Naloty\Dzien_1\trasa_test.gpkg")
gdf = gpd.read_file(r"D:\Atlasus\Naloty\do_usuwania.gpkg")
gdf_copy = gdf
pathway = []
coordsX = []
coordsY = []

def length(feature):
    return feature["length"].values[0]

def numbers(feature):
    return feature["Numer"].values[0]

def points(number, gdf):

    shape = gdf[gdf["Numer"] == number]

    multi = shape["geometry"].iloc[0]
    line = list(multi.geoms)

    for i in line:

        first_point = i.coords[0]
        second_point = i.coords[1]

        coordsX.append(first_point[0])
        coordsX.append(second_point[0])
        coordsY.append(first_point[1])
        coordsY.append(second_point[1])

def point_list(pathway, gdf):

    pathway.pop(0)
    print(pathway)

    for i in pathway:
        points(i, gdf)

def text_maker(coordsX, coordsY):

    template = [[int(1), int(0), int(16), 0, 0, 0, 0, 53, 18, 100, int(1)]]

    columns = ["Col1", "Frame", "Command", "Col2", "Col3", "Col4", "Col5", "B", "L", "H", "Col6"]

    int_cols = ["Col1", "Frame", "Command", "Col6"]

    df = pd.DataFrame(template, columns=columns)

    for i in range(len(coordsX)):

        b = coordsY[i]
        l = coordsX[i]

        add = {"Col1" : int(0), "Frame" : int(10), "Command" : int(16), "Col2" : 0, "Col3" : 0, "Col4" : 0, "Col5" : 0, "B" : b, "L" : l, "H" : 55, "Col6" : int(1)}
        df = df._append(add, ignore_index = True)
    
    df[int_cols] = df[int_cols].map(np.int64)

    df.to_csv(r"D:\Atlasus\Naloty\Dzien_1\trasa.waypoints", sep = "\t", index = True, header = None)
    



start = 513 #starting line
max_length = 5000  #how long should the segment be
current_length = 0  #value for collecting lengths

points(start, gdf)
start_line = gdf[gdf["Numer"] == start] #set the starting line
pathway.append(int(numbers(start_line)))
gdf = gdf[gdf["Numer"] != start]
current_length = current_length + length(start_line)   #add the starting line to the accumulated length


def line_maker(start_line, max_length, current_length, gdf):
    while current_length <= max_length: #while length hasn't reached the limit value
        neighbours = start_line["Sasiedzi"].str.split(",").values[0]   #get neighbours and make them into a list
        print("neighbours of current starting line",neighbours)
        num_neighbours = {} #empty dir
        to_remove = []
        line_left = []

        while len(neighbours) > 1:
            for i in neighbours:    #for each neighbour that the start line had
                a = gdf[gdf["Numer"] == int(i)] #get the feature
                try:
                    number = a["Sasiedzi"].str.split(",").values[0] #get the number of neighbours
                    num_neighbours[int(i)] = len(number)    #add the number to the directory
                except:
                    print(f"Line already used - {i}, skipping") #if the line was already used add it to removal list
                    to_remove.append(i)
                #time.sleep(0.5)

            neighbours = [x for x in neighbours if x not in to_remove] #remove lines that were already used
            print("neighbours after removal of arleady used lines", neighbours)
            min_neighbours = [key for key, value in num_neighbours.items() if value == min(num_neighbours.values())] #finding lines with lowest number of neighbours. If its 2 or 3
            #it means its hanging, more means that it has more neighbours down the line.
            print("Number of lines with minimal neighbours",len(min_neighbours))

            if len(min_neighbours) == 1: #if there is a single smallest neighbour
                if num_neighbours.get(min_neighbours[0]) == 2: 
                    print("using",min_neighbours[0])
                    hanging_neighbour = gdf[gdf["Numer"] == min_neighbours[0]] #get the feature
                    current_length = current_length + 2*(length(hanging_neighbour)) #add its length to the count, its 2* cause its hanging
                    gdf = gdf[gdf["Numer"] != min_neighbours[0]] #remove it from the dataframe
                    neighbours.remove(str(numbers(hanging_neighbour)))    #remove it from the neighbours list
                    num_neighbours.pop(numbers(hanging_neighbour))    #remove it from available neighbours
                    pathway.append(int(numbers(hanging_neighbour)))   #add it to the pathway list
                elif num_neighbours.get(min_neighbours[0]) == 3:
                    hanging_neighbour = gdf[gdf["Numer"] == min_neighbours[0]]
                    current_length = current_length + 2*(length(hanging_neighbour))
                    gdf = gdf[gdf["Numer"] != min_neighbours[0]]
                    neighbours.remove(str(numbers(hanging_neighbour)))
                    num_neighbours.pop(numbers(hanging_neighbour))
                    pathway.append(int(numbers(hanging_neighbour)))
                else:
                    line = gdf[gdf["Numer"] == min_neighbours[0]]   #get the feature
                    line_left.append(str(numbers(line)))  #add it to a temporary list
                    neighbours = line_left  #after the line was chosen, make it the only one available
                    print("Intersection detected, using ", numbers(line))

            if len(min_neighbours) >= 2: #if there are two smallest neighbours
                if num_neighbours.get(min_neighbours[0]) == 2:
                    for i in min_neighbours: #for each of the hanging neighbour we do the same
                        hanging_neighbour = gdf[gdf["Numer"] == i] #get the feature
                        current_length = current_length + 2*(length(hanging_neighbour)) #add its length to the count, its 2* cause its hanging
                        gdf = gdf[gdf["Numer"] != i] #remove it from the dataframe
                        neighbours.remove(str(numbers(hanging_neighbour)))    #remove it from the neighbours list
                        num_neighbours.pop(numbers(hanging_neighbour))    #remove it from available neighbours
                        pathway.append(int(numbers(hanging_neighbour)))   #add it to the pathway list
                        if len(neighbours) == 0:    #in the case when there were only hanging neighbours, break, because its the end of the line
                            print("END OF LINE")
                            break

                elif num_neighbours.get(min_neighbours[0]) == 3:
                    for i in min_neighbours:
                        hanging_neighbour = gdf[gdf["Numer"] == i]
                        current_length = current_length + 2*(length(hanging_neighbour))
                        gdf = gdf[gdf["Numer"] != i]
                        neighbours.remove(str(numbers(hanging_neighbour)))
                        num_neighbours.pop(numbers(hanging_neighbour))
                        pathway.append(int(numbers(hanging_neighbour)))
                        if len(neighbours) == 0:
                            print("END OF LINE")
                            break

                else:
                    line = gdf[gdf["Numer"] == min_neighbours[0]]
                    line_left.append(str(numbers(line)))
                    neighbours = line_left
                    print("Intersection detected, using ", numbers(line))

        try:
            print("Whats left: ", int(neighbours[0]))
            print("Current length", current_length)
            print("Current path", pathway)
            start_line = gdf[gdf["Numer"] == int(neighbours[0])] #set the new starting line for the next loop
            pathway.append(int(numbers(start_line)))  #add the new start line to the pathway
            current_length = current_length + length(start_line)    #add its length
            gdf = gdf[gdf["Numer"] != int(neighbours[0])] #remove the start line from the dataset
        except:
            break #if above cannot be executed, break the loop
    last_line = pathway[-1]     
    return current_length, pathway, last_line


def main():
    cur, path, last = line_maker(start_line, max_length, current_length, gdf)

    print("\n, \n, \n, \n PROGRAM FINISHED, LINE ENDED")
    print("Current length : ", cur)
    print("Current path : ", path)
    print("Last line : ", last)
    #point_list(path, gdf)
    #text_maker(coordsX, coordsY)

    

    selected_line = gdf_copy[gdf_copy["Numer"].isin(path)]
    output = r"D:\Wycena_Naloty\ENEA\Kolejnosc\line.gpkg"
    selected_line.to_file(output, driver = "GPKG")

main()


