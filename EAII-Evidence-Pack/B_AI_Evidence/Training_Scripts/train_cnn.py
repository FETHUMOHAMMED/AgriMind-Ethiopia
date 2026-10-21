import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split, Subset
from torchvision import datasets, transforms, models
import time
import random

# Config
DATA_DIR = "datasets/flat_crops"
MODEL_PATH = "model/agrimind_mobilenetv2.pth"
IMG_SIZE = 128
BATCH_SIZE = 32
EPOCHS = 2
LEARNING_RATE = 0.001
SUBSET_SIZE = 5000  # Use 5000 images for faster training

print("Starting AgriMind CNN training...")
device = torch.device("cpu")
print(f"Device: {device}")

# Data transforms
train_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Load dataset
print("Loading dataset...")
full_dataset = datasets.ImageFolder(DATA_DIR, transform=train_transform)
num_classes = len(full_dataset.classes)
print(f"Classes ({num_classes}): {full_dataset.classes}")
print(f"Total images available: {len(full_dataset)}")

# Use subset for faster training
random.seed(42)
if SUBSET_SIZE < len(full_dataset):
    indices = random.sample(range(len(full_dataset)), SUBSET_SIZE)
    full_dataset = Subset(full_dataset, indices)
    print(f"Using SUBSET of {len(full_dataset)} images for faster training")

# Split 80/20
train_size = int(0.8 * len(full_dataset))
val_size = len(full_dataset) - train_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
print(f"Train: {train_size} | Val: {val_size}")

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# Load pretrained MobileNetV2
print("Loading pretrained MobileNetV2...")
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

# Freeze base layers (transfer learning)
for param in model.features.parameters():
    param.requires_grad = False

# Replace classifier for our classes
model.classifier[1] = nn.Linear(model.last_channel, num_classes)
model = model.to(device)

# Loss and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.classifier.parameters(), lr=LEARNING_RATE)

# Training loop
print("\nTraining started...")
print(f"Batches per epoch: {len(train_loader)}")
for epoch in range(EPOCHS):
    start = time.time()
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for i, (images, labels) in enumerate(train_loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        correct += (predicted == labels).sum().item()
        total += labels.size(0)

        if (i + 1) % 20 == 0:
            elapsed_so_far = time.time() - start
            print(f"  Epoch {epoch+1} | Batch {i+1}/{len(train_loader)} | Loss: {running_loss/(i+1):.3f} | Acc: {100*correct/total:.2f}% | Time: {elapsed_so_far:.0f}s")

    train_acc = 100 * correct / total
    elapsed = time.time() - start
    print(f"\nEpoch {epoch+1} DONE | Train Acc: {train_acc:.2f}% | Time: {elapsed:.0f}s")

    # Validation
    model.eval()
    val_correct = 0
    val_total = 0
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            val_correct += (predicted == labels).sum().item()
            val_total += labels.size(0)

    val_acc = 100 * val_correct / val_total
    print(f"  Validation Acc: {val_acc:.2f}%\n")

# Save model
os.makedirs("model", exist_ok=True)
torch.save({
    "model_state": model.state_dict(),
    "classes": full_dataset.dataset.classes if isinstance(full_dataset, Subset) else full_dataset.classes,
    "img_size": IMG_SIZE
}, MODEL_PATH)

print(f"Model saved to {MODEL_PATH}")
print("Training complete!")