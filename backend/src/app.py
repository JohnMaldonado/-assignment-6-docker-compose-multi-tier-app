import os
import redis
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'jhon-postgres'),
    'database': os.getenv('DB_NAME', 'jhon_db'),
    'user': os.getenv('DB_USER', 'jhon_user'),
    'password': os.getenv('DB_PASSWORD', 'jhon_password')
}

# Redis configuration with password
REDIS_HOST = os.getenv('REDIS_HOST', 'jhon-redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'jhon_redis_pass')

# Initialize Redis client WITH PASSWORD
cache = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    password=REDIS_PASSWORD,
    decode_responses=True
)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        conn.close()
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    try:
        cache.ping()
        redis_status = 'healthy'
    except Exception as e:
        redis_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': db_status,
        'redis': redis_status
    }), 200

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    cached_tasks = cache.get('tasks')
    if cached_tasks:
        return jsonify({
            'source': 'cache',
            'tasks': eval(cached_tasks)
        }), 200
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, completed FROM tasks ORDER BY id')
        tasks = [{'id': row[0], 'title': row[1], 'completed': row[2]} 
                 for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        cache.setex('tasks', 60, str(tasks))
        
        return jsonify({
            'source': 'database',
            'tasks': tasks
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    title = data.get('title')
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (title, completed) VALUES (%s, %s) RETURNING id',
            (title, False)
        )
        task_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        cache.delete('tasks')
        
        return jsonify({
            'id': task_id,
            'title': title,
            'completed': False
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/init-db', methods=['POST'])
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO tasks (title, completed) VALUES
            ('Learn Docker', true),
            ('Master Docker Compose', false),
            ('Deploy to AWS Lightsail', false)
            ON CONFLICT DO NOTHING
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Database initialized successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development')
