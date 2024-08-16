import paho.mqtt.client as mqtt
import json
import requests

broker = "broker.emqx.io"
port = 1883
topic = "factory/energy"

middleware_url = "http://middleware-server/api/energy"

def on_connect(client, userdata, flags, rc):
    print(f"Conectado com o código {rc}")
    client.subscribe(topic)

def on_message(client, userdata, message):
    data = json.loads(message.payload.decode())
    print(f"Dados recebidos: {data}")
    send_to_middleware(data)

def send_to_middleware(data):
    headers = {"Content-Type": "application/json"}
    response = requests.post(middleware_url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print("Dados enviados com sucesso ao middleware")
    else:
        print(f"Falha ao enviar os dados ao middleware: {response.status_code}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port)
client.loop_forever()
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('energy.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS energy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id INTEGER,
            energy REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/energy', methods=['POST'])
def receive_data():
    data = request.get_json()
    conn = sqlite3.connect('energy.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO energy_data (sensor_id, energy, timestamp)
        VALUES (?, ?, ?)
    ''', (data['sensor_id'], data['energy'], data['timestamp']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

@app.route('/api/energy', methods=['GET'])
def get_data():
    conn = sqlite3.connect('energy.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM energy_data')
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
import pandas as pd
import sqlite3
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

# Conectar ao banco de dados e carregar os dados
conn = sqlite3.connect('energy.db')
data = pd.read_sql_query("SELECT * FROM energy_data", conn)
conn.close()

# Processar os dados
X = data[["sensor_id"]]  # Exemplo: Usando sensor_id como feature
y = data["energy"]

# Dividir os dados em conjunto de treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Criar e treinar o modelo
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Previsões e avaliação
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Erro Quadrático Médio: {mse:.2f}")
import tkinter as tk
from tkinter import ttk
import sqlite3

def fetch_latest_data():
    conn = sqlite3.connect('energy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT energy FROM energy_data ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def update_display():
    energy_value = fetch_latest_data()
    if energy_value:
        label.config(text=f"Consumo de Energia: {energy_value:.2f} kWh")
    root.after(1000, update_display)

root = tk.Tk()
root.title("Monitoramento de Energia")

label = ttk.Label(root, text="Consumo de Energia: -- kWh", font=("Arial", 20))
label.pack(pady=20)

update_display()
root.mainloop()