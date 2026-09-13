import os
from app import create_app
from app.seed import seed

app = create_app()

with app.app_context():
    seed()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
