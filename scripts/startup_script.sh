#!/bin/bash
# Automated A100 VM Setup Script
# Run this script on the video-gen-vm instance after first SSH connection

set -e  # Exit on error

echo "========================================="
echo "A100 VM Setup for Wan 2.2 Video Generation"
echo "========================================="

# Update system
echo "[1/10] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install NVIDIA Driver
echo "[2/10] Installing NVIDIA Driver 535..."
sudo apt-get install -y nvidia-driver-535

echo "⚠️  REBOOT REQUIRED after driver installation"
echo "After reboot, run this script again with --skip-driver flag"
echo ""
read -p "Reboot now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi

# Check if driver is loaded
if ! nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA driver not detected. Please reboot and run again."
    exit 1
fi

echo "✅ NVIDIA Driver detected"
nvidia-smi

# Install CUDA 12.1
echo "[3/10] Installing CUDA Toolkit 12.1..."
if [ ! -d "/usr/local/cuda-12.1" ]; then
    wget -q https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
    sudo sh cuda_12.1.0_530.30.02_linux.run --silent --toolkit --no-opengl-libs
    rm cuda_12.1.0_530.30.02_linux.run
fi

# Add CUDA to PATH
if ! grep -q "cuda-12.1" ~/.bashrc; then
    echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
fi
export PATH=/usr/local/cuda-12.1/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH

echo "✅ CUDA installed"
nvcc --version

# Install Python 3.10
echo "[4/10] Installing Python 3.10..."
sudo apt-get install -y python3.10 python3.10-venv python3-pip git

# Create project directory
echo "[5/10] Creating project directory..."
sudo mkdir -p /wan-project/outputs
sudo chown -R $USER:$USER /wan-project
cd /wan-project

# Create virtual environment
echo "[6/10] Setting up Python virtual environment..."
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install PyTorch with CUDA 12.1
echo "[7/10] Installing PyTorch with CUDA 12.1..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify PyTorch GPU
echo "✅ Verifying PyTorch GPU support..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}'); print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB' if torch.cuda.is_available() else 'N/A')"

# Clone Wan repository
echo "[8/10] Cloning Wan 2.2 repository..."
if [ ! -d "Wan-Video" ]; then
    git clone https://github.com/Wan-Video/Wan-Video.git
fi
cd Wan-Video
pip install -r requirements.txt
pip install diffusers transformers accelerate safetensors

# Install Google Cloud SDK
echo "[9/10] Installing Google Cloud SDK..."
if ! command -v gcloud &> /dev/null; then
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
    sudo apt-get update && sudo apt-get install -y google-cloud-sdk
fi

echo "✅ Google Cloud SDK installed"

# Create generation script
echo "[10/10] Creating generation script..."
cat > /wan-project/generate.py << 'EOF'
#!/usr/bin/env python3
import argparse
import torch
from wan.pipelines import WanPipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', type=str, default='i2v-14B')
    parser.add_argument('--size', type=str, default='1280*720')
    parser.add_argument('--ckpt_dir', type=str, required=True)
    parser.add_argument('--prompt', type=str, required=True)
    parser.add_argument('--save_file', type=str, required=True)
    parser.add_argument('--precision', type=str, default='fp16', choices=['fp16', 'fp32'])
    args = parser.parse_args()
    
    # Parse resolution
    width, height = map(int, args.size.split('*'))
    
    # Load pipeline with FP16
    dtype = torch.float16 if args.precision == 'fp16' else torch.float32
    pipe = WanPipeline.from_pretrained(
        args.ckpt_dir,
        torch_dtype=dtype
    ).to('cuda')
    
    # Generate video
    output = pipe(
        prompt=args.prompt,
        width=width,
        height=height,
        num_inference_steps=50,
        guidance_scale=7.5
    )
    
    # Save
    output.save(args.save_file)
    print(f"Video saved to: {args.save_file}")

if __name__ == '__main__':
    main()
EOF

chmod +x /wan-project/generate.py

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Authenticate gcloud: gcloud auth login"
echo "2. Download FP16 model weights to /wan-project/models/Wan2.2-I2V-14B-720P-FP16"
echo "3. Test generation with:"
echo "   cd /wan-project"
echo "   source venv/bin/activate"
echo "   python3 generate.py --task i2v-14B --size 1280*720 \\"
echo "     --ckpt_dir /wan-project/models/Wan2.2-I2V-14B-720P-FP16 \\"
echo "     --prompt 'A serene ocean sunset' \\"
echo "     --save_file /wan-project/outputs/test.mp4 \\"
echo "     --precision fp16"
echo ""
