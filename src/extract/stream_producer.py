import cv2
import requests
from confluent_kafka import Producer
import json
import time
import os
import threading
import numpy as np

class CameraStreamProducer:
    def __init__(self):
        self.KAFKA_BROKERS = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        self.CAM_STREAM_URL = os.getenv('CAM_STREAM_URL', 'http://localhost:5000')
        self.KAFKA_TOPIC = 'camera_frames'
        self.FRAME_RATE = 30
        self.MAX_QUEUE_SIZE = 10000  # Maximum frames in queue before slowing down
        
        # Enhanced producer configuration
        self.producer_conf = {
            'bootstrap.servers': self.KAFKA_BROKERS,
            'queue.buffering.max.messages': 1000000,
            'queue.buffering.max.kbytes': 1048576,  # 1GB
            'batch.num.messages': 10000,
            'compression.type': 'lz4',
            'message.send.max.retries': 5,
            'retry.backoff.ms': 500,
            'default.topic.config': {'acks': 'all'},
            'socket.keepalive.enable': True
        }
        
        self.producer = Producer(self.producer_conf)
        self.running = True
        self.frame_queue = []
        self.lock = threading.Lock()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.processing_thread.start()
    
    def delivery_report(self, err, msg):
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}')
    
    def get_camera_tokens(self):
        try:
            response = requests.get(f"{self.CAM_STREAM_URL}/api/cameras", timeout=5)
            if response.status_code == 200:
                cameras = response.json().get('cameras', [])
                return {cam['name']: cam['token'] for cam in cameras}
            return {}
        except Exception as e:
            print(f"Error fetching camera tokens: {e}")
            return {}
    
    def capture_frames(self, camera_name, token):
        """Thread function to capture frames and add to queue"""
        stream_url = f"{self.CAM_STREAM_URL}/stream/{token}"
        print(f"Starting frame capture for {camera_name}")
        
        try:
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                print(f"Failed to open stream for {camera_name}")
                return
                
            frame_interval = 1.0 / self.FRAME_RATE
            
            while self.running:
                start_time = time.time()
                
                ret, frame = cap.read()
                if not ret:
                    print(f"Stream ended for {camera_name}")
                    break
                
                # Calculate frame metrics
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = np.mean(gray)
                sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # Convert frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    
                    # Create enhanced metadata
                    metadata = {
                        'camera_id': camera_name,
                        'timestamp': int(time.time() * 1000),
                        'frame': frame_bytes.hex(),
                        'resolution': {
                            'width': frame.shape[1],
                            'height': frame.shape[0],
                            'channels': frame.shape[2] if len(frame.shape) > 2 else 1
                        },
                        'metrics': {
                            'brightness': float(brightness),
                            'sharpness': float(sharpness),
                            'frame_size': len(frame_bytes)
                        },
                        'processing_info': {
                            'capture_time': time.time(),
                            'token': token
                        }
                    }
                    
                    # Add to queue with thread-safe operation
                    with self.lock:
                        if len(self.frame_queue) < self.MAX_QUEUE_SIZE:
                            self.frame_queue.append(metadata)
                        else:
                            print("Queue full - dropping frame")
                
                # Control frame rate
                elapsed = time.time() - start_time
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                    
        except Exception as e:
            print(f"Error capturing frames for {camera_name}: {e}")
        finally:
            cap.release()
            print(f"Stopped capturing frames for {camera_name}")
    
    def process_queue(self):
        """Thread function to process the frame queue"""
        while self.running:
            try:
                # Get frame from queue (thread-safe)
                with self.lock:
                    if not self.frame_queue:
                        time.sleep(0.01)
                        continue
                    metadata = self.frame_queue.pop(0)
                
                # Publish to Kafka
                self.producer.produce(
                    self.KAFKA_TOPIC,
                    key=metadata['camera_id'].encode('utf-8'),
                    value=json.dumps(metadata),
                    callback=self.delivery_report
                )
                
                # Poll to trigger callbacks
                self.producer.poll(0)
                
                # Print queue status periodically
                if time.time() % 5 < 0.01:  # Every ~5 seconds
                    with self.lock:
                        print(f"Queue status: {len(self.frame_queue)} frames pending")
                
            except BufferError:
                print("Producer queue full - waiting...")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error processing queue: {e}")
                time.sleep(1)
    
    def run(self):
        try:
            while self.running:
                cameras = self.get_camera_tokens()
                if not cameras:
                    print("No cameras found, retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                
                # Start a thread for each camera
                for camera_name, token in cameras.items():
                    threading.Thread(
                        target=self.capture_frames,
                        args=(camera_name, token),
                        daemon=True
                    ).start()
                
                # Keep main thread alive
                while self.running:
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("Shutting down producer...")
            self.running = False
            self.producer.flush()
            print(f"Flushed {self.producer.flush()} remaining messages")

if __name__ == '__main__':
    producer = CameraStreamProducer()
    producer.run()