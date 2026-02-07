# Quick Reference: A100 Setup Commands

## On Your Local Machine

### 1. Update Configuration
```bash
# Edit settings.yaml with your GCP details
code core/config/settings.yaml

# Update these fields:
# gcp.project_id: "your-project-id"
# gcp.bucket_name: "your-bucket-name"
```

### 2. Test Local Workflow
```bash
python main.py --topic "AI breakthroughs 2026"
```

---

## On the A100 VM (video-gen-vm)

### First-Time Setup

```bash
# 1. SSH into VM
gcloud compute ssh video-gen-vm --zone=us-central1-a

# 2. Run automated setup
bash scripts/startup_script.sh

# 3. Download FP16 weights
mkdir -p /wan-project/models/Wan2.2-I2V-14B-720P-FP16
huggingface-cli download Wan-AI/Wan2.2-I2V-14B-720P-FP16 \
  --local-dir /wan-project/models/Wan2.2-I2V-14B-720P-FP16

# 4. Verify setup
python3 scripts/verify_a100_setup.py
```

### Manual Test Generation

```bash
cd /wan-project
source venv/bin/activate

python3 generate.py \
  --task i2v-14B \
  --size 1280*720 \
  --ckpt_dir /wan-project/models/Wan2.2-I2V-14B-720P-FP16 \
  --prompt "A serene ocean sunset with gentle waves" \
  --save_file /wan-project/outputs/test.mp4 \
  --precision fp16

# Monitor GPU
watch -n 1 nvidia-smi
```

---

## Troubleshooting

### GPU Not Detected
```bash
nvidia-smi
# If fails, reboot: sudo reboot
```

### CUDA Issues
```bash
nvcc --version
# Reinstall if needed: see docs/a100_vm_setup.md
```

### PyTorch Not Using GPU
```bash
python3 -c "import torch; print(torch.cuda.is_available())"
# Should print: True
```

---

## Cost Management

```bash
# Stop VM manually (if auto-stop fails)
gcloud compute instances stop video-gen-vm --zone=us-central1-a

# Check VM status
gcloud compute instances list --filter="name=video-gen-vm"
```

---

## Documentation Links

- **Full Setup Guide:** `docs/a100_vm_setup.md`
- **Performance Comparison:** `docs/a100_performance_comparison.md`
- **Walkthrough:** See artifacts in `.gemini/antigravity/brain/`
