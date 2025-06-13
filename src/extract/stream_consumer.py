from confluent_kafka import Consumer, KafkaError
import json
import cv2
import numpy as np
import os
from datetime import datetime

class FrameConsumer:
    def __init__(self):
        self.KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        self.KAFKA_TOPIC = 'camera_frames'
        self.GROUP_ID = 'frame_test_consumer'
        self.OUTPUT_DIR = "received_frames"
        
        # Create output directory if it doesn't exist
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        
        # Consumer configuration
        self.conf = {
            'bootstrap.servers': self.KAFKA_BROKERS,
            'group.id': self.GROUP_ID,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            'max.poll.interval.ms': 86400000  # High value for debugging
        }
        
        self.consumer = Consumer(self.conf)
        self.running = True
    
    def overlay_metadata(self, img, metadata):
        """Overlay metadata on the image"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        color = (0, 255, 0)  # Green
        y_offset = 20
        line_height = 25
        
        # Basic info
        cv2.putText(img, f"Camera: {metadata['camera_id']}", (10, y_offset), 
                   font, font_scale, color, font_thickness)
        y_offset += line_height
        
        # Timestamp
        dt = datetime.fromtimestamp(metadata['timestamp']/1000)
        cv2.putText(img, f"Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}", (10, y_offset), 
                   font, font_scale, color, font_thickness)
        y_offset += line_height
        
        # Resolution
        cv2.putText(img, 
                   f"Res: {metadata['resolution']['width']}x{metadata['resolution']['height']}",
                   (10, y_offset), font, font_scale, color, font_thickness)
        y_offset += line_height
        
        # Metrics if available
        if 'metrics' in metadata:
            cv2.putText(img, 
                       f"Brightness: {metadata['metrics']['brightness']:.1f}", 
                       (10, y_offset), font, font_scale, color, font_thickness)
            y_offset += line_height
            
            cv2.putText(img, 
                       f"Sharpness: {metadata['metrics']['sharpness']:.1f}", 
                       (10, y_offset), font, font_scale, color, font_thickness)
            y_offset += line_height
        
        return img
    
    def save_frame(self, img, metadata, frame_count):
        """Save frame with metadata overlay"""
        # Create camera-specific directory
        camera_dir = os.path.join(self.OUTPUT_DIR, metadata['camera_id'])
        os.makedirs(camera_dir, exist_ok=True)
        
        # Add metadata overlay
        img_with_meta = self.overlay_metadata(img.copy(), metadata)
        
        # Generate filename
        timestamp = datetime.fromtimestamp(metadata['timestamp']/1000).strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(camera_dir, f"frame_{timestamp}_{frame_count}.jpg")
        
        # Save image
        cv2.imwrite(filename, img_with_meta)
        print(f"Saved frame to {filename}")
        
        # Also save original without overlay
        orig_filename = os.path.join(camera_dir, f"original_{timestamp}_{frame_count}.jpg")
        cv2.imwrite(orig_filename, img)
    
    def consume_frames(self):
        self.consumer.subscribe([self.KAFKA_TOPIC])
        frame_count = 0
        
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        continue
                
                try:
                    data = json.loads(msg.value())
                    camera_id = data['camera_id']
                    frame_bytes = bytes.fromhex(data['frame'])
                    
                    # Convert bytes to image
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        frame_count += 1
                        print(f"\nReceived frame {frame_count} from {camera_id}")
                        
                        # Print metadata
                        print(f"Timestamp: {data['timestamp']}")
                        print(f"Resolution: {data['resolution']['width']}x{data['resolution']['height']}")
                        if 'metrics' in data:
                            print(f"Brightness: {data['metrics']['brightness']:.1f}")
                            print(f"Sharpness: {data['metrics']['sharpness']:.1f}")
                        
                        # Save every frame with metadata overlay
                        self.save_frame(img, data, frame_count)
                    
                    self.consumer.commit(asynchronous=False)
                    
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            print("Shutting down consumer...")
            self.running = False
        finally:
            self.consumer.close()

if __name__ == '__main__':
    consumer = FrameConsumer()
    consumer.consume_frames()