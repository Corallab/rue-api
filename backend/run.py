from app import create_app

# Create the application instance
app = create_app()

# Run the Flask development server
if __name__ == "__main__":
    # Enable debugging mode for development
    app.run(host="0.0.0.0", port=5003, debug=True)
