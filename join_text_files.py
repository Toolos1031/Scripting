import os

input_directory = r"D:\Katowice\camera_log"
output_file_path = r"D:\Katowice\camera_log.txt"

def join_text_files(input_directory, output_file_path):
    with open(output_file_path, 'w') as output_file:
        for file_name in os.listdir(input_directory):
            if file_name.endswith(".txt"):
                file_path = os.path.join(input_directory, file_name)
                with open(file_path, 'r') as input_file:
                    lines = input_file.readlines()
                    if lines:
                        # Write lines except the first line
                        output_file.writelines(lines[1:])

# Call the function
join_text_files(input_directory, output_file_path)

print(f"Files from {input_directory} have been joined into {output_file_path}")