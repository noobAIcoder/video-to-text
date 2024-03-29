# video_processing.py
from scenedetect import detect, ContentDetector
import cv2
import os

def process_video(video_path, output_folder, sensitivity):
    print(f"Starting video processing for: {video_path}")
    print(f"Output folder: {output_folder}")
    print(f"Sensitivity: {sensitivity}")
    
    try:
        # Open the video file
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise Exception("Failed to open video file")
        print("Video file opened successfully")
        
        # Get the total number of frames in the video
        num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Total frames: {num_frames}")
        
        # Detect scenes using ContentDetector with the specified sensitivity
        print("Detecting scenes...")
        scene_manager = detect(video_path, ContentDetector(threshold=sensitivity))
        num_scenes = len(scene_manager)
        print(f"Number of scenes detected: {num_scenes}")
        
        # Process each detected scene
        for i, scene in enumerate(scene_manager):
            start_frame = scene[0].get_frames()
            end_frame = scene[1].get_frames()
            print(f"Processing scene {i+1}: start_frame={start_frame}, end_frame={end_frame}")
            
            # Set the video position to the start frame of the scene
            video.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            success, frame = video.read()
            if not success:
                print(f"Failed to read frame at position: {start_frame}")
                continue
            
            # Save the keyframe for the scene
            print(f"Saving keyframe at frame: {start_frame}")
            keyframe_filename = f"keyframe_{start_frame:06d}.jpg"  # Add leading zeroes
            keyframe_path = os.path.join(output_folder, keyframe_filename)
            cv2.imwrite(keyframe_path, frame)
        
        # Release the video capture
        video.release()
        print("Video processing completed.")
        
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise
    
    return output_folder