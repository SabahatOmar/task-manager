from app import create_frontend


frontend_app = create_frontend()
frontend_app.config['SECRET_KEY'] = 'your_secret_key'

print("run.py is executed")
if __name__ == "__main__":
    frontend_app.run(host='0.0.0.0', port=8080, debug=True)

    #frontend_app.run(debug=True)

