import subprocess
import os
import re

def tex_to_image(tex_file, output_image, density=300, quality=90):
    """
    Convert a .tex file into an image by first compiling it into a PDF using pdflatex 
    and then converting the PDF into an image using ImageMagick's magick command.
    
    Parameters:
    - tex_file: Path to the .tex file (e.g., "model_summary.tex")
    - output_image: Desired output image file name with extension (e.g., "output.png")
    - density: Density for the magick command (default 300 for high resolution)
    - quality: Quality for the magick command (default 90)
    
    Returns:
    - output_image: The path to the generated image file.
    """
    # Remove captions from the .tex file
    remove_captions_from_tex(tex_file)
    
    # Step 1: Modify the .tex file to include necessary LaTeX packages and ensure valid document structure
    ensure_latex_document_structure(tex_file)
    
    # Step 2: Compile the LaTeX file to a PDF using pdflatex
    try:
        # Get the directory of the tex_file
        tex_dir = os.path.dirname(tex_file)
        
        # Run pdflatex with the output directory set to the tex_file's directory
        result = subprocess.run(
            ['pdflatex', '-output-directory', tex_dir, tex_file], 
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(result.stdout.decode())  # Output from pdflatex
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode())  # Print pdflatex error
        raise RuntimeError(f"Error compiling LaTeX file: {e}")
    
    # Extract the name of the PDF (same as .tex but with .pdf extension)
    pdf_file = os.path.join(tex_dir, os.path.basename(tex_file).replace('.tex', '.pdf'))
    
    # Check if the PDF was created
    if not os.path.exists(pdf_file):
        raise FileNotFoundError(f"PDF file {pdf_file} was not created.")
    
    # Step 3: Convert the PDF into an image using ImageMagick's magick command
    try:
        result = subprocess.run([
            'magick', '-density', str(density), pdf_file, 
            '-background', 'white', '-alpha', 'remove', '-alpha', 'off',
            '-trim',  # Trim the image to remove any border areas
            '-quality', str(quality), output_image
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(result.stdout.decode())  # Output from magick
    except subprocess.CalledProcessError as e:
        print(e.stderr.decode())  # Print magick error
        raise RuntimeError(f"Error converting PDF to image: {e}")
    
    # Step 4: Check if the image was created
    if not os.path.exists(output_image):
        raise FileNotFoundError(f"Image file {output_image} was not created.")
    
    # Clean up the PDF and auxiliary files after the image is created
    base_name = os.path.splitext(os.path.basename(tex_file))[0]
    aux_files = [f"{base_name}.pdf", f"{base_name}.log", f"{base_name}.aux"]
    
    for aux_file in aux_files:
        aux_file_path = os.path.join(tex_dir, aux_file)
        if os.path.exists(aux_file_path):
            os.remove(aux_file_path)
    
    return output_image

def ensure_latex_document_structure(tex_file):
    """
    Ensure that the LaTeX file has a valid document structure by checking if it includes
    a preamble and the \begin{document} and \end{document} tags.
    
    Parameters:
    - tex_file: Path to the .tex file (e.g., "model_summary.tex")
    """
    with open(tex_file, 'r') as file:
        content = file.read()

    # Check if the LaTeX document contains \begin{document}
    if "\\begin{document}" not in content:
        print(f"Adding document structure to {tex_file}")

        # Add preamble and necessary packages
        preamble = (
            "\\documentclass{article}\n"
            "\\usepackage{dcolumn}\n"
            "\\usepackage{float}\n"
            "\\usepackage{booktabs}\n"
            "\\usepackage{graphicx}\n"
            "\\pagestyle{empty}\n"  # Suppress page numbers
            "\\begin{document}\n"
        )

        # Append the document ending
        end_document = "\n\\end{document}\n"

        # Add the preamble at the beginning and \end{document} at the end
        content = preamble + content + end_document

        # Write the updated content back to the file
        with open(tex_file, 'w') as file:
            file.write(content)
    else:
        print(f"Document structure already exists in {tex_file}")

def convert_all_tex_to_images(input_folder, output_folder, density=300, quality=90):
    """
    Convert all .tex files in the input_folder to images and save them to output_folder.
    
    Parameters:
    - input_folder: Path to the folder containing .tex files.
    - output_folder: Path to the folder where the output images will be saved.
    - density: Density for the convert command (default 300 for high resolution)
    - quality: Quality for the convert command (default 90)
    """
    # Ensure the output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Iterate over all files in the input_folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.tex'):
            input_file = os.path.join(input_folder, file_name)
            
            # Set the output image name (same name as .tex but with .png extension)
            output_image_name = file_name.replace('.tex', '.png')
            output_image_path = os.path.join(output_folder, output_image_name)
            
            # Convert the .tex file to an image
            try:
                image_path = tex_to_image(input_file, output_image_path, density, quality)
                print(f"Converted: {input_file} to {image_path}")
            except Exception as e:
                print(f"Error processing {file_name}: {e}")

def remove_captions_from_tex(tex_file):
    """
    Remove the caption from tables in a .tex file.
    
    Parameters:
    - tex_file: Path to the .tex file.
    """
    with open(tex_file, 'r') as file:
        content = file.read()

    # Remove lines containing \caption
    content = re.sub(r'^.*\\caption.*$', '', content, flags=re.MULTILINE)

    with open(tex_file, 'w') as file:
        file.write(content)
