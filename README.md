# Multimodal-Clinical-Sleep-Data-Preprocessing-Pipeline

A robust, automated pipeline for synchronizing and preprocessing complex, multimodal data from clinical sleep studies. This project is designed to handle time-series physiological data from Polysomnography (PSG) and time-stamped infrared video recordings, preparing a clean, synchronized, and labelled dataset ready for downstream machine learning analysis.

This work is part of a larger research effort to apply AI and deep learning to understand sleep behaviour and its clinical implications.

📖 Table of Contents
Key Features

Workflow Overview

Prerequisites

Installation

Usage

Code Description

Author

License

✨ Key Features
Multimodal Data Parsing: Efficiently parses and cleans multiple time-series PSG data streams, including Heart Rate, SpO₂, Body Position, and Sleep Stage data from proprietary text file formats.

Video & PSG Synchronization: Precisely synchronizes the time-series physiological data with multi-file, time-stamped video recordings based on metadata.

Epoch-based Frame Extraction: Extracts specific video frames corresponding to the midpoint of each 30-second physiological epoch using ffmpeg for accurate temporal alignment.

Image Preprocessing & Normalization: Applies a projective transformation (homography) to each extracted frame to isolate a consistent region of interest (e.g., the bed), correcting for camera perspective and ensuring spatial consistency across all images.

Automated File & Directory Management: Intelligently builds file paths and manages output directories for large-scale clinical datasets, ensuring a structured and organized workflow.

Robust Error Handling: Includes logging and error handling to manage common issues in clinical data, such as missing files, corrupted data, or timing discrepancies.

🔄 Workflow Overview
The pipeline follows a systematic process to transform raw, unsynchronized clinical data into a machine-learning-ready dataset.

1. Load & Parse Data
   |
   |--> [PSG .txt Files (HR, SpO2, Position, Stage)] --> Parse & Clean DataFrames
   |
   '--> [Video Metadata .txt File] --> Parse Video Start Times & Filenames

2. Synchronize Modalities
   |
   |--> [Combined PSG DataFrame] + [Video Metadata] --> Align Timestamps & Create Master Synchronized DataFrame

3. Extract & Process Frames
   |
   |--> For each row in Master DataFrame:
   |      |
   |      |--> Calculate midpoint of 30s epoch
   |      |--> Identify corresponding video file
   |      |--> Use FFmpeg to extract the precise frame
   |      |--> Apply Projective Transform to isolate Region of Interest
   |      '--> Save processed frame with a unique, descriptive name

4. Output
   |
   '--> [Clean, Labeled Image Dataset] & [Master CSV with labels and frame paths]

🛠 Prerequisites
Python 3.9+

FFmpeg: This pipeline relies on ffmpeg for video processing. You must have it installed and accessible in your system's PATH. You can download it from ffmpeg.org.

⚙️ Installation
Clone the repository:

git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

Install the required Python libraries:
A requirements.txt file is included for easy installation.

pip install -r requirements.txt

The requirements.txt file should contain:

numpy
matplotlib
scikit-image
pandas
ffmpeg-python

🚀 Usage
Directory Structure:
Ensure your data is organized in the expected directory structure. The script is configured to locate files based on a root directory and a participant ID.

D:/Data/sleep_video_data/DRI-006/
|
|-- DRI006_D012/
|   |-- DRI006_D012_video/
|   |   |-- video1.mp4
|   |   |-- video2.mp4
|   |   '-- video_metadata.txt
|   |
|   '-- video_framesv7/  <-- This will be created by the script
|
'-- DRI006_D012_variables/
    |-- Heart Rate.txt
    |-- Position.txt
    |-- SpO2.txt
    '-- Sleep profile - SDRI006_D012_V3_N1_Consensus.txt

Configure the Script:
Open the main Python script and modify the following variables at the bottom of the file:

participant_id: Set this to the ID of the participant you wish to process (e.g., "DRI006_D012").

root_dir: (Optional) Change the root directory if your data is stored elsewhere.

Run the script:

python your_script_name.py

The script will log its progress to the console and save the processed frames in the specified output directory.

📜 Code Description
project_transform(): Applies a projective transformation to an image to warp a defined source quadrilateral to a destination quadrilateral, effectively normalizing the perspective.

build_file_paths(): Constructs all necessary input and output file paths based on a participant ID and a root directory.

heart_file(), positions_file(), etc.: A series of robust parser functions designed to read proprietary .txt files, handle header irregularities, and load the data into clean Pandas DataFrames.

parse_video_metadata(): Reads the video metadata file to extract the start times and filenames for each video segment.

find_valid_start_epoch(): Aligns video start times to the nearest 30-second epoch boundary to ensure correct synchronization with PSG data.

sync_psg_with_video(): Merges the physiological data with the video metadata to create a master DataFrame where each physiological reading is mapped to a specific video file.

extract_frames_from_videos(): The core function that iterates through the synchronized data, calculates the precise timestamp for frame extraction, uses ffmpeg to extract the frame, applies the projective transform, and saves the final processed image.

👨‍💻 Author
Dr. Sarmad Mueen

GitHub: @your-github-username

LinkedIn: Your LinkedIn Profile URL

📄 License
This project is licensed under the MIT License - see the LICENSE.md file for details.
