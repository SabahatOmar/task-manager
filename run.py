from app import create_app

#checking github commit
#now tryung branching
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

