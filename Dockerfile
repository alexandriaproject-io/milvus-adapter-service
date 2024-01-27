FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Install system dependencies
RUN apt-get update

# Install PyTorch manually
# RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Create a cache directory
RUN mkdir ./cache

# Copy application files
COPY LICENSE .
COPY com com/
COPY src src/
COPY requirements.txt .
COPY __init__.py .
COPY main.py .

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Command to run your application
CMD ["python3", "main.py"]
