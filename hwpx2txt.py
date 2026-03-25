import os
import zipfile
import xml.etree.ElementTree as ET
import sys

def hwpx_to_text(hwpx_path):
    """
    Extracts text from a .hwpx file and returns it as a string.
    .hwpx files are ZIP archives containing XML files.
    Main text content is usually in Contents/section0.xml, section1.xml, etc.
    """
    if not os.path.exists(hwpx_path):
        print(f"Error: File not found: {hwpx_path}")
        return None

    extracted_text = []
    
    try:
        with zipfile.ZipFile(hwpx_path, 'r') as z:
            # List all files in the zip to find section XMLs
            file_list = z.namelist()
            
            # Filter and sort section files (Contents/section0.xml, Contents/section1.xml, ...)
            section_files = sorted([f for f in file_list if f.startswith('Contents/section') and f.endswith('.xml')])
            
            if not section_files:
                print(f"Warning: No section files found in {hwpx_path}")
                return None

            for section_file in section_files:
                with z.open(section_file) as f:
                    xml_content = f.read()
                    root = ET.fromstring(xml_content)
                    
                    # HWML namespaces
                    # The text is usually inside <hp:t> tags
                    # We use a wildcard for the namespace to make it more robust
                    for t_tag in root.iter():
                        if t_tag.tag.endswith('}t') or t_tag.tag == 't':
                            if t_tag.text:
                                extracted_text.append(t_tag.text)
                            # Handle cases where there might be a line break after a paragraph
                            # In HWPX, paragraphs are usually <hp:p> tags
                        elif t_tag.tag.endswith('}p') or t_tag.tag == 'p':
                             extracted_text.append('\n')

        return "".join(extracted_text).strip()

    except Exception as e:
        print(f"Error processing {hwpx_path}: {e}")
        return None

def main():
    # If a path is provided as an argument, use it. 
    # Otherwise, look for .hwpx files in the 'input' directory.
    target_files = []
    
    if len(sys.argv) > 1:
        target_files.append(sys.argv[1])
    else:
        input_dir = 'input'
        if os.path.exists(input_dir):
            for f in os.listdir(input_dir):
                if f.lower().endswith('.hwpx'):
                    target_files.append(os.path.join(input_dir, f))
    
    if not target_files:
        print("No .hwpx files found. Please provide a path or place files in the 'input' folder.")
        return

    for hwpx_path in target_files:
        print(f"Processing: {hwpx_path}...")
        text = hwpx_to_text(hwpx_path)
        
        if text:
            # Save as .txt in the same directory as the source
            output_path = os.path.splitext(hwpx_path)[0] + '.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Successfully saved to: {output_path}")
        else:
            print(f"Failed to extract text from {hwpx_path}")

if __name__ == "__main__":
    main()
