// Initialize MongoDB with collections and indexes
db = db.getSiblingDB('retail_realtime');

// Create collections
db.createCollection('raw_detections');
db.createCollection('person_tracking');
db.createCollection('zone_analytics');

// Create indexes for better performance
db.raw_detections.createIndex({ "camera_id": 1, "timestamp": -1 });
db.raw_detections.createIndex({ "timestamp": -1 });
db.raw_detections.createIndex({ "store_id": 1, "timestamp": -1 });

db.person_tracking.createIndex({ "person_track_id": 1 });
db.person_tracking.createIndex({ "camera_id": 1, "timestamp": -1 });
db.person_tracking.createIndex({ "store_id": 1, "last_seen": -1 });

db.zone_analytics.createIndex({ "zone_id": 1, "timestamp": -1 });
db.zone_analytics.createIndex({ "store_id": 1, "timestamp": -1 });
db.zone_analytics.createIndex({ "hour": 1, "date": 1 });

print('MongoDB initialized with retail analytics collections and indexes');