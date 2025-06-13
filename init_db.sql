-- Stores table
CREATE TABLE stores (
    store_id VARCHAR(50) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cameras table
CREATE TABLE cameras (
    camera_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) REFERENCES stores(store_id),
    camera_name VARCHAR(100),
    position_x FLOAT,
    position_y FLOAT,
    position_z FLOAT,
    angle FLOAT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zones table
CREATE TABLE zones (
    zone_id VARCHAR(50) PRIMARY KEY,
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(50),
    mask_coordinates JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO stores (store_id, store_name, location) VALUES 
('store_001', 'Downtown Retail Store', 'Downtown Location'),
('store_002', 'Mall Branch', 'Shopping Mall Location');

INSERT INTO cameras (camera_id, store_id, camera_name, position_x, position_y, position_z, angle) VALUES 
('cam_001', 'store_001', 'Entrance Camera', 0.0, 0.0, 2.5, 0.0),
('cam_002', 'store_001', 'Electronics Section', 10.0, 5.0, 2.5, 45.0),
('cam_003', 'store_001', 'Checkout Area', 15.0, 0.0, 2.5, 90.0);

INSERT INTO zones (zone_id, camera_id, zone_name, zone_type, mask_coordinates) VALUES 
('zone_entrance', 'cam_001', 'entrance', 'transition', '{"coordinates": [[0,0], [100,0], [100,100], [0,100]]}'),
('zone_electronics', 'cam_002', 'electronics', 'product', '{"coordinates": [[0,0], [200,0], [200,150], [0,150]]}'),
('zone_groceries', 'cam_002', 'groceries', 'product', '{"coordinates": [[200,0], [400,0], [400,150], [200,150]]}'),
('zone_clothing', 'cam_003', 'clothing', 'product', '{"coordinates": [[0,0], [300,0], [300,200], [0,200]]}'),
('zone_checkout', 'cam_003', 'checkout', 'transaction', '{"coordinates": [[300,0], [500,0], [500,100], [300,100]]}');