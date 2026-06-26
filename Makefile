.PHONY: all build serve clean install-frontend install-backend

all: build serve

# Install frontend dependencies
install-frontend:
	cd frontend && npm install --silent

# Install backend dependencies
install-backend:
	cd backend && pip install -r requirements.txt -q

# Build frontend static files
build: install-frontend
	cd frontend && npx vite build

# Start backend server (serves built frontend on port 5000)
serve:
	cd backend && python app.py

# Clean build artifacts
clean:
	rm -rf frontend/dist

# Full setup: install everything, build, then serve
setup: install-backend install-frontend build
	@echo "============================================"
	@echo "  Setup complete. Run 'make serve' to start."
	@echo "============================================"
