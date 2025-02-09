import geopandas as gpd
import time

gdf = gpd.read_file(r"D:\Atlasus\Naloty\do_usuwania.gpkg")
gdf_copy = gdf
pathway = []


def length(feature):
    return feature["length"].values[0]

def numbers(feature):
    return feature["Numer"].values[0]


start = 412 #starting line
max_length = 5000  #how long should the segment be
current_length = 0  #value for collecting lengths
start_line = gdf[gdf["Numer"] == start] #set the starting line
pathway.append(int(numbers(start_line)))
gdf = gdf[gdf["Numer"] != start]
current_length = current_length + length(start_line)   #add the starting line to the accumulated length


def line_maker(start_line, max_length, current_length, gdf):
    intersections = []
    while current_length <= max_length: #while length hasn't reached the limit value
        neighbours = start_line["Sasiedzi"].str.split(",").values[0]   #get neighbours and make them into a list
        print("neighbours of current starting line",neighbours)
        num_neighbours = {} #empty dictionary
        to_remove = []
        line_left = []
        line_end = False

        while len(neighbours) > 1:
            for i in neighbours:    #for each neighbour that the start line had
                a = gdf[gdf["Numer"] == int(i)] #get the feature
                try:
                    number = a["Sasiedzi"].str.split(",").values[0] #get the number of neighbours
                    num_neighbours[int(i)] = len(number)    #add the number to the dictionary
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
                if num_neighbours.get(min_neighbours[0]) == 2 or num_neighbours.get(min_neighbours[0]) == 3: 
                    print("using",min_neighbours[0])
                    hanging_neighbour = gdf[gdf["Numer"] == min_neighbours[0]] #get the feature
                    current_length = current_length + 2*(length(hanging_neighbour)) #add its length to the count, its 2* cause its hanging
                    gdf = gdf[gdf["Numer"] != min_neighbours[0]] #remove it from the dataframe
                    neighbours.remove(str(numbers(hanging_neighbour)))    #remove it from the neighbours list
                    num_neighbours.pop(numbers(hanging_neighbour))    #remove it from available neighbours
                    pathway.append(int(numbers(hanging_neighbour)))   #add it to the pathway list
                else:
                    line = gdf[gdf["Numer"] == min_neighbours[0]]   #get the feature
                    line_left.append(str(numbers(line)))  #add it to a temporary list
                    intersection = [x for x in neighbours if x not in line_left]
                    placeholder = list(intersections)
                    intersections.extend(x for x in intersection if x not in placeholder)
                    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", intersections)
                    neighbours = line_left  #after the line was chosen, make it the only one available
                    print("Intersection detected, using ", numbers(line))
                    

            if len(min_neighbours) >= 2: #if there are two smallest neighbours
                if num_neighbours.get(min_neighbours[0]) == 2 or num_neighbours.get(min_neighbours[0]) == 3:
                    for i in min_neighbours: #for each of the hanging neighbour we do the same
                        hanging_neighbour = gdf[gdf["Numer"] == i] #get the feature
                        current_length = current_length + 2*(length(hanging_neighbour)) #add its length to the count, its 2* cause its hanging
                        gdf = gdf[gdf["Numer"] != i] #remove it from the dataframe
                        neighbours.remove(str(numbers(hanging_neighbour)))    #remove it from the neighbours list
                        num_neighbours.pop(numbers(hanging_neighbour))    #remove it from available neighbours
                        pathway.append(int(numbers(hanging_neighbour)))   #add it to the pathway list
                        if len(neighbours) == 0:    #in the case when there were only hanging neighbours, break, because its the end of the line
                            print("END OF LINE")
                            line_end = True

                else:
                    line = gdf[gdf["Numer"] == min_neighbours[0]]
                    line_left.append(str(numbers(line)))
                    intersection = [x for x in neighbours if x not in line_left]
                    placeholder = list(intersections)
                    intersections.extend(x for x in intersection if x not in placeholder)
                    print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", intersections)
                    neighbours = line_left
                    print("Intersection detected, using ", numbers(line))


        if line_end: #if the line has ended (hanging line w/o neighbours) pick a line from the last intersection
            if len(intersections) != 0:
                print("Found the end of the line, going back to the first intersection")
                print("Current length: ", current_length)
                print("Current path: ", pathway)
                start_line = gdf[gdf["Numer"] == int(intersections[0])] #change the start line from the last line into the one from the crossing
                pathway.append(int(numbers(start_line)))  #add the new start line to the pathway
                gdf = gdf[gdf["Numer"] != int(intersections[0])] #remove the start line from the dataset
                print("New start line: ", int(numbers(start_line)))
                intersections.remove(str(numbers(start_line)))
            else:
                print("Every single path in the line utilized")
                break


        else:
            print("Whats left: ", int(neighbours[0]))
            print("Current length: ", current_length)
            print("Current path: ", pathway)
            start_line = gdf[gdf["Numer"] == int(neighbours[0])] #set the new starting line for the next loop
            pathway.append(int(numbers(start_line)))  #add the new start line to the pathway
            current_length = current_length + length(start_line)    #add its length
            gdf = gdf[gdf["Numer"] != int(neighbours[0])] #remove the start line from the dataset
            print("New start line: ", int(numbers(start_line)))
            try:
                intersections.remove(str(numbers(start_line)))
            except:
                pass


    last_line = pathway[-1]     
    return current_length, pathway, last_line


def main():
    cur, path, last = line_maker(start_line, max_length, current_length, gdf)

    print("\n \n \n \n PROGRAM FINISHED, LINE ENDED")
    print("Current length : ", cur)
    print("Current path : ", path)
    print("Last line : ", last)

    

    selected_line = gdf_copy[gdf_copy["Numer"].isin(path)]
    output = r"D:\Wycena_Naloty\ENEA\Kolejnosc\line.gpkg"
    selected_line.to_file(output, driver = "GPKG")

main()

