from Backend.app import app

def main():
    print("🚀 Starte Backend-Server...")
    app.run(debug=True, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
