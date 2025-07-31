import pandas as pd
import re
import subprocess
import os
import logging
from datetime import datetime, timedelta
from skimage.io import imread, imsave
import glob
import ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_file_paths(participant_id, root_dir=r'D:/Data/sleep_video_data/DRI-006/'):

    var_root=f"root_folder"
    variable_folder = f"participant_PSG_variables"
    
    HEART_PATH = os.path.join(root_dir, var_root,variable_folder, "Heart Rate.txt")
    print('HEART_PATH  ',HEART_PATH)
    POSITIONS_PATH = os.path.join(root_dir, var_root,variable_folder, "Position.txt")
    SPO2_FILE = os.path.join(root_dir,var_root, variable_folder, "SpO2.txt")
    Stage_file = os.path.join(root_dir, var_root, variable_folder, f"PSG_Sleep profile.txt")
    
    # Video folder is named as "{participant_id}_video"
    VIDEO_DIRECTORY = os.path.join(root_dir, participant_id, f"{participant_id}_video")
    print('VIDEO_DIRECTORY   ',VIDEO_DIRECTORY)
    
 
    video_meta_files = glob.glob(os.path.join(VIDEO_DIRECTORY, "*.txt"))
    print('video_meta_files  ',video_meta_files)
    if video_meta_files:
        VID_METADATA_FILE = video_meta_files[0]
    else:
        VID_METADATA_FILE = None
        logger.error(f"No video metadata .txt file found in {VIDEO_DIRECTORY}")
    
    # Output directory for video frames
    OUTPUT_DIRECTORY = os.path.join(root_dir, participant_id, "video_frames")
    
    return {
        "HEART_PATH": HEART_PATH,
        "POSITIONS_PATH": POSITIONS_PATH,
        "SPO2_FILE": SPO2_FILE,
        "Stage_file": Stage_file,
        "VID_METADATA_FILE": VID_METADATA_FILE,
        "VIDEO_DIRECTORY": VIDEO_DIRECTORY,
        "OUTPUT_DIRECTORY": OUTPUT_DIRECTORY }


def find_data_start(lines):
    pattern = re.compile(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2},\d{3};')
    for idx, line in enumerate(lines):
        if pattern.match(line.strip()):
            return idx
    raise ValueError("Data start not found in the file.")

def heart_file(heart_path):
    try:
        with open(heart_path, 'r') as file:
            lines = file.readlines()
        start_idx = find_data_start(lines)
        heart_data = pd.read_csv(
            heart_path,
            sep=';',
            header=None,
            names=['Timestamp', 'Heart_rate', 'Sleep_State_from_heart_psg'],
            parse_dates=['Timestamp'],
            date_parser=lambda x: pd.to_datetime(x, format='%d.%m.%Y %H:%M:%S,%f'),
            skiprows=start_idx    )
        heart_data['Heart_rate'] = pd.to_numeric(heart_data['Heart_rate'], errors='coerce')
        heart_data = heart_data.dropna(subset=['Heart_rate']).reset_index(drop=True)
        return heart_data
    except Exception as e:
        logger.error(f"Error reading heart rate file: {e}")
        return pd.DataFrame()

def positions_file(path):
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
        start_idx = find_data_start(lines)
        positions_data = pd.read_csv(
            path,
            sep=';',
            header=None,
            names=['Timestamp', 'PSG_Body_Position', 'PSG_Sleep_State'],
            parse_dates=['Timestamp'],
            date_parser=lambda x: pd.to_datetime(x, format='%d.%m.%Y %H:%M:%S,%f'),
            skiprows=start_idx   )
        positions_data['PSG_Body_Position'] = positions_data['PSG_Body_Position'].str.strip()
        positions_data = positions_data[positions_data['PSG_Body_Position'] != 'A'].reset_index(drop=True)
        return positions_data
    except Exception as e:
        logger.error(f"Error reading positions file: {e}")
        return pd.DataFrame()

def spo_data(spo2_file):
    try:
        with open(spo2_file, 'r') as file:
            lines = file.readlines()
        start_idx = find_data_start(lines)
        spo2_data = pd.read_csv(
            spo2_file,
            sep=';',
            header=None,
            names=['Timestamp', 'SpO2', 'Spo_sleep_state'],
            parse_dates=['Timestamp'],
            date_parser=lambda x: pd.to_datetime(x, format='%d.%m.%Y %H:%M:%S,%f'),
            skiprows=start_idx )
        spo2_data['SpO2'] = pd.to_numeric(spo2_data['SpO2'], errors='coerce')
        spo2_data = spo2_data.dropna(subset=['SpO2']).reset_index(drop=True)
        return spo2_data
    except Exception as e:
        logger.error(f"Error reading SpO₂ file: {e}")
        return pd.DataFrame()





def sleep_stage_file(path):
    try:
        with open(path, 'r') as file:
            lines = file.readlines()
        start_idx = find_data_start(lines)
        positions_data = pd.read_csv(
            path,
            sep=';',
            header=None,
            names=['Timestamp', 'Sleep_stage' ],
            parse_dates=['Timestamp'],
            date_parser=lambda x: pd.to_datetime(x, format='%d.%m.%Y %H:%M:%S,%f'),
            skiprows=start_idx)
        positions_data['Sleep_stage'] = positions_data['Sleep_stage'].str.strip()
        positions_data = positions_data[positions_data['Sleep_stage'] != 'A'].reset_index(drop=True)
        return positions_data
    except Exception as e:
        logger.error(f"Error reading positions file: {e}")
        return pd.DataFrame()





def find_valid_start_epoch(psg_data, video_start_time):
    # Remove microseconds (ignore milliseconds)
    video_start_clean = video_start_time.replace(microsecond=0)

    
    
    # Floor the seconds to the nearest 30-second boundary.
    # For example, if seconds == 18, then 18 - (18 % 30) == 18 - 18 == 0.
    boundary_sec = video_start_clean.second - (video_start_clean.second % 30)
    floor_time = video_start_clean.replace(second=boundary_sec)

    
    
    if video_start_clean > floor_time:
        valid_start_epoch = floor_time + timedelta(seconds=30)
    else:
        valid_start_epoch = floor_time

    # print('video_start_clean   ',video_start_clean,'boundary_sec    ',boundary_sec,'floor_time   ',floor_time,   'valid_start_epoch     ',valid_start_epoch)
    
    return valid_start_epoch


def parse_video_metadata(vid_metadata_file):
    video_data = []
    file_name = None

    with open(vid_metadata_file, 'r') as file:
        content = file.readlines()
        for line in content:
            line = line.strip()
            if line.startswith('FileName='):
                file_name = line.split('=')[1].strip().lower()  # Convert to lowercase
            elif line.startswith('Start='):
                if file_name is None:
                    logger.warning("Start line encountered without a FileName. Skipping.")
                    continue
                try:
                    start_time = pd.to_datetime(line.split('=')[1].strip(), format='%d.%m.%Y %H:%M:%S,%f')
                except ValueError as e:
                    logger.error(f"Error parsing datetime: {e}. Skipping entry.")
                    file_name = None
                    continue
                video_data.append({'FileName': file_name, 'Start': start_time})
                file_name = None

    video_metadata_df = pd.DataFrame(video_data)
    return video_metadata_df.sort_values('Start').reset_index(drop=True)

def get_video_properties_ffmpeg(video_file):
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=avg_frame_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_file
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        r_frame_rate = result.stdout.strip()
        
        if '/' in r_frame_rate:
            num, denom = map(int, r_frame_rate.split('/'))
            fps = num / denom
        else:
            fps = float(r_frame_rate)
        return fps
    except Exception as e:
        return 25.0

def sync_psg_with_video(combined_data, video_metadata):
    combined_data = combined_data.copy()
    combined_data['Video_File'] = None

    for idx, row in video_metadata.iterrows():
        video_file = row['FileName'].lower() 
        video_start = row['Start']
        valid_start = row['Valid_Start_Epoch']
        video_end = video_metadata.iloc[idx + 1]['Start'] if idx + 1 < len(video_metadata) else combined_data['Timestamp'].max()

        # Assign video file to combined data rows whose timestamps fall between valid_start and video_end
        mask = (combined_data['Timestamp'] >= valid_start) & (combined_data['Timestamp'] < video_end)
        combined_data.loc[mask, 'Video_File'] = video_file

    combined_data = combined_data.dropna(subset=['Video_File']).reset_index(drop=True)
    return combined_data

def extract_frames_from_videos(combined_data_synced, video_metadata, video_directory, output_directory):
    from datetime import timedelta
    processed_df = combined_data_synced.copy()
    frame_paths = []
    os.makedirs(output_directory, exist_ok=True)
    rows_to_drop = []
    variable_log = []

    for idx, row in processed_df.iterrows():
        video_file_name = row['Video_File']
        timestamp = row['Timestamp']

        if pd.isna(video_file_name):
            rows_to_drop.append(idx)
            continue

        # Get video metadata for the file
        video_meta = video_metadata[video_metadata['FileName'] == video_file_name].iloc[0]
        # use the valid start epoch computed earlier
        valid_start_epoch = video_meta['Valid_Start_Epoch']
        # Get the original video start time from metadata
        video_start = video_meta['Start'].replace(microsecond=0)
        fps = get_video_properties_ffmpeg(os.path.join(video_directory, video_file_name))

        # Now, compute the epoch start relative to valid_start_epoch
        epoch_start = valid_start_epoch + timedelta(seconds=((timestamp - valid_start_epoch).total_seconds() // 30) * 30)
        middle_epoch_time = epoch_start + timedelta(seconds=15)

        # Compute the time offset in seconds from video_start
        time_offset = (middle_epoch_time - video_start).total_seconds()


        if time_offset < 0:
            logger.warning(f"Skipping frame extraction for {video_file_name} at {timestamp}: Time offset is negative.")
            rows_to_drop.append(idx)
            continue

        frame_number = int(time_offset * fps)
        timestamp_str = middle_epoch_time.strftime("%Y%m%d_%H%M%S")
        final_output_path = os.path.join(output_directory, f"{video_file_name}_{frame_number}.jpg")
        temp_frame_path = os.path.join(output_directory, f"temp_{video_file_name}_{timestamp_str}.jpg")


        ffmpeg_cmd = [
            'ffmpeg',
            '-ss', str(max(0, time_offset)),
            '-i', os.path.join(video_directory, video_file_name),
            '-frames:v', '1',
            '-q:v', '2',
            temp_frame_path,
            '-y'
        ]

        try:
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            # logger.error(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            # logger.error(f"FFmpeg error: {result.stderr}")
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error for {video_file_name} at {timestamp}: {result.stderr}")
                rows_to_drop.append(idx)
                continue

            if not os.path.exists(temp_frame_path):
                logger.error(f"Temporary frame image not found: {temp_frame_path}")
                rows_to_drop.append(idx)
                continue

            frame = imread(temp_frame_path)
            transformed_frame = project_transform(frame, area_of_interest, area_of_projection)
            imsave(final_output_path, transformed_frame)

            if os.path.exists(final_output_path):
                frame_paths.append(final_output_path)
                processed_df.at[idx, 'frame_path'] = final_output_path
            else:
                logger.error(f"Final output path not found: {final_output_path}")
                rows_to_drop.append(idx)

            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
        except Exception as e:
            logger.error(f"Error processing frame {idx}: {str(e)}")
            rows_to_drop.append(idx)
            if os.path.exists(temp_frame_path):
                os.remove(temp_frame_path)
            continue

    processed_df.drop(rows_to_drop, inplace=True)
    return processed_df.reset_index(drop=True)


participant_id = "DRI006_D024"
paths = build_file_paths(participant_id)

# assign file paths from the dictionary:
HEART_PATH = paths["HEART_PATH"]
POSITIONS_PATH = paths["POSITIONS_PATH"]
SPO2_FILE = paths["SPO2_FILE"]
Stage_file = paths["Stage_file"]
VID_METADATA_FILE = paths["VID_METADATA_FILE"]
VIDEO_DIRECTORY = paths["VIDEO_DIRECTORY"]
OUTPUT_DIRECTORY = paths["OUTPUT_DIRECTORY"]

logger.info(f"HEART_PATH: {HEART_PATH}")
logger.info(f"POSITIONS_PATH: {POSITIONS_PATH}")
logger.info(f"SPO2_FILE: {SPO2_FILE}")
logger.info(f"Stage_file: {Stage_file}")
logger.info(f"VID_METADATA_FILE: {VID_METADATA_FILE}")
logger.info(f"VIDEO_DIRECTORY: {VIDEO_DIRECTORY}")
logger.info(f"OUTPUT_DIRECTORY: {OUTPUT_DIRECTORY}")



heart_data = heart_file(HEART_PATH)
positions_data = positions_file(POSITIONS_PATH)
spo2_data = spo_data(SPO2_FILE)
sleep_stage= sleep_stage_file(Stage_file)


heart_data = heart_file(HEART_PATH)
# Drop the unwanted sleep state column from heart_data
if 'Sleep_State_from_heart_psg' in heart_data.columns:
    heart_data = heart_data.drop(columns=['Sleep_State_from_heart_psg'])

positions_data = positions_file(POSITIONS_PATH)
# Drop the unwanted PSG sleep state column from positions_data
if 'PSG_Sleep_State' in positions_data.columns:
    positions_data = positions_data.drop(columns=['PSG_Sleep_State'])

spo2_data = spo_data(SPO2_FILE)
# Drop the unwanted SpO₂ sleep state column from spo2_data
if 'Spo_sleep_state' in spo2_data.columns:
    spo2_data = spo2_data.drop(columns=['Spo_sleep_state'])


    
# Combine DataFrames
combined_data = pd.merge(heart_data, positions_data, on='Timestamp', how='outer')
combined_data = pd.merge(combined_data, spo2_data, on='Timestamp', how='outer')
combined_data = pd.merge(combined_data, sleep_stage, on='Timestamp', how='outer')

combined_data = combined_data.sort_values('Timestamp').reset_index(drop=True)

    # Process video metadata
video_metadata = parse_video_metadata(VID_METADATA_FILE)

for idx, row in video_metadata.iterrows():
    valid_start_epoch = find_valid_start_epoch(positions_data, row['Start'])
    if valid_start_epoch is not None:
        video_metadata.at[idx, 'Valid_Start_Epoch'] = valid_start_epoch
        logger.info(f"Valid start epoch for video {row['FileName']}: {valid_start_epoch}")
    else:
        logger.error(f"No valid start epoch found for video {row['FileName']}")


    # Sync and extract frames
combined_data_synced = sync_psg_with_video(combined_data, video_metadata)
combined_data_synced = extract_frames_from_videos(combined_data_synced, video_metadata, VIDEO_DIRECTORY, OUTPUT_DIRECTORY)
logger.info("Processing completed successfully")
