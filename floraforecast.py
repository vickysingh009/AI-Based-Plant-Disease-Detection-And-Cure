import cv2
from skimage.metrics import structural_similarity as ssim
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import openai
import re
import shutil

# Set up your OpenAI API credentials
openai.api_key = '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'

# Define the folder containing the images for comparison
folder_path = "C:\\New folder (3)"  # Update with your folder path

# Initialize image_files to an empty list
image_files = []

# Function to resize an image
def resize_image(image, width=None, height=None):
    if width and height:
        return cv2.resize(image, (width, height))
    elif width:
        aspect_ratio = width / float(image.shape[1])
        new_height = int(image.shape[0] * aspect_ratio)
        return cv2.resize(image, (width, new_height))
    elif height:
        aspect_ratio = height / float(image.shape[0])
        new_width = int(image.shape[1] * aspect_ratio)
        return cv2.resize(image, (new_width, height))
    else:
        return image

# Function to compare images
def compare_images(image1, image2):
    if image1 is None or image2 is None:
        return False, 0.0

    min_height = min(image1.shape[0], image2.shape[0])
    min_width = min(image1.shape[1], image2.shape[1])
    image1_resized = resize_image(image1, width=min_width, height=min_height)
    image2_resized = resize_image(image2, width=min_width, height=min_height)

    gray_image1 = cv2.cvtColor(image1_resized, cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image2_resized, cv2.COLOR_BGR2GRAY)

    similarity_index, _ = ssim(gray_image1, gray_image2, full=True)
    
    return similarity_index >= 0.9, similarity_index * 100

# Function to compare images when the "Compare" button is clicked
def compare_images_button():
    global image_files, image1, folder_path, target_image_path, matched_image_file

    # Check if image files are available
    if image_files is None:
        messagebox.showerror("Error", "No image files found in the folder.")
        return

    # Clear previous results
    output_text_images.config(state=tk.NORMAL)
    output_text_images.delete('1.0', tk.END)
    output_text_images.config(state=tk.DISABLED)

    # Get the selected target image path
    image1_path = target_image_path.get()

    print("Comparing with target image:", image1_path)  # Debugging line

    # Load the target image
    image1 = cv2.imread(image1_path)

    # Check if the target image is loaded successfully
    if image1 is None:
        messagebox.showerror("Error", "Unable to load the target image.")
        return

    # Flag to indicate if a match was found
    match_found = False

    # Compare the target image with images in the folder
    for image_file in image_files:
        image_path = os.path.join(folder_path, image_file)

        # Load the image from the folder
        image2 = cv2.imread(image_path)

        # Check if the image from the folder is loaded successfully
        if image2 is None:
            print(f"Error: Unable to load the image from {image_path}.")  # Debugging line
            continue

        # Compare the images
        is_same, similarity_percentage = compare_images(image1, image2)

        # Print the result for images with similarity above 90%
        if is_same and similarity_percentage > 50:
            output_text_images.config(state=tk.NORMAL)
            output_text_images.insert(tk.END, f"Similarity Percentage for {image_file}: {similarity_percentage:.2f}%\n")
            output_text_images.config(state=tk.DISABLED)  # Disable editing
            match_found = True
            matched_image_file = image_file  # Store the matched image file

    # Display a message if no match was found
    if not match_found:
        output_text_images.config(state=tk.NORMAL)
        output_text_images.insert(tk.END, "No matching image found.\n")
        output_text_images.config(state=tk.DISABLED)  # Disable editing

    # Display the matched image file name and button to copy it
    if matched_image_file:
        output_text_images.config(state=tk.NORMAL)
        output_text_images.insert(tk.END, f"Matched Image: {matched_image_file}\n")
        output_text_images.config(state=tk.DISABLED)  # Disable editing

        # Button to copy the matched image file name
        copy_image_name_button = tk.Button(left_frame, text="Copy Image Name", command=lambda: copy_image_name(matched_image_file), font=('Arial', 12))
        copy_image_name_button.configure(bg='#4CAF50', fg='white')
        copy_image_name_button.pack(pady=10)

# Function to copy the matched image to a specified directory
def copy_matched_image(image_file):
    # Specify the destination directory where the image will be copied
    destination_directory = "C:\\DestinationFolder"  # Update with your destination folder path

    # Check if the destination directory exists, if not, create it
    if not os.path.exists(destination_directory):
        os.makedirs(destination_directory)

    # Copy the image to the destination directory
    source_image_path = os.path.join(folder_path, image_file)
    destination_image_path = os.path.join(destination_directory, image_file)
    shutil.copyfile(source_image_path, destination_image_path)
    messagebox.showinfo("Image Copied", f"The image '{image_file}' has been copied to the destination folder.")

# Function to select the target image
def select_target_image():
    global target_image_path
    image1_path = filedialog.askopenfilename(title="Select Target Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    target_image_path.set(image1_path)

# Function to generate a crop suggestion based on pH and temperature
def get_crop_suggestion():
    user_input = entry.get()

    # Extract pH and temperature values using regular expressions
    ph_match = re.search(r'([\d.]+)\s*ph', user_input, re.IGNORECASE)
    temperature_match = re.search(r'([\d.]+)\s*temperature', user_input, re.IGNORECASE)

    if ph_match and temperature_match:
        try:
            ph_value = float(ph_match.group(1))
            temperature_value = float(temperature_match.group(1))

            # Generate crop suggestion based on pH and temperature
            crop_suggestion = generate_crop_suggestion(ph_value, temperature_value)
            output_text_crop.config(state=tk.NORMAL)
            output_text_crop.delete("1.0", tk.END)  # Clear previous content
            output_text_crop.insert(tk.END, f"Crop suggestion: {crop_suggestion}")
            output_text_crop.tag_configure("center", justify="center")
            output_text_crop.tag_add("center", "1.0", "end")
            output_text_crop.tag_configure("color", foreground="green")
            output_text_crop.tag_add("color", "1.0", "end")
            output_text_crop.config(state=tk.DISABLED)  # Disable editing
        except ValueError:
            messagebox.showerror("Error", "Please provide valid numerical values for pH and temperature.")
    else:
        messagebox.showerror("Error", "Invalid input format. Please enter in the format 'X ph and Y temperature'.")

# Function to generate a crop suggestion based on pH and temperature
def generate_crop_suggestion(ph, temperature):
    prompt = f"The current pH is {ph} and the temperature is {temperature}. What crops are best suited for this environment?"
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=2000,
        temperature=0.7,
        n=1,
        stop=None,
        timeout=15
    )
    return response.choices[0].text.strip()

# Create the main application window
root = tk.Tk()
root.title("Image and Crop Suggestion App")
root.geometry("800x600")  # Adjust the window size as needed

# Configure a style for ttk widgets
style = ttk.Style()
style.configure('TButton', font=('Arial', 12))

# Create and place UI components

# Frame for the left side (buttons)
left_frame = tk.Frame(root, padx=20, pady=20)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

label_image_comparison = ttk.Label(left_frame, text="Image Comparison:", font=('Arial', 16, 'bold'))
label_image_comparison.pack(pady=10)

# Button to select the target image
select_target_button = tk.Button(left_frame, text="Select Target Image", command=select_target_image, font=('Arial', 12))
select_target_button.configure(bg='#4CAF50', fg='white')
select_target_button.pack(pady=10)

# Button to compare images
compare_button = tk.Button(left_frame, text="Compare Images", command=compare_images_button, font=('Arial', 12))
compare_button.configure(bg='#2196F3', fg='white')
compare_button.pack(pady=10)

# Spacer between functionalities
spacer = ttk.Label(left_frame, text="")
spacer.pack(pady=20)

# UI components for crop suggestion
label_crop_suggestion = ttk.Label(left_frame, text="Crop Suggestion:", font=('Arial', 16, 'bold'))
label_crop_suggestion.pack(pady=10)

label_input = ttk.Label(left_frame, text="Enter pH and temperature:", font=('Arial', 14))
label_input.pack(pady=5)

entry = ttk.Entry(left_frame, width=20, font=('Arial', 14))
entry.pack(pady=5)

button_crop_suggestion = tk.Button(left_frame, text="Get Crop Suggestion", command=get_crop_suggestion, font=('Arial', 12))
button_crop_suggestion.configure(bg='#FFC107', fg='black')
button_crop_suggestion.pack(pady=10)

# Frame for the right side (output)
right_frame = tk.Frame(root, padx=20, pady=20)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Output screen for image comparison
output_text_images = tk.Text(right_frame, width=60, height=10, font=('Arial', 12), wrap=tk.WORD)
output_text_images.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
output_text_images.insert(tk.END, "Image comparison results will be displayed here.")
output_text_images.config(state=tk.DISABLED)  # Disable editing

# Output screen for crop suggestion
output_text_crop = tk.Text(right_frame, width=60, height=10, font=('Arial', 12), wrap=tk.WORD)
output_text_crop.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
output_text_crop.insert(tk.END, "Crop suggestion will be displayed here.")
output_text_crop.config(state=tk.DISABLED)  # Disable editing

# Variable to store the target image path
target_image_path = tk.StringVar()

# Variable to store the matched image file name
matched_image_file = None

# Run the GUI application
root.mainloop()
