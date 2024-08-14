import os

input_directory = r"C:\Atlasus\ZDJECIA\zur_jezewo\MAP"
output_file_path = r"C:\Atlasus\ZDJECIA\zur_jezewo\MAP_raw.txt"

def join_text_files(input_directory, output_file_path):
    with open(output_file_path, 'w') as output_file:
        for file_name in os.listdir(input_directory):
            if file_name.endswith(".txt"):
                file_path = os.path.join(input_directory, file_name)
                with open(file_path, 'r') as input_file:
                    lines = input_file.readlines()
                    if lines:
                        # Write lines except the first line
                        #output_file.writelines(lines) #Kopiowanie RGB
                        output_file.writelines(lines[1:]) #Kopiowanie Skaner

# Call the function
join_text_files(input_directory, output_file_path)

print(f"Files from {input_directory} have been joined into {output_file_path}")